"""Consultant management and unauthenticated client routes for magic links."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from starlette.datastructures import UploadFile

from app.config import settings
from app.database import get_db
from app.models.assessment import Assessment
from app.routers.web import templates
from app.services import evidence as evidence_service
from app.services import magic_links as magic_service, rfi_requests, report_snapshots
from app.services.conclusion_review import reviewer_actor

router = APIRouter(include_in_schema=False)

_CONSULTANT_HEADERS = {
    "Cache-Control": "no-store",
    "Referrer-Policy": "no-referrer",
}


def _render_invalid(request: Request):
    return templates.TemplateResponse(
        "magic/invalid.html",
        {
            "request": request,
            "firm_name": settings.firm_name,
            "message": magic_service.INVALID_LINK_MESSAGE,
        },
        status_code=404,
        headers=magic_service.SECURITY_HEADERS,
    )


def _upload_context(request: Request, db: Session, link: magic_service.MagicLink) -> dict:
    usage = magic_service.link_usage(db, link)
    uploads = [
        row
        for row in magic_service.client_upload_rows(db, link.engagement_id)
        if row["magic_link_id"] == link.id
    ]
    return {
        "request": request,
        "firm_name": settings.firm_name,
        "items": magic_service.scope_items(link),
        "remaining": max(0, link.max_uploads - usage.uploads_total),
        "max_uploads": link.max_uploads,
        "expires_at": magic_service._as_utc(link.expires_at).strftime("%Y-%m-%d %H:%M"),
        "uploads": uploads,
    }


def _render_upload(
    request: Request,
    db: Session,
    link: magic_service.MagicLink,
    *,
    status_code: int = 200,
    error: str | None = None,
    success_filename: str | None = None,
    headers: dict[str, str] | None = None,
):
    context = _upload_context(request, db, link)
    context.update({"error": error, "success_filename": success_filename})
    return templates.TemplateResponse(
        "magic/upload.html",
        context,
        status_code=status_code,
        headers=headers or magic_service.SECURITY_HEADERS,
    )


def _consultant_context(
    request: Request,
    db: Session,
    engagement_id: str,
    *,
    error: str | None = None,
    new_link_url: str | None = None,
) -> dict:
    return {
        "request": request,
        "engagement_id": engagement_id,
        "magic_links": magic_service.magic_link_rows(db, engagement_id),
        "client_uploads": magic_service.client_upload_rows(db, engagement_id),
        "error": error,
        "new_link_url": new_link_url,
    }


def _render_consultant(
    request: Request,
    db: Session,
    engagement_id: str,
    *,
    status_code: int = 200,
    error: str | None = None,
    new_link_url: str | None = None,
):
    return templates.TemplateResponse(
        "partials/magic_links.html",
        _consultant_context(
            request,
            db,
            engagement_id,
            error=error,
            new_link_url=new_link_url,
        ),
        status_code=status_code,
        headers=_CONSULTANT_HEADERS,
    )


def _form_int(form, name: str, default: int, message: str) -> int:
    raw = form.get(name, default)
    try:
        return int(raw)
    except (TypeError, ValueError) as exc:
        raise magic_service.MagicLinkValidationError(message) from exc


def _render_rfi_links(
    request: Request,
    db: Session,
    assessment: Assessment,
    *,
    error: str | None = None,
    new_link_url: str | None = None,
    status_code: int = 200,
):
    try:
        context = rfi_requests.page_context(db, assessment)
    except report_snapshots.SnapshotError as exc:
        context = {
            "assessment": assessment,
            "scope_recorded": assessment.scope_answers is not None,
            "preview": None,
            "mapped_hints": {},
            "versions": [],
            "current_issue": None,
            "current_items": [],
            "links": [],
            "coverage": {},
            "received": {},
            "reviewer_name": "",
        }
        error = exc.message
    context.update(
        {
            "request": request,
            "error": error,
            "new_link_url": new_link_url,
        }
    )
    return templates.TemplateResponse(
        "partials/rfi_links.html",
        context,
        status_code=status_code,
        headers=_CONSULTANT_HEADERS,
    )


@router.get("/magic/{token}")
def get_magic_link(token: str, request: Request, db: Session = Depends(get_db)):
    link = magic_service.resolve_token(db, token)
    if link is None:
        return _render_invalid(request)
    return _render_upload(request, db, link)


@router.post("/magic/{token}")
async def post_magic_link(token: str, request: Request, db: Session = Depends(get_db)):
    link = magic_service.resolve_token(db, token)
    if link is None:
        return _render_invalid(request)

    content_length = request.headers.get("content-length")
    try:
        body_size = int(content_length) if content_length is not None else None
    except ValueError:
        body_size = None
    if body_size is None or body_size < 0:
        return _render_upload(
            request,
            db,
            link,
            status_code=411,
            error="Content-Length required.",
        )
    if body_size > magic_service.MAX_FILE_BYTES + magic_service.MULTIPART_OVERHEAD_BYTES:
        return _render_upload(
            request,
            db,
            link,
            status_code=413,
            error=magic_service.FILE_TOO_LARGE_MESSAGE,
        )

    try:
        usage = magic_service.check_upload_allowed(db, link)
    except magic_service.RateLimited as exc:
        headers = dict(magic_service.SECURITY_HEADERS)
        headers["Retry-After"] = str(exc.retry_after_seconds)
        return _render_upload(
            request,
            db,
            link,
            status_code=exc.status_code,
            error=exc.message,
            headers=headers,
        )
    except magic_service.UploadLimitReached as exc:
        return _render_upload(
            request,
            db,
            link,
            status_code=exc.status_code,
            error=exc.message,
        )

    form = await request.form()
    item_key = form.get("item_key")
    item_keys = {item["key"] for item in magic_service.scope_items(link)}
    if not isinstance(item_key, str) or item_key not in item_keys:
        return _render_upload(
            request,
            db,
            link,
            status_code=422,
            error="Choose one of the requested items.",
        )

    upload = form.get("file")
    if not isinstance(upload, UploadFile) or not upload.filename:
        return _render_upload(
            request,
            db,
            link,
            status_code=422,
            error="Choose a file to upload.",
        )

    content = await upload.read(magic_service.MAX_FILE_BYTES + 1)
    try:
        result = magic_service.receive_client_upload(
            db,
            link=link,
            item_key=item_key,
            filename=upload.filename,
            content=content,
            usage=usage,
        )
    except (magic_service.MagicLinkError, evidence_service.EvidenceError) as exc:
        db.rollback()
        return _render_upload(
            request,
            db,
            link,
            status_code=exc.status_code,
            error=exc.message,
        )

    if not result.released:
        return _render_upload(
            request,
            db,
            link,
            status_code=422,
            error=evidence_service.SCAN_REJECTED_MESSAGE,
        )
    return _render_upload(
        request,
        db,
        link,
        success_filename=result.evidence.original_filename,
    )


@router.post("/engagements/{engagement_id}/magic-links")
async def create_magic_link(
    engagement_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    form = await request.form()
    items = form.get("items", "")
    item_titles = items.splitlines() if isinstance(items, str) else []
    try:
        created = magic_service.create_link(
            db,
            engagement_id=engagement_id,
            item_titles=item_titles,
            expires_in_days=_form_int(
                form,
                "expires_in_days",
                7,
                "Expiry must be between 1 and 30 days.",
            ),
            max_uploads=_form_int(
                form,
                "max_uploads",
                20,
                "Upload limit must be between 1 and 100.",
            ),
            max_total_mb=_form_int(
                form,
                "max_total_mb",
                100,
                "Total size limit must be between 1 and 500 MB.",
            ),
        )
        db.commit()
    except magic_service.MagicLinkNotFound as exc:
        db.rollback()
        return _render_consultant(
            request,
            db,
            engagement_id,
            status_code=404,
            error=exc.message,
        )
    except magic_service.MagicLinkError as exc:
        db.rollback()
        return _render_consultant(request, db, engagement_id, error=exc.message)

    new_link_url = str(request.base_url).rstrip("/") + "/magic/" + created.token
    return _render_consultant(
        request,
        db,
        engagement_id,
        new_link_url=new_link_url,
    )


@router.post("/assessments/{assessment_id}/rfi/versions/{snapshot_id}/magic-links")
async def create_rfi_magic_link(
    assessment_id: str,
    snapshot_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        db.rollback()
        return _render_rfi_links(
            request,
            db,
            Assessment(
                id=assessment_id,
                company_name="",
                industry="",
                company_size="",
            ),
            status_code=404,
            error="Assessment not found",
        )
    form = await request.form()
    item_ids = [value for value in form.getlist("item_ids") if isinstance(value, str)]
    try:
        created = rfi_requests.create_client_link(
            db,
            assessment,
            snapshot_id,
            item_ids=item_ids,
            expires_in_days=_form_int(
                form,
                "expires_in_days",
                7,
                "Expiry must be between 1 and 30 days.",
            ),
            max_uploads=_form_int(
                form,
                "max_uploads",
                20,
                "Upload limit must be between 1 and 100.",
            ),
            max_total_mb=_form_int(
                form,
                "max_total_mb",
                100,
                "Total size limit must be between 1 and 500 MB.",
            ),
            actor=reviewer_actor(form.get("reviewer_name", "")),
        )
        db.commit()
    except rfi_requests.RfiError as exc:
        db.rollback()
        status = 404 if exc.status_code == 404 else 200
        return _render_rfi_links(
            request,
            db,
            assessment,
            status_code=status,
            error=exc.message,
        )
    except magic_service.MagicLinkNotFound as exc:
        db.rollback()
        return _render_rfi_links(
            request,
            db,
            assessment,
            status_code=404,
            error=exc.message,
        )
    except report_snapshots.SnapshotIntegrityError as exc:
        db.rollback()
        return _render_rfi_links(
            request,
            db,
            assessment,
            status_code=500,
            error=exc.message,
        )
    except magic_service.MagicLinkError as exc:
        db.rollback()
        return _render_rfi_links(
            request,
            db,
            assessment,
            error=exc.message,
        )
    except Exception:
        db.rollback()
        return _render_rfi_links(
            request,
            db,
            assessment,
            status_code=500,
            error="The client link could not be created. Try again.",
        )

    new_link_url = str(request.base_url).rstrip("/") + "/magic/" + created.token
    return _render_rfi_links(
        request,
        db,
        assessment,
        new_link_url=new_link_url,
    )


@router.post("/engagements/{engagement_id}/magic-links/{link_id}/revoke")
def revoke_magic_link(
    engagement_id: str,
    link_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    try:
        magic_service.revoke_link(
            db,
            engagement_id=engagement_id,
            link_id=link_id,
        )
        db.commit()
    except magic_service.MagicLinkNotFound as exc:
        db.rollback()
        return _render_consultant(
            request,
            db,
            engagement_id,
            status_code=404,
            error=exc.message,
        )
    except magic_service.MagicLinkConflict as exc:
        db.rollback()
        return _render_consultant(request, db, engagement_id, error=exc.message)
    return _render_consultant(request, db, engagement_id)
