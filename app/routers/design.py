"""Debug-only Yozora component gallery and template preview routes."""

from collections.abc import Callable
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
            "form_values": {
                "account_id": aws_evidence.EXAMPLE_ACCOUNT_ID,
                "role_arn": f"arn:aws:iam::{aws_evidence.EXAMPLE_ACCOUNT_ID}:role/YozoraReadOnlyAudit",
                "regions": "ap-south-1, us-east-1",
            },
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
            regions=("eu-west-1",),
            sources=(
                aws_evidence.SourceSummary("aws_config", "eu-west-1", "collected", 12, 8, 2, 2, 0, False, 0),
                aws_evidence.SourceSummary("aws_securityhub", "eu-west-1", "collected", 6, 4, 1, 1, 0, False, 0),
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


def _workpaper_entry_matches(entry, state: str) -> bool:
    if state == "legacy":
        return entry.in_scope and entry.card.legacy_bulk_approval
    if state == "excluded":
        return not entry.in_scope
    return entry.in_scope and entry.card.state == "edited"


def workpaper_entry_preview(request: Request, db: Session) -> Response:
    """Render one real workpaper entry as the entry page (no production route exists).

    ``?entry=<anchor>`` picks an entry; otherwise the state picks the first entry that
    has that shape in the seeded data: an edited conclusion (default), a legacy bulk
    approval (legacy) or a scope-excluded conclusion (excluded). The fixture below is
    used only when the database holds no conclusions at all."""
    state = request.query_params.get("state", "default")
    if state not in {"default", "legacy", "excluded"}:
        state = "default"
    anchor = request.query_params.get("entry")
    assessments = db.query(Assessment).order_by(Assessment.created_at, Assessment.id).all()
    found = []
    for candidate in assessments:
        sections = workpaper.build_workpaper(db, candidate).sections
        found.extend(
            (candidate, item)
            for section in sections
            for item in (*section.entries, *section.excluded_entries)
        )
    match = next(((a, e) for a, e in found if anchor and e.anchor == anchor), None)
    match = match or next(((a, e) for a, e in found if _workpaper_entry_matches(e, state)), None)
    match = match or (found[0] if found else None)
    if match is not None:
        assessment, entry = match
        from app.services.report_basis import basis_for

        basis = basis_for(assessment)
        engagement = db.get(Engagement, assessment.engagement_id) if assessment.engagement_id else None
        client = db.get(Client, engagement.client_id) if engagement else None
    else:
        assessment = SimpleNamespace(
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
            locked=True, legacy_bulk_approval=state == "legacy", legacy_report_status=None, last_decision=None,
            previous_outcome=None, unsupported_assertion=False, withheld_proposal=None,
        )
        entry = SimpleNamespace(
            card=card, anchor="wp-dpdpa-DPDPA-1", in_scope=state != "excluded", client_response=None,
            mapped_evidence=[], desk_review_findings=[], ai_proposal=None, revisions=[], findings=[],
        )
        basis = None
        engagement = client = None
    return templates.TemplateResponse(
        "pages/workpaper.html",
        {
            "request": request,
            "assessment": assessment,
            "preview_entry": entry,
            "preview_basis": basis,
            "engagement": engagement,
            "client": client,
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
