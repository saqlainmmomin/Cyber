"""Debug-only Yozora component gallery and template preview routes."""

from collections.abc import Callable
from dataclasses import replace
from datetime import datetime, timezone
import json
from types import SimpleNamespace

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.assessment import Assessment
from app.models.client import Client
from app.models.engagement import Engagement
from app.routers.web import templates
from app.services import aws_evidence, workpaper

router = APIRouter(tags=["design"])

# Debug-only pages that do not have standalone production routes register here.
PREVIEW_PAGES: dict[str, Callable[[Request, Session], Response]] = {}


def login_preview(request: Request, db: Session | None = None) -> Response:
    state = request.query_params.get("state", "default")
    if state not in {"default", "error", "loading"}:
        state = "default"
    return templates.TemplateResponse(
        "pages/login.html",
        {"request": request, "preview_state": state},
    )


PREVIEW_PAGES["login"] = login_preview


def aws_evidence_preview(request: Request, db: Session) -> Response:
    state = request.query_params.get("state", "ready")
    if state not in {"ready", "pulling", "result", "error", "notconfigured"}:
        state = "ready"
    engagement = (
        db.query(Engagement)
        .join(Client, Client.id == Engagement.client_id)
        .filter(Client.name == "Meridian Ledger Technologies")
        .order_by(Engagement.created_at, Engagement.id)
        .first()
        or db.query(Engagement).order_by(Engagement.created_at, Engagement.id).first()
    )
    client = db.get(Client, engagement.client_id) if engagement else None
    engagement = engagement or SimpleNamespace(id="preview-engagement", name="Preview engagement", client_id="preview-client")
    client = client or SimpleNamespace(id="preview-client", name="Meridian Ledger Technologies")
    context = aws_evidence.page_context(db, engagement)
    external_id = "preview-external-id-1234567890"
    context.update(
        {
            "request": request,
            "engagement": engagement,
            "client": client,
            "configured": True,
            "external_id": external_id,
            "suggested_role_name": "YozoraReadOnlyAudit",
            "trust_policy_json": json.dumps(aws_evidence.trust_policy(external_id), indent=2),
            "permissions_policy_json": json.dumps(aws_evidence.permissions_policy(aws_evidence.EXAMPLE_ACCOUNT_ID), indent=2),
            "consultant_policy_json": json.dumps(aws_evidence.consultant_policy(), indent=2).replace("ComplianceEvidenceReadOnly", "YozoraReadOnlyAudit"),
        }
    )
    if state == "result":
        started_at = datetime(2026, 3, 21, 10, tzinfo=timezone.utc)
        context["result"] = aws_evidence.PullResult(
            pull_id="preview-pull-001",
            account_id=aws_evidence.EXAMPLE_ACCOUNT_ID,
            regions=("ap-south-1", "us-east-1"),
            sources=(
                aws_evidence.SourceSummary("aws_config", "ap-south-1", "collected", 142, 12, 3, 127, 0, False, 0),
                aws_evidence.SourceSummary("aws_securityhub", "ap-south-1", "collected", 31, 4, 2, 25, 0, False, 0),
                aws_evidence.SourceSummary("aws_securityhub", "us-east-1", "not_enabled", 0, 0, 0, 0, 0, False, 0),
            ),
            evidence_ids=(),
            started_at=started_at,
            finished_at=datetime(2026, 3, 21, 10, 4, tzinfo=timezone.utc),
        )
    return templates.TemplateResponse(
        "pages/aws_evidence.html",
        context,
    )


PREVIEW_PAGES["aws_evidence"] = aws_evidence_preview


def workpaper_entry_preview(request: Request, db: Session) -> Response:
    state = request.query_params.get("state", "default")
    if state not in {"default", "legacy", "excluded"}:
        state = "default"
    assessments = db.query(Assessment).order_by(Assessment.created_at, Assessment.id).all()
    assessment = assessments[0] if assessments else None
    entry = None
    for candidate in assessments:
        read_model = workpaper.build_workpaper(db, candidate)
        sections = read_model.sections
        candidate_entry = next((item for section in sections for item in section.entries), None)
        candidate_entry = candidate_entry or next(
            (item for section in sections for item in section.excluded_entries),
            None,
        )
        if candidate_entry is not None:
            assessment = candidate
            entry = candidate_entry
            break
    if entry is None:
        assessment = assessment or SimpleNamespace(
            id="preview-assessment",
            display_name="Preview assessment",
            company_name="Meridian Ledger Technologies",
            frameworks=["dpdpa"],
        )
        conclusion = SimpleNamespace(
            framework_id="dpdpa", requirement_id="DPDPA-1", version=1, id="preview-conclusion",
            ai_proposed=True, outcome="compliant", risk_level="low", rationale="Documented practice",
            gaps_identified="None recorded", recommended_action="Maintain the control",
            evidence_summary="Privacy notice.pdf supports the conclusion",
        )
        card = SimpleNamespace(
            conclusion=conclusion, requirement_title="Privacy notice and transparency", state="approved",
            locked=False, legacy_bulk_approval=False, legacy_report_status=None, last_decision=None,
            previous_outcome=None, unsupported_assertion=False, withheld_proposal=None,
        )
        entry = SimpleNamespace(
            card=card, anchor="wp-dpdpa-DPDPA-1", in_scope=True, client_response=None,
            mapped_evidence=[], desk_review_findings=[], ai_proposal=None, revisions=[], findings=[],
        )
    if state == "legacy":
        if hasattr(entry.card, "__dataclass_fields__"):
            entry = replace(entry, card=replace(entry.card, legacy_bulk_approval=True))
        else:
            card_values = vars(entry.card).copy()
            card_values["legacy_bulk_approval"] = True
            entry.card = SimpleNamespace(**card_values)
    elif state == "excluded":
        if hasattr(entry, "__dataclass_fields__"):
            entry = replace(entry, in_scope=False)
        else:
            entry.in_scope = False
    return templates.TemplateResponse(
        "pages/workpaper.html",
        {
            "request": request,
            "assessment": assessment,
            "preview_entry": entry,
            "preview_period_label": "01 Apr 2026 to 30 Jun 2026",
            "preview_cutoff_label": "15 Jul 2026",
        },
    )


PREVIEW_PAGES["workpaper_entry"] = workpaper_entry_preview


def _debug_only() -> None:
    if settings.env.casefold() == "production":
        raise HTTPException(status_code=404, detail="Not found")


@router.get("/design", response_class=HTMLResponse, include_in_schema=False)
def design_gallery(request: Request) -> Response:
    _debug_only()
    return templates.TemplateResponse(
        "pages/design.html",
        {
            "request": request,
            "dark": "dark" in request.query_params,
            "focus": "focus" in request.query_params,
        },
    )


@router.get("/design/pages/{name}", response_class=HTMLResponse, include_in_schema=False)
def design_preview(request: Request, name: str, db: Session = Depends(get_db)) -> Response:
    _debug_only()
    preview = PREVIEW_PAGES.get(name)
    if preview is None:
        raise HTTPException(status_code=404, detail="Not found")
    return preview(request, db)
