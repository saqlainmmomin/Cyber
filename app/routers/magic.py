"""Consultant management and unauthenticated client routes for magic links."""

from __future__ import annotations

import json
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from starlette.datastructures import UploadFile

from app.database import get_db
from app.models.assessment import Assessment
from app.models.audit_event import AuditEvent
from app.models.client import Client
from app.models.engagement import Engagement
from app.models.evidence import Evidence
from app.models.magic_link import MagicLink
from app.routers.web import templates
from app.services import evidence as evidence_service
from app.services import firm_settings, magic_links as magic_service, request_summary, rfi_requests, report_snapshots
from app.services.conclusion_review import reviewer_actor

router = APIRouter(include_in_schema=False)

_CONSULTANT_HEADERS = {
    "Cache-Control": "no-store",
    "Referrer-Policy": "no-referrer",
}


def _client_headers() -> dict[str, str]:
    """Allow the standalone client page to load the vendored Yozora styles and script."""
    headers = dict(magic_service.SECURITY_HEADERS)
    headers["Content-Security-Policy"] = headers["Content-Security-Policy"].replace(
        "style-src 'unsafe-inline'", "style-src 'self' 'unsafe-inline'; script-src 'unsafe-inline'"
    )
    return headers


def _inactive_link(db: Session, token: str) -> MagicLink | None:
    """Find an issued, inactive link for app-driven invalid-page copy.

    This only hashes a syntactically valid path token and never returns the link's
    engagement or client to the template. Active links and inactive engagements are
    deliberately treated as unknown here.
    """
    if not isinstance(token, str) or magic_service.TOKEN_PATTERN.fullmatch(token) is None:
        return None
    matches = (
        db.query(MagicLink)
        .filter(MagicLink.token_digest == magic_service.token_digest(token))
        .all()
    )
    if len(matches) != 1:
        return None
    link = matches[0]
    engagement = db.get(Engagement, link.engagement_id)
    if engagement is None or engagement.status != "active":
        return None
    return link if magic_service.link_status(link) in {"expired", "revoked"} else None


def _invalid_context(request: Request, db: Session, link: MagicLink | None = None) -> dict:
    firm = firm_settings.get(db)
    state = magic_service.link_status(link) if link is not None else "unknown"
    return {
        "request": request,
        "firm_name": firm.firm_name,
        "firm_contact_email": firm.contact_email,
        "invalid_state": state,
        "expired_on": (
            magic_service._as_utc(link.expires_at).strftime("%-d %b %Y")
            if link is not None and state == "expired"
            else None
        ),
        "message": magic_service.INVALID_LINK_MESSAGE,
    }


def _render_invalid(
    request: Request,
    db: Session,
    *,
    link: MagicLink | None = None,
    status_code: int = 404,
    headers: dict[str, str] | None = None,
):
    # Firm-level only: do not reveal the token, engagement, client or client contact.
    return templates.TemplateResponse(
        "magic/invalid.html",
        _invalid_context(request, db, link),
        status_code=status_code,
        headers=headers or _client_headers(),
    )


def _upload_context(request: Request, db: Session, link: magic_service.MagicLink) -> dict:
    usage = magic_service.link_usage(db, link)
    uploads = [
        row
        for row in magic_service.client_upload_rows(db, link.engagement_id)
        if row["magic_link_id"] == link.id
    ]
    items = []
    for item in magic_service.scope_items(link):
        received = next(
            (
                upload
                for upload in uploads
                if upload["status"] != "rejected"
                and upload["change_reason"].endswith(f": {item['title']}")
            ),
            None,
        )
        items.append({**item, "received": received is not None, "filename": received["filename"] if received else None})
    firm = firm_settings.get(db)
    return {
        "request": request,
        "firm_name": firm.firm_name,
        "items": items,
        "contact_first_name": magic_service.contact_first_name(link),
        "remaining": max(0, link.max_uploads - usage.uploads_total),
        "max_uploads": link.max_uploads,
        "received_count": sum(1 for item in items if item["received"]),
        "expires_on": magic_service._as_utc(link.expires_at).strftime("%-d %b %Y"),
        "uploads": uploads,
    }


