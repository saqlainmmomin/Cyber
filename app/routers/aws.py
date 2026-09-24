"""Consultant-triggered AWS evidence routes."""

from __future__ import annotations

from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.client import Client
from app.models.engagement import Engagement
from app.routers.web import templates
from app.services import aws_evidence

router = APIRouter(include_in_schema=False)

_HEADERS = {"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"}


def _render_panel(
    request: Request,
    *,
    engagement_id: str,
    configured: bool,
    form_values: dict,
    error: str | None = None,
    result: aws_evidence.PullResult | None = None,
    rows: list[dict] | None = None,
    status_code: int = 200,
):
    return templates.TemplateResponse(
        request=request,
        name="partials/aws_evidence_panel.html",
        context={
            "request": request,
            "engagement_id": engagement_id,
            "configured": configured,
            "form_values": form_values,
            "error": error,
            "result": result,
            "rows": rows or [],
        },
        status_code=status_code,
        headers=_HEADERS,
    )


@router.get("/engagements/{engagement_id}/aws-evidence", response_class=HTMLResponse)
def aws_evidence_page(
    request: Request,
    engagement_id: str,
    db: Session = Depends(get_db),
):
    engagement = db.get(Engagement, engagement_id)
    if engagement is None:
        raise HTTPException(404, "Engagement not found", headers=_HEADERS)
    client = db.get(Client, engagement.client_id)
    if client is None:
        raise HTTPException(404, "Client not found", headers=_HEADERS)
    context = aws_evidence.page_context(db, engagement)
    context.update({"request": request, "engagement": engagement, "client": client})
    return templates.TemplateResponse(
        request=request,
        name="pages/aws_evidence.html",
        context=context,
        headers=_HEADERS,
    )


@router.post("/engagements/{engagement_id}/aws-evidence/pull", response_class=HTMLResponse)
def aws_evidence_pull(
    request: Request,
    engagement_id: str,
    account_id: str = Form(""),
    role_arn: str = Form(""),
    regions: str = Form(""),
    db: Session = Depends(get_db),
):
    engagement = db.get(Engagement, engagement_id)
    if engagement is None:
        raise HTTPException(404, "Engagement not found", headers=_HEADERS)
    form_values = {"account_id": account_id, "role_arn": role_arn, "regions": regions}
    origin = request.headers.get("origin")
    if origin and urlsplit(origin).netloc != request.headers.get("host"):
        return _render_panel(
            request,
            engagement_id=engagement_id,
            configured=aws_evidence.is_configured(),
            form_values=form_values,
            error=aws_evidence.ORIGIN_REJECTED,
            status_code=403,
        )
    try:
        result = aws_evidence.pull_aws_evidence(
            db,
            engagement_id=engagement_id,
            account_id=account_id,
            role_arn=role_arn,
            regions_raw=regions,
        )
    except aws_evidence.AwsEngagementNotFound as exc:
        raise HTTPException(exc.status_code, exc.message, headers=_HEADERS) from exc
    except aws_evidence.AwsEvidenceError as exc:
        return _render_panel(
            request,
            engagement_id=engagement_id,
            configured=aws_evidence.is_configured(),
            form_values=form_values,
            error=exc.message,
            rows=aws_evidence.aws_evidence_rows(db, engagement_id),
        )
    return _render_panel(
        request,
        engagement_id=engagement_id,
        configured=aws_evidence.is_configured(),
        form_values=form_values,
        result=result,
        rows=aws_evidence.aws_evidence_rows(db, engagement_id),
    )