def _consultant_link_cards(
    db: Session,
    engagement_id: str,
    summaries: list[request_summary.RequestSummary],
) -> list[dict]:
    """Build the request-card view without exposing a capability token.

    ``magic_link_rows`` remains the source for link metadata. Receipt events are
    joined here so the Requests page can show one marker and the latest file for
    each requested item, while the assessment table uses the shared summary
    service for its version and count rollups.
    """
    raw_links = (
        db.query(magic_service.MagicLink)
        .filter(magic_service.MagicLink.engagement_id == engagement_id)
        .order_by(magic_service.MagicLink.created_at.desc(), magic_service.MagicLink.id.desc())
        .all()
    )
    if not raw_links:
        return []

    received: dict[str, dict[str, dict]] = defaultdict(dict)
    events = (
        db.query(AuditEvent)
        .filter(
            AuditEvent.entity_type == "magic_link",
            AuditEvent.action == "magic_link.upload_received",
            AuditEvent.entity_id.in_([link.id for link in raw_links]),
        )
        .order_by(AuditEvent.created_at, AuditEvent.id)
        .all()
    )
    for event in events:
        try:
            metadata = json.loads(event.metadata_json or "{}")
        except (json.JSONDecodeError, TypeError):
            continue
        item_key = metadata.get("item_key")
        evidence_id = metadata.get("evidence_id")
        evidence = db.get(Evidence, evidence_id) if evidence_id else None
        if not isinstance(item_key, str) or evidence is None:
            continue
        received[event.entity_id][item_key] = {
            "evidence_id": evidence.id,
            "filename": evidence.original_filename,
            "status": evidence.status,
            "uploaded_at": evidence.created_at,
        }

    summary_by_assessment = {summary.assessment_id: summary for summary in summaries}
    row_by_id = {row["id"]: row for row in magic_service.magic_link_rows(db, engagement_id)}
    cards = []
    for link in raw_links:
        row = row_by_id[link.id]
        items = []
        for item in magic_service.scope_items(link):
            receipt = received.get(link.id, {}).get(item.get("key"))
            item_status = receipt["status"] if receipt else None
            items.append(
                {
                    "title": item.get("title", "Requested item"),
                    "received": receipt is not None and item_status != "rejected",
                    "evidence_id": receipt["evidence_id"] if receipt else None,
                    "filename": receipt["filename"] if receipt else None,
                    "status": item_status,
                    "uploaded_at": receipt["uploaded_at"] if receipt else None,
                }
            )
        received_count = sum(item["received"] for item in items)
        total = len(items)
        raw_scope = json.loads(link.scope_json)
        rfi = raw_scope.get("rfi") if isinstance(raw_scope, dict) else None
        summary = summary_by_assessment.get(rfi.get("assessment_id")) if isinstance(rfi, dict) else None
        if rfi and summary and summary.version is not None:
            source_label = f"From RFI version {summary.version}"
        elif rfi:
            source_label = "From RFI"
        else:
            source_label = "Manual request"
        status = row["status"]
        if status == "active" and total and received_count == total:
            status_label, status_tone = "Complete", "ok"
        elif status == "active":
            status_label, status_tone = "Active", "accent"
        elif status == "expired":
            status_label, status_tone = "Expired", "neutral"
        else:
            status_label, status_tone = "Revoked", "neutral"
        cards.append(
            {
                **row,
                "contact_display": row["contact_name"] or "Client contact",
                "source_label": source_label,
                "items": items,
                "received_count": received_count,
                "total_items": total,
                "progress_percent": (received_count / total * 100) if total else 0,
                "status_label": status_label,
                "status_tone": status_tone,
                "revoke_path": f"/engagements/{engagement_id}/magic-links/{link.id}/revoke",
            }
        )
    return cards


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
        headers=headers or _client_headers(),
    )


def _consultant_context(
    request: Request,
    db: Session,
    engagement_id: str,
    *,
    error: str | None = None,
    new_link_url: str | None = None,
) -> dict:
    summaries = request_summary.engagement_summaries(db, engagement_id)
    engagement = db.get(Engagement, engagement_id)
    client = db.get(Client, engagement.client_id) if engagement else None
    return {
        "request": request,
        "engagement_id": engagement_id,
        "engagement": engagement,
        "client": client,
        "request_summaries": summaries,
        "magic_links": _consultant_link_cards(db, engagement_id, summaries),
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
    toast_message: str | None = None,
    toast_type: str = "success",
):
    headers = dict(_CONSULTANT_HEADERS)
    if toast_message:
        headers["X-Toast-Message"] = toast_message
        headers["X-Toast-Type"] = toast_type
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
        headers=headers,
    )


@router.get("/engagements/{engagement_id}/requests")
def requests_page(
    engagement_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    engagement = db.get(Engagement, engagement_id)
    if engagement is None:
        raise HTTPException(404, "Engagement not found")
    client = db.get(Client, engagement.client_id)
    if client is None:
        raise HTTPException(404, "Client not found")
    return templates.TemplateResponse(
        "pages/requests.html",
        _consultant_context(request, db, engagement_id),
    )


def _form_int(form, name: str, default: int, message: str) -> int:
    raw = form.get(name, default)
    try:
        return int(raw)
    except (TypeError, ValueError) as exc:
        raise magic_service.MagicLinkValidationError(message) from exc


def _form_text(form, name: str) -> str:
    value = form.get(name)
    return value if isinstance(value, str) else ""


def _render_rfi_links(
    request: Request,
    db: Session,
    assessment: Assessment,
    *,
    error: str | None = None,
    new_link_url: str | None = None,
    status_code: int = 200,
    toast_message: str | None = None,
    toast_type: str = "success",
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
    headers = dict(_CONSULTANT_HEADERS)
    if toast_message:
        headers["X-Toast-Message"] = toast_message
        headers["X-Toast-Type"] = toast_type
    return templates.TemplateResponse(
        "partials/rfi_links.html",
        context,
        status_code=status_code,
        headers=headers,
    )


@router.get("/magic/{token}")
def get_magic_link(token: str, request: Request, db: Session = Depends(get_db)):
    link = magic_service.resolve_token(db, token)
    if link is None:
        return _render_invalid(request, db, link=_inactive_link(db, token))
    return _render_upload(request, db, link)


@router.post("/magic/{token}")
async def post_magic_link(token: str, request: Request, db: Session = Depends(get_db)):
    link = magic_service.resolve_token(db, token)
    if link is None:
        return _render_invalid(request, db, link=_inactive_link(db, token))

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
        headers = _client_headers()
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
        contact_name, contact_email = magic_service.validated_contact(
            _form_text(form, "contact_name"), _form_text(form, "contact_email")
        )
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
        magic_service.set_contact(
            db, created.link, contact_name=contact_name, contact_email=contact_email
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
        toast_message="Client link created.",
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
        contact_name, contact_email = magic_service.validated_contact(
            _form_text(form, "contact_name"), _form_text(form, "contact_email")
        )
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
        magic_service.set_contact(
            db, created.link, contact_name=contact_name, contact_email=contact_email
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
        toast_message="Client link created.",
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
    return _render_consultant(
        request,
        db,
        engagement_id,
        toast_message="Client link revoked.",
    )
