"""Web portal routes — HTML-serving endpoints for the assessment UI."""

import json
import logging
from collections import defaultdict
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import literal_column
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dpdpa.context_questions import CONTEXT_BLOCKS
from app.dpdpa.questionnaire import ANSWER_OPTIONS, build_questionnaire
from app.models.assessment import Assessment, AssessmentDocument
from app.models.client import Client
from app.models.engagement import Engagement
from app.models.questionnaire import QuestionnaireResponse
from app.models.rfi import RFIDocument
from app.services.followup_engine import generate_followups
from app.services.engagement_factory import create_engagement_with_assessment
from app.services.portfolio import (
    build_client_card,
    build_engagement_card,
    framework_badges,
)
from app.services.question_engine import build_adaptive_questionnaire
from app.models.report import GapItem, GapReport
from app.models.conclusion import Conclusion, ConclusionRevision
from app.schemas.assessment import DocumentCategory
from app.services import evidence as evidence_service, findings as finding_service, workpaper
from app.services.evidence import analysis_documents, evidence_panel_rows
from app.services.magic_links import client_upload_rows, magic_link_rows
from app.services.scoring import report_framework_scores
from app.services.conclusion_review import conclusion_cards
from app.utils.review_gate import require_review_approval

from app.template_config import configure_templates

router = APIRouter(tags=["web"])
logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")
configure_templates(templates)

ENABLED_ASSESSMENT_FRAMEWORKS = ("dpdpa", "iso27001", "nist_csf")
ROADMAP_FRAMEWORKS = ("gdpr", "hipaa", "pci_dss")


def _with_toast(response, message: str, toast_type: str = "success"):
    response.headers["X-Toast-Message"] = message
    response.headers["X-Toast-Type"] = toast_type
    return response


# --- Auth dependency ---




def _selected_framework_ids(assessment: Assessment) -> list[str]:
    """Resolve the assessment's selected framework ids. Legacy rows without a
    selection predate multi-framework support and default to DPDPA."""
    return assessment.frameworks


def _selected_framework_names(assessment: Assessment) -> list[str]:
    from app.frameworks.registry import FrameworkRegistry

    names = []
    for fw_id in _selected_framework_ids(assessment):
        fw = FrameworkRegistry.get_or_none(fw_id)
        names.append(fw.name if fw else fw_id.upper())
    return names


def _framework_display(
    assessment: Assessment,
    framework_scores: dict[str, dict],
) -> dict[str, dict]:
    """Build ordered, template-safe framework score display data."""
    from app.frameworks.registry import FrameworkRegistry

    display = {}
    for framework_id in assessment.frameworks:
        framework = FrameworkRegistry.get_or_none(framework_id)
        scores = framework_scores.get(framework_id) or {}
        display[framework_id] = {
            "name": framework.name if framework else framework_id.upper(),
            "version": framework.version if framework else "",
            "score": scores.get("overall_score"),
            "rating": scores.get("overall_rating"),
            "domain_scores": scores.get("domain_scores", {}),
        }
    return display


def _framework_catalog() -> list[dict]:
    from app.frameworks.registry import FrameworkRegistry

    frameworks = []
    for fw_id in ENABLED_ASSESSMENT_FRAMEWORKS + ROADMAP_FRAMEWORKS:
        fw = FrameworkRegistry.get(fw_id)
        frameworks.append({
            "id": fw.id,
            "name": fw.name,
            "version": fw.version,
            "control_count": fw.control_count(),
            "enabled": fw_id in ENABLED_ASSESSMENT_FRAMEWORKS,
        })
    return frameworks


# --- Dashboard ---


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    clients = db.query(Client).order_by(Client.name).all()
    engagements = (
        db.query(Engagement)
        .filter(Engagement.status != "closed")
        .order_by(Engagement.created_at.desc())
        .all()
    )
    linked = (
        db.query(Assessment)
        .filter(
            Assessment.status != "archived",
            Assessment.engagement_id.isnot(None),
        )
        .all()
    )
    unmigrated = (
        db.query(Assessment)
        .filter(
            Assessment.engagement_id.is_(None),
            Assessment.status != "archived",
        )
        .order_by(Assessment.created_at.desc())
        .all()
    )

    assessments_by_engagement = defaultdict(list)
    for assessment in linked:
        assessments_by_engagement[assessment.engagement_id].append(assessment)

    engagements_by_client = defaultdict(list)
    for engagement in engagements:
        engagements_by_client[engagement.client_id].append(
            build_engagement_card(
                engagement,
                assessments_by_engagement[engagement.id],
            )
        )

    client_cards = [
        build_client_card(client, engagements_by_client[client.id])
        for client in clients
    ]
    return templates.TemplateResponse(
        "pages/dashboard.html",
        {
            "request": request,
            "clients": client_cards,
            "unmigrated_assessments": unmigrated,
            "total_client_count": len(clients),
            "total_engagement_count": len(engagements),
        },
    )


# --- Portfolio hierarchy ---


def _is_fragment_request(request: Request) -> bool:
    is_htmx = request.headers.get("HX-Request", "").lower() == "true"
    is_boosted = request.headers.get("HX-Boosted", "").lower() == "true"
    return is_htmx and not is_boosted


def _engagement_cards_for_client(db: Session, client_id: str) -> list[dict]:
    # Hide closed engagements on client detail and its lazy fragment too, for consistency with the dashboard.
    engagements = (
        db.query(Engagement)
        .filter(
            Engagement.client_id == client_id,
            Engagement.status != "closed",
        )
        .order_by(Engagement.created_at.desc())
        .all()
    )
    engagement_ids = [engagement.id for engagement in engagements]
    assessments = (
        db.query(Assessment)
        .filter(
            Assessment.engagement_id.in_(engagement_ids),
            Assessment.status != "archived",
        )
        .all()
        if engagement_ids
        else []
    )
    assessments_by_engagement = defaultdict(list)
    for assessment in assessments:
        assessments_by_engagement[assessment.engagement_id].append(assessment)
    cards = [
        build_engagement_card(
            engagement,
            assessments_by_engagement[engagement.id],
        )
        for engagement in engagements
    ]
    return sorted(cards, key=lambda card: card["last_activity"], reverse=True)


@router.get("/clients/{client_id}", response_class=HTMLResponse)
def client_detail(
    request: Request,
    client_id: str,
    db: Session = Depends(get_db),
):
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(404, "Client not found")
    engagements = _engagement_cards_for_client(db, client_id)
    return templates.TemplateResponse(
        "pages/client_detail.html",
        {
            "request": request,
            "client": client,
            "engagements": engagements,
            "assessment_count": sum(card["assessment_count"] for card in engagements),
            "last_activity": max(
                (card["last_activity"] for card in engagements),
                default=client.updated_at,
            ),
        },
    )


@router.get("/clients/{client_id}/engagements-list", response_class=HTMLResponse)
def client_engagement_list(
    request: Request,
    client_id: str,
    db: Session = Depends(get_db),
):
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(404, "Client not found")
    if not _is_fragment_request(request):
        return RedirectResponse(f"/clients/{client_id}", status_code=307)
    return templates.TemplateResponse(
        "partials/engagement_list.html",
        {"request": request, "engagements": _engagement_cards_for_client(db, client_id)},
    )


@router.get("/engagements/new", response_class=HTMLResponse)
def new_engagement_page(
    request: Request,
    client_id: str | None = None,
    db: Session = Depends(get_db),
):
    return templates.TemplateResponse(
        "pages/new_engagement.html",
        _new_engagement_context(
            request,
            db,
            preselected_client_id=client_id,
        ),
    )


@router.get("/engagements/new/client-fields", response_class=HTMLResponse)
def new_engagement_client_fields(
    request: Request,
    mode: str,
    client_id: str | None = None,
    db: Session = Depends(get_db),
):
    if mode not in {"existing", "new"}:
        raise HTTPException(400, "mode must be 'existing' or 'new'")
    if not _is_fragment_request(request):
        return RedirectResponse("/engagements/new", status_code=307)
    clients = db.query(Client).order_by(Client.name).all()
    return templates.TemplateResponse(
        "partials/client_picker.html",
        {
            "request": request,
            "mode": mode,
            "clients": clients,
            "preselected_client_id": client_id,
            "form_values": None,
        },
    )


@router.get("/engagements/{engagement_id}", response_class=HTMLResponse)
def engagement_detail(
    request: Request,
    engagement_id: str,
    db: Session = Depends(get_db),
):
    engagement = db.get(Engagement, engagement_id)
    if not engagement:
        raise HTTPException(404, "Engagement not found")
    client = db.get(Client, engagement.client_id)
    if not client:
        raise HTTPException(404, "Client not found")
    assessments = (
        db.query(Assessment)
        .filter(
            Assessment.engagement_id == engagement_id,
            Assessment.status != "archived",
        )
        .order_by(Assessment.created_at.desc())
        .all()
    )
    card = build_engagement_card(engagement, assessments)
    assessment_cards = [
        {
            "id": assessment.id,
            "company_name": assessment.company_name,
            "description": assessment.description,
            "status": assessment.status,
            "created_at": assessment.created_at,
            "updated_at": assessment.updated_at,
            "framework_badges": framework_badges(assessment.frameworks),
        }
        for assessment in assessments
    ]
    return templates.TemplateResponse(
        "pages/engagement_detail.html",
        {
            "request": request,
            "engagement": engagement,
            "client": client,
            "card": card,
            "assessments": assessment_cards,
            "engagement_id": engagement_id,
            "magic_links": magic_link_rows(db, engagement_id),
            "client_uploads": client_upload_rows(db, engagement_id),
        },
    )


def _new_engagement_form_values(form) -> dict:
    return {
        "client_mode": form.get("client_mode", ""),
        "client_id": form.get("client_id", ""),
        "company_name": form.get("company_name", ""),
        "industry": form.get("industry", ""),
        "company_size": form.get("company_size", ""),
        "engagement_name": form.get("engagement_name", ""),
        "engagement_type": form.get("engagement_type", "gap_assessment"),
        "description": form.get("description", ""),
        "selected_frameworks": form.getlist("selected_frameworks"),
    }


def _new_engagement_context(
    request: Request,
    db: Session,
    *,
    mode: str | None = None,
    preselected_client_id: str | None = None,
    error: str | None = None,
    form_values: dict | None = None,
) -> dict:
    clients = db.query(Client).order_by(Client.name).all()
    values = form_values or {}
    selected_client_id = values.get("client_id") or preselected_client_id
    return {
        "request": request,
        "frameworks": _framework_catalog(),
        "clients": clients,
        "mode": values.get("client_mode") or mode or (
            "existing" if selected_client_id else "new"
        ),
        "preselected_client_id": selected_client_id,
        "error": error,
        "form_values": form_values,
    }


def _render_new_engagement_error(
    request: Request,
    db: Session,
    error: str,
    form_values: dict,
):
    return templates.TemplateResponse(
        "pages/new_engagement.html",
        _new_engagement_context(
            request,
            db,
            error=error,
            form_values=form_values,
        ),
        status_code=400,
    )


@router.post("/engagements")
async def create_engagement(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    form_values = _new_engagement_form_values(form)
    client_mode = form_values["client_mode"]
    if client_mode not in {"existing", "new"}:
        return _render_new_engagement_error(
            request,
            db,
            "Select an existing client or create a new one.",
            form_values,
        )

    framework_ids = list(dict.fromkeys(form.getlist("selected_frameworks")))
    form_values["selected_frameworks"] = framework_ids
    if not framework_ids:
        return _render_new_engagement_error(
            request,
            db,
            "Select at least one framework to assess against.",
            form_values,
        )
    if any(framework_id not in ENABLED_ASSESSMENT_FRAMEWORKS for framework_id in framework_ids):
        return _render_new_engagement_error(
            request,
            db,
            "One or more selected frameworks are not available for assessment yet.",
            form_values,
        )

    engagement_name = str(form_values["engagement_name"] or "").strip()
    form_values["engagement_name"] = engagement_name
    if not engagement_name:
        return _render_new_engagement_error(
            request,
            db,
            "Engagement name is required.",
            form_values,
        )
    engagement_type = str(form_values["engagement_type"] or "gap_assessment")
    if engagement_type not in {"gap_assessment", "audit", "readiness"}:
        return _render_new_engagement_error(
            request,
            db,
            "Select a valid engagement type.",
            form_values,
        )
    description = str(form_values["description"] or "")

    client = None
    if client_mode == "existing":
        client_id = str(form_values["client_id"] or "").strip()
        client = db.get(Client, client_id) if client_id else None
        if not client:
            return _render_new_engagement_error(
                request,
                db,
                "Select an existing client or create a new one.",
                form_values,
            )
    else:
        company_name = str(form_values["company_name"] or "").strip()
        industry = str(form_values["industry"] or "").strip()
        company_size = str(form_values["company_size"] or "").strip()
        form_values.update(
            {
                "company_name": company_name,
                "industry": industry,
                "company_size": company_size,
            }
        )
        if not company_name or not industry or not company_size:
            return _render_new_engagement_error(
                request,
                db,
                "Client details are required.",
                form_values,
            )
        if db.query(Client).filter(Client.name == company_name).first():
            return _render_new_engagement_error(
                request,
                db,
                f"A client named '{company_name}' already exists — select it instead.",
                form_values,
            )
        client = Client(name=company_name, industry=industry, size=company_size)
        db.add(client)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            return _render_new_engagement_error(
                request,
                db,
                f"A client named '{company_name}' already exists — select it instead.",
                form_values,
            )

    try:
        engagement = create_engagement_with_assessment(
            db,
            client=client,
            engagement_name=engagement_name,
            engagement_type=engagement_type,
            description=description,
            framework_ids=framework_ids,
        )
    except Exception:
        return _render_new_engagement_error(
            request,
            db,
            "Unable to create the engagement. Please try again.",
            form_values,
        )
    return RedirectResponse(f"/engagements/{engagement.id}", status_code=303)


# --- Assessment CRUD ---


@router.get("/assessments/new", response_class=HTMLResponse)
def new_assessment_page(request: Request):
    return RedirectResponse("/engagements/new", status_code=307)


@router.post("/assessments", include_in_schema=False)
@router.post("/assessments/new")
async def create_assessment(
    request: Request,

    company_name: str = Form(...),
    industry: str = Form(...),
    company_size: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db),
):
    # Extract multi-valued frameworks checkboxes from form
    form = await request.form()
    selected_frameworks = form.getlist("selected_frameworks") or form.getlist("frameworks")
    if not selected_frameworks:
        return templates.TemplateResponse(
            "pages/new_engagement.html",
            _new_engagement_context(
                request,
                db,
                error="Select at least one framework to assess against.",
                form_values={
                    "client_mode": "new",
                    "company_name": company_name,
                    "industry": industry,
                    "company_size": company_size,
                    "engagement_name": f"{company_name} Assessment",
                    "engagement_type": "gap_assessment",
                    "description": description,
                    "selected_frameworks": [],
                },
            ),
            status_code=400,
        )

    selected_frameworks = list(dict.fromkeys(selected_frameworks))
    if any(fid not in ENABLED_ASSESSMENT_FRAMEWORKS for fid in selected_frameworks):
        return templates.TemplateResponse(
            "pages/new_engagement.html",
            _new_engagement_context(
                request,
                db,
                error="One or more selected frameworks are not available for assessment yet.",
                form_values={
                    "client_mode": "new",
                    "company_name": company_name,
                    "industry": industry,
                    "company_size": company_size,
                    "engagement_name": f"{company_name} Assessment",
                    "engagement_type": "gap_assessment",
                    "description": description,
                    "selected_frameworks": selected_frameworks,
                },
            ),
            status_code=400,
        )

    client = db.query(Client).filter(Client.name == company_name).first()
    if not client:
        client = Client(name=company_name, industry=industry, size=company_size)
        db.add(client)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            client = db.query(Client).filter(Client.name == company_name).first()
            if not client:
                raise
    try:
        engagement = create_engagement_with_assessment(
            db,
            client=client,
            engagement_name=f"{company_name} Assessment",
            engagement_type="gap_assessment",
            description=description,
            framework_ids=selected_frameworks,
        )
    except Exception:
        return templates.TemplateResponse(
            "pages/new_engagement.html",
            _new_engagement_context(
                request,
                db,
                error="Unable to create the engagement. Please try again.",
                form_values={
                    "client_mode": "new",
                    "company_name": company_name,
                    "industry": industry,
                    "company_size": company_size,
                    "engagement_name": f"{company_name} Assessment",
                    "engagement_type": "gap_assessment",
                    "description": description,
                    "selected_frameworks": selected_frameworks,
                },
            ),
            status_code=400,
        )
    assessment = (
        db.query(Assessment)
        .filter(Assessment.engagement_id == engagement.id)
        .order_by(Assessment.created_at.desc())
        .first()
    )
    return RedirectResponse(f"/assessments/{assessment.id}", status_code=303)


@router.get("/assessments/{assessment_id}/tab/{framework_id}", response_class=HTMLResponse)
def framework_tab(
    request: Request,
    assessment_id: str,
    framework_id: str,
    db: Session = Depends(get_db),
):
    from app.frameworks.registry import FrameworkRegistry

    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404, "Assessment not found")
    if framework_id not in assessment.frameworks:
        raise HTTPException(404, "Framework is not part of this assessment")
    framework = FrameworkRegistry.get_or_none(framework_id)
    if not framework:
        raise HTTPException(404, "Framework not found")
    report = db.query(GapReport).filter(GapReport.assessment_id == assessment_id).first()
    finding_count = 0
    if report:
        finding_count = (
            db.query(GapItem)
            .filter(
                GapItem.report_id == report.id,
                GapItem.framework_id == framework_id,
            )
            .count()
        )
    return templates.TemplateResponse(
        "partials/framework_panel.html",
        {
            "request": request,
            "assessment": assessment,
            "framework": framework,
            "finding_count": finding_count,
        },
    )


@router.get("/evidence/{evidence_id}", response_class=HTMLResponse)
def evidence_detail_page(
    request: Request,
    evidence_id: str,
    db: Session = Depends(get_db),
):
    try:
        evidence = evidence_service.evidence_detail(db, evidence_id)
    except evidence_service.EvidenceError as exc:
        raise HTTPException(exc.status_code, exc.message) from exc
    engagement = db.get(Engagement, evidence["engagement_id"])
    if engagement is None:
        raise HTTPException(404, "Engagement not found")
    client = db.get(Client, engagement.client_id)
    if client is None:
        raise HTTPException(404, "Client not found")
    originating_assessment = (
        db.get(Assessment, evidence["assessment_id"])
        if evidence["assessment_id"]
        else None
    )
    return templates.TemplateResponse(
        "pages/evidence_detail.html",
        {
            "request": request,
            "evidence": evidence,
            "engagement": engagement,
            "client": client,
            "originating_assessment": originating_assessment,
        },
    )


@router.get("/assessments/{assessment_id}", response_class=HTMLResponse)
def assessment_detail(
    request: Request,
    assessment_id: str,
    tab: str | None = None,
    context_error: str | None = None,
    db: Session = Depends(get_db),
):
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404, "Assessment not found")

    documents = evidence_panel_rows(db, assessment_id)
    analysable_document_count = len(analysis_documents(db, assessment_id))

    report = (
        db.query(GapReport)
        .filter(GapReport.assessment_id == assessment_id)
        .first()
    )

    gap_items = []
    if report:
        gap_items = (
            db.query(GapItem)
            .filter(GapItem.report_id == report.id)
            .all()
        )

    # Check questionnaire progress
    response_count = (
        db.query(QuestionnaireResponse)
        .filter(QuestionnaireResponse.assessment_id == assessment_id)
        .count()
    )

    context_done = assessment.context_answers is not None
    scope_done = assessment.scope_answers is not None
    screening_done = assessment.screening_status == "completed"

    # Resolve selected frameworks early — needed by scope tab and display
    from app.frameworks.registry import FrameworkRegistry
    raw_fw_ids = _selected_framework_ids(assessment)
    active_framework = request.query_params.get("framework")
    if tab in raw_fw_ids:
        active_framework = tab
        tab = None
    if active_framework not in raw_fw_ids:
        active_framework = raw_fw_ids[0]
    report_view_mode = request.query_params.get("view")
    if report_view_mode not in ("combined", "per_framework"):
        report_view_mode = "combined" if assessment.is_multi_framework else "per_framework"

    # Default workflow tab: scope if not yet scoped, else documents
    if tab is None:
        tab = "scope" if not scope_done else "documents"

    # Build scope context for the scope tab
    scope_context: dict = {}
    if tab == "scope":
        if scope_done:
            from app.services.scope_profiler import compute_scope_multi
            scope_data = json.loads(assessment.scope_answers)
            result = compute_scope_multi(scope_data, assessment.industry or "", assessment.company_size or "", raw_fw_ids)
            scope_context = {
                "checklist": result["evidence_checklist"],
                "excluded": result["excluded_requirements"],
                "flags": result["flags"],
                "applicable_count": len(result["applicable_requirements"]),
                "total_count": result["total_count"],
            }
        else:
            scope_questions_by_fw = []
            for fw_id in raw_fw_ids:
                fw = FrameworkRegistry.get_or_none(fw_id)
                if fw and fw.scope_questions:
                    scope_questions_by_fw.append({
                        "framework_id": fw.id,
                        "framework_name": fw.name,
                        "questions": [
                            {"id": sq.id, "question": sq.question, "help_text": sq.help_text,
                             "type": sq.type, "options": sq.options}
                            for sq in fw.scope_questions
                        ],
                    })
            scope_context = {
                "scope_questions_by_fw": scope_questions_by_fw,
                "existing": {},
            }

    # Resolve selected framework metadata for display
    selected_frameworks_info = []
    for fw_id in raw_fw_ids:
        fw = FrameworkRegistry.get_or_none(fw_id)
        if fw:
            selected_frameworks_info.append({
                "id": fw.id,
                "name": fw.name,
                "version": fw.version,
            })
    framework_display = {}
    if report and tab in ("report", "questionnaire"):
        framework_display = _framework_display(
            assessment,
            report_framework_scores(report, assessment),
        )

    timeline_steps = [
        ("Scope", scope_done),
        ("Documents", bool(analysable_document_count)),
        ("Desk Review", assessment.desk_review_status == "completed"),
        (
            "Questionnaire",
            assessment.status in ("questionnaire_done", "analyzing", "completed"),
        ),
        ("Analysis", assessment.status == "completed"),
    ]

    return templates.TemplateResponse(
        "pages/assessment.html",
        {
            "request": request,
            "assessment": assessment,
            "documents": documents,
            "analysable_document_count": analysable_document_count,
            "report": report,
            "gap_items": gap_items,
            "tab": tab,
            "response_count": response_count,
            "context_done": context_done,
            "scope_done": scope_done,
            "screening_done": screening_done,
            "context_error": context_error,
            "doc_categories": [c.value for c in DocumentCategory],
            "selected_frameworks": selected_frameworks_info,
            "active_framework": active_framework,
            "report_view_mode": report_view_mode,
            "framework_display": framework_display,
            "active_framework_info": next(
                (fw for fw in selected_frameworks_info if fw["id"] == active_framework),
                selected_frameworks_info[0] if selected_frameworks_info else {"id": active_framework, "name": active_framework},
            ),
            "active_framework_definition": FrameworkRegistry.get(active_framework),
            "active_framework_finding_count": sum(
                1 for item in gap_items
                if item.framework_id == active_framework
            ),
            "timeline_steps": timeline_steps,
            **scope_context,
        },
    )


@router.delete("/assessments/{assessment_id}")
def delete_assessment_web(
    request: Request,
    assessment_id: str,

    db: Session = Depends(get_db),
):
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404)
    assessment.status = "archived"
    db.commit()
    return HTMLResponse("")


# --- Scope ---


@router.get("/assessments/{assessment_id}/scope", response_class=HTMLResponse)
def scope_page(
    request: Request,
    assessment_id: str,
    db: Session = Depends(get_db),
):
    """Redirect to assessment scope tab."""
    return RedirectResponse(f"/assessments/{assessment_id}?tab=scope", status_code=303)


@router.post("/assessments/{assessment_id}/scope/save")
async def save_scope(
    request: Request,
    assessment_id: str,
    db: Session = Depends(get_db),
):
    """Save scope answers, compute applicable requirements, redirect to scope complete view."""
    from app.services.scope_profiler import compute_scope_multi
    from app.frameworks.registry import FrameworkRegistry

    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404)

    # Resolve selected frameworks
    selected_fw_ids = _selected_framework_ids(assessment)

    # Collect all scope question IDs across selected frameworks
    all_scope_q_ids: set[str] = set()
    for fw_id in selected_fw_ids:
        fw = FrameworkRegistry.get_or_none(fw_id)
        if fw:
            for sq in fw.scope_questions:
                all_scope_q_ids.add(sq.id)

    form = await request.form()
    scope_answers = {}
    for qid in all_scope_q_ids:
        value = form.get(qid)
        if value:
            scope_answers[qid] = value

    assessment.scope_answers = json.dumps(scope_answers)

    # Compute applicable requirements across all selected frameworks
    result = compute_scope_multi(
        scope_answers, assessment.industry or "", assessment.company_size or "", selected_fw_ids
    )
    assessment.applicable_requirements = json.dumps(result["applicable_requirements"])

    if assessment.status == "created":
        assessment.status = "scoped"

    db.commit()
    return RedirectResponse(f"/assessments/{assessment_id}?tab=scope", status_code=303)


# --- Evidence checklist export ---


@router.get("/assessments/{assessment_id}/evidence-checklist/pdf")
def download_evidence_checklist_pdf(assessment_id: str, db: Session = Depends(get_db)):
    """Download the evidence request checklist as PDF."""
    from fastapi.responses import Response
    from app.services.scope_profiler import compute_scope_multi
    from app.utils.evidence_checklist_export import generate_evidence_checklist_pdf

    assessment = db.get(Assessment, assessment_id)
    if not assessment or not assessment.scope_answers:
        raise HTTPException(404, "Scope not yet defined")

    scope_answers = json.loads(assessment.scope_answers)
    result = compute_scope_multi(
        scope_answers,
        assessment.industry or "",
        assessment.company_size or "",
        _selected_framework_ids(assessment),
    )

    pdf_bytes = generate_evidence_checklist_pdf(
        company_name=assessment.company_name,
        checklist=result["evidence_checklist"],
        flags=result["flags"],
    )
    filename = f"Evidence-Request-{assessment.company_name.replace(' ', '-')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/assessments/{assessment_id}/evidence-checklist/docx")
def download_evidence_checklist_docx(assessment_id: str, db: Session = Depends(get_db)):
    """Download the evidence request checklist as DOCX."""
    from fastapi.responses import Response
    from app.services.scope_profiler import compute_scope_multi
    from app.utils.evidence_checklist_export import generate_evidence_checklist_docx

    assessment = db.get(Assessment, assessment_id)
    if not assessment or not assessment.scope_answers:
        raise HTTPException(404, "Scope not yet defined")

    scope_answers = json.loads(assessment.scope_answers)
    result = compute_scope_multi(
        scope_answers,
        assessment.industry or "",
        assessment.company_size or "",
        _selected_framework_ids(assessment),
    )

    docx_bytes = generate_evidence_checklist_docx(
        company_name=assessment.company_name,
        checklist=result["evidence_checklist"],
        flags=result["flags"],
    )
    filename = f"Evidence-Request-{assessment.company_name.replace(' ', '-')}.docx"
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# --- Document upload (HTMX) ---


@router.post("/assessments/{assessment_id}/upload", response_class=HTMLResponse)
async def upload_document_web(
    request: Request,
    assessment_id: str,
    category: str = Form(...),
    file: UploadFile = File(...),

    db: Session = Depends(get_db),
):
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404)
    try:
        result = evidence_service.ingest_upload(
            db,
            assessment_id=assessment_id,
            filename=file.filename or "document",
            content=await file.read(),
            category=category,
        )
        if not result.released:
            return templates.TemplateResponse(
                "partials/upload_status.html",
                {"request": request, "error": evidence_service.SCAN_REJECTED_MESSAGE},
            )
    except evidence_service.EvidenceError as exc:
        return templates.TemplateResponse(
            "partials/upload_status.html",
            {"request": request, "error": exc.message},
        )

    response = templates.TemplateResponse(
        "partials/document_list.html",
        {
            "request": request,
            "documents": evidence_panel_rows(db, assessment_id),
            "assessment_id": assessment_id,
        },
    )
    return _with_toast(response, "Document uploaded")


@router.delete("/assessments/{assessment_id}/documents/{document_id}", response_class=HTMLResponse)
def delete_document_web(
    request: Request,
    assessment_id: str,
    document_id: str,

    db: Session = Depends(get_db),
):
    evidence = db.get(evidence_service.Evidence, document_id)
    if evidence is None:
        legacy = db.get(AssessmentDocument, document_id)
        if legacy is not None and legacy.assessment_id == assessment_id:
            raise HTTPException(
                409,
                "Legacy document: run scripts/migrate_documents_to_evidence.py before archiving it.",
            )
        raise HTTPException(404)
    if evidence.assessment_id != assessment_id:
        raise HTTPException(404)
    try:
        evidence_service.transition_evidence(
            db,
            evidence_id=document_id,
            to_status="archived",
            actor=evidence_service.CONSULTANT_ACTOR,
        )
        db.commit()
    except evidence_service.EvidenceError as exc:
        raise HTTPException(exc.status_code, exc.message) from exc
    return templates.TemplateResponse(
        "partials/document_list.html",
        {
            "request": request,
            "documents": evidence_panel_rows(db, assessment_id),
            "assessment_id": assessment_id,
        },
    )


@router.post("/assessments/{assessment_id}/evidence/{evidence_id}/versions", response_class=HTMLResponse)
async def upload_document_version_web(
    request: Request,
    assessment_id: str,
    evidence_id: str,
    change_reason: str = Form(""),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    evidence = db.get(evidence_service.Evidence, evidence_id)
    if evidence is None or evidence.assessment_id != assessment_id:
        raise HTTPException(404)
    try:
        result = evidence_service.ingest_new_version(
            db,
            evidence_id=evidence_id,
            filename=file.filename or "document",
            content=await file.read(),
            change_reason=change_reason,
        )
        if not result.released:
            return templates.TemplateResponse(
                "partials/upload_status.html",
                {"request": request, "error": evidence_service.SCAN_REJECTED_MESSAGE},
            )
    except evidence_service.EvidenceError as exc:
        return templates.TemplateResponse(
            "partials/upload_status.html",
            {"request": request, "error": exc.message},
        )
    response = templates.TemplateResponse(
        "partials/document_list.html",
        {
            "request": request,
            "documents": evidence_panel_rows(db, assessment_id),
            "assessment_id": assessment_id,
        },
    )
    return _with_toast(response, "New version uploaded")


# --- Context questionnaire (HTMX step-by-step) ---


@router.get("/assessments/{assessment_id}/context/block/{block_index}", response_class=HTMLResponse)
def get_context_block(
    request: Request,
    assessment_id: str,
    block_index: int,

    db: Session = Depends(get_db),
):
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404)

    if block_index >= len(CONTEXT_BLOCKS):
        return templates.TemplateResponse(
            "partials/context_complete.html",
            {"request": request, "assessment_id": assessment_id},
        )

    block = CONTEXT_BLOCKS[block_index]
    return templates.TemplateResponse(
        "partials/question_step.html",
        {
            "request": request,
            "assessment_id": assessment_id,
            "block": block,
            "block_index": block_index,
            "total_blocks": len(CONTEXT_BLOCKS),
            "is_context": True,
        },
    )


@router.post("/assessments/{assessment_id}/context/submit", response_class=HTMLResponse)
def submit_context_web(
    request: Request,
    assessment_id: str,

    db: Session = Depends(get_db),
):
    from app.services.context_profiler import derive_risk_profile

    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404)

    form_data = {}  # Will be populated from HTMX form
    # Parse the accumulated form data
    # Context answers are sent as hidden fields with name=question_id
    return RedirectResponse(f"/assessments/{assessment_id}?tab=questionnaire", status_code=303)


@router.post("/assessments/{assessment_id}/context/save", response_class=HTMLResponse)
async def save_context_answers(
    request: Request,
    assessment_id: str,

    db: Session = Depends(get_db),
):
    """Save all context answers from the multi-step form and derive risk profile."""
    from app.services.context_profiler import derive_risk_profile

    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404)

    form = await request.form()
    answers = []
    for block in CONTEXT_BLOCKS:
        for q in block["questions"]:
            qid = q["id"]
            if q["type"] == "multi_select":
                values = form.getlist(qid)
                if values:
                    answers.append({"question_id": qid, "answer": values})
            else:
                value = form.get(qid)
                if value:
                    answers.append({"question_id": qid, "answer": value})

    assessment.context_answers = json.dumps(answers)

    context_error = None
    try:
        profile = derive_risk_profile(
            context_answers=answers,
            industry=assessment.industry,
            company_size=assessment.company_size,
        )
        assessment.context_profile = json.dumps(profile)
    except Exception as e:
        context_error = str(e)

    if assessment.status in ("created", "documents_uploaded"):
        assessment.status = "context_gathered"
    db.commit()

    redirect_url = f"/assessments/{assessment_id}?tab=questionnaire"
    if context_error:
        redirect_url += f"&context_error={context_error}"
    return RedirectResponse(redirect_url, status_code=303)


# --- Compliance questionnaire ---


@router.get("/assessments/{assessment_id}/questionnaire/sections", response_class=HTMLResponse)
def get_questionnaire_sections_web(
    request: Request,
    assessment_id: str,

    db: Session = Depends(get_db),
):
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404)

    # Build adaptive questionnaire (merges base + industry, modulated by desk review)
    result = build_adaptive_questionnaire(assessment_id, db)
    sections = result["sections"]
    stats = result["stats"]

    # Load existing responses
    existing = {}
    responses = (
        db.query(QuestionnaireResponse)
        .filter(QuestionnaireResponse.assessment_id == assessment_id)
        .all()
    )
    for r in responses:
        existing[r.question_id] = {
            "answer": r.answer,
            "notes": r.notes,
            "evidence_reference": r.evidence_reference,
            "na_reason": r.na_reason,
            "confidence": r.confidence,
            "answer_source": r.answer_source,
        }

    return templates.TemplateResponse(
        "partials/questionnaire_sections.html",
        {
            "request": request,
            "assessment_id": assessment_id,
            "sections": sections,
            "existing": existing,
            "stats": stats,
        },
    )


@router.get("/assessments/{assessment_id}/questionnaire/section/{section_id}", response_class=HTMLResponse)
def get_section_questions(
    request: Request,
    assessment_id: str,
    section_id: str,

    db: Session = Depends(get_db),
):
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404)

    # Use adaptive engine and find the requested section
    result = build_adaptive_questionnaire(assessment_id, db)
    target_section = None
    for s in result["sections"]:
        if s["section_id"] == section_id:
            target_section = s
            break

    if not target_section:
        raise HTTPException(404, "Section not found")

    # Load existing responses
    existing = {}
    responses = (
        db.query(QuestionnaireResponse)
        .filter(QuestionnaireResponse.assessment_id == assessment_id)
        .all()
    )
    for r in responses:
        existing[r.question_id] = {
            "answer": r.answer,
            "notes": r.notes,
            "evidence_reference": r.evidence_reference,
        }

    return templates.TemplateResponse(
        "partials/section_questions.html",
        {
            "request": request,
            "assessment_id": assessment_id,
            "section_id": section_id,
            "section_title": target_section["section_title"],
            "chapter_title": target_section["chapter_title"],
            "questions": target_section["questions"],
            "existing": existing,
        },
    )


@router.post("/assessments/{assessment_id}/questionnaire/save", response_class=HTMLResponse)
async def save_questionnaire_responses(
    request: Request,
    assessment_id: str,

    db: Session = Depends(get_db),
):
    """Save questionnaire responses for a section (HTMX partial submit)."""
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404)

    form = await request.form()
    section_id = form.get("section_id", "")

    # Use adaptive engine to get section questions (includes industry questions)
    result = build_adaptive_questionnaire(assessment_id, db)
    section_questions = []
    for s in result["sections"]:
        if s["section_id"] == section_id:
            section_questions = [q for q in s["questions"] if q.get("status") != "skipped"]
            break

    for q in section_questions:
        qid = q["id"]
        answer = form.get(f"answer_{qid}")
        if not answer:
            continue
        if answer not in ANSWER_OPTIONS:
            logger.warning(
                "Skipping invalid questionnaire answer during web save",
                extra={"assessment_id": assessment_id, "question_id": qid, "answer": answer},
            )
            continue
        notes = form.get(f"notes_{qid}", "")
        evidence = form.get(f"evidence_{qid}", "")

        existing = (
            db.query(QuestionnaireResponse)
            .filter(
                QuestionnaireResponse.assessment_id == assessment_id,
                QuestionnaireResponse.question_id == qid,
            )
            .first()
        )
        if existing:
            # Track answer source provenance for audit trail
            if existing.answer_source == "document":
                # Human is confirming or overriding a document pre-fill
                existing.answer_source = (
                    "document_confirmed" if answer == existing.answer
                    else "human_override"
                )
            elif existing.answer_source not in ("human", "human_override", "document_confirmed"):
                existing.answer_source = "human"
            existing.answer = answer
            existing.notes = notes or None
            existing.evidence_reference = evidence or None
        else:
            db.add(QuestionnaireResponse(
                assessment_id=assessment_id,
                question_id=qid,
                answer=answer,
                notes=notes or None,
                evidence_reference=evidence or None,
                answer_source="human",
            ))

    # Save follow-up responses (form fields named followup_FU.{parent_id}.{n})
    for key in form.keys():
        if key.startswith("followup_FU."):
            fu_answer = form.get(key, "").strip()
            if not fu_answer:
                continue
            fu_id = key.replace("followup_", "")  # e.g., "FU.CH2.CONSENT.1.1"
            existing_fu = (
                db.query(QuestionnaireResponse)
                .filter(
                    QuestionnaireResponse.assessment_id == assessment_id,
                    QuestionnaireResponse.question_id == fu_id,
                )
                .first()
            )
            if existing_fu:
                existing_fu.answer = fu_answer
            else:
                # Extract parent question ID from FU ID: FU.{parent_id}.{n}
                parts = fu_id.split(".")
                parent_id = ".".join(parts[1:-1]) if len(parts) > 2 else ""
                db.add(QuestionnaireResponse(
                    assessment_id=assessment_id,
                    question_id=fu_id,
                    answer=fu_answer,
                    notes=f"Follow-up to {parent_id}",
                ))

    if assessment.status not in ("analyzing", "completed"):
        assessment.status = "questionnaire_done"
    db.commit()

    response = templates.TemplateResponse(
        "partials/section_saved.html",
        {"request": request, "section_id": section_id, "assessment_id": assessment_id},
    )
    return _with_toast(response, "Section saved")


# --- Follow-up generation ---


@router.post("/assessments/{assessment_id}/questionnaire/followup", response_class=HTMLResponse)
async def generate_followup_questions(
    request: Request,
    assessment_id: str,
    db: Session = Depends(get_db),
):
    """Generate follow-up questions based on answer (HTMX, called on radio change)."""
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404)

    form = await request.form()
    question_id = form.get("question_id", "")
    answer = form.get("answer", "")

    if not question_id or not answer:
        return HTMLResponse("")

    # Find the question in adaptive questionnaire
    result = build_adaptive_questionnaire(assessment_id, db)
    target_q = None
    for s in result["sections"]:
        for q in s["questions"]:
            if q["id"] == question_id:
                target_q = q
                break
        if target_q:
            break

    if not target_q:
        return HTMLResponse("")

    # Only generate follow-ups for questions with follow-up enabled
    if not target_q.get("follow_up_enabled"):
        # Still check if answer is weak enough on critical questions
        from app.services.followup_engine import _assess_trigger
        trigger = _assess_trigger(
            answer, target_q.get("criticality", "medium"),
            target_q.get("desk_review_evidence"), target_q.get("desk_review_note"),
        )
        if trigger["level"] == "none":
            return HTMLResponse("")

    try:
        followups = generate_followups(
            question_text=target_q["question"],
            question_id=question_id,
            answer=answer,
            criticality=target_q.get("criticality", "medium"),
            maps_to=target_q.get("maps_to", []),
            desk_review_evidence=target_q.get("desk_review_evidence"),
            desk_review_note=target_q.get("desk_review_note"),
            guidance=target_q.get("guidance", ""),
        )
    except Exception:
        # Follow-up generation is best-effort — don't block the questionnaire
        return HTMLResponse("")

    if not followups:
        return HTMLResponse("")

    return templates.TemplateResponse(
        "partials/followup_questions.html",
        {"request": request, "assessment_id": assessment_id, "followups": followups},
    )


# --- Screening pass (Phase 3) ---


@router.get("/assessments/{assessment_id}/screening", response_class=HTMLResponse)
def screening_form(
    request: Request,
    assessment_id: str,
    db: Session = Depends(get_db),
):
    """Serve the 9-question domain screening form."""
    from app.services.screening import get_domain_coverage

    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404)

    domains = get_domain_coverage()
    screening_done = assessment.screening_status == "completed"

    return templates.TemplateResponse(
        "partials/screening_form.html",
        {
            "request": request,
            "assessment_id": assessment_id,
            "domains": domains,
            "screening_done": screening_done,
        },
    )


@router.post("/assessments/{assessment_id}/screening/submit", response_class=HTMLResponse)
async def submit_screening(
    request: Request,
    assessment_id: str,
    db: Session = Depends(get_db),
):
    """Process screening form submission, run Claude inference, redirect to questionnaire."""
    from app.services.screening import run_screening_pass, get_domain_coverage

    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404)

    form = await request.form()
    domains = get_domain_coverage()
    domain_answers = {d["id"]: form.get(d["id"], "") for d in domains}

    try:
        run_screening_pass(assessment_id, domain_answers, db)
    except Exception as e:
        logger.error("Screening failed for assessment %s: %s", assessment_id, e)
        return templates.TemplateResponse(
            "partials/screening_form.html",
            {
                "request": request,
                "assessment_id": assessment_id,
                "domains": domains,
                "screening_done": False,
                "error": str(e),
            },
        )

    return RedirectResponse(
        f"/assessments/{assessment_id}?tab=questionnaire",
        status_code=303,
    )


# --- Analysis trigger ---


@router.post("/assessments/{assessment_id}/run-analysis", response_class=HTMLResponse)
def run_analysis_web(
    request: Request,
    assessment_id: str,

    db: Session = Depends(get_db),
):
    """Trigger analysis: set status to analyzing, kick off in background via direct call."""
    from app.routers.analysis import trigger_analysis

    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404)

    # Run analysis synchronously (15-30s). The HTMX polling handles UX.
    # Set status first so the poll shows "running"
    assessment.status = "analyzing"
    db.commit()

    try:
        # Use a fresh db session to avoid conflicts
        from app.database import SessionLocal
        analysis_db = SessionLocal()
        try:
            trigger_analysis(assessment_id, db=analysis_db)
        finally:
            analysis_db.close()
    except Exception:
        assessment.status = "error"
        db.commit()

    response = templates.TemplateResponse(
        "partials/analysis_running.html",
        {"request": request, "assessment_id": assessment_id},
    )
    return _with_toast(response, "Analysis started", "info")


@router.get("/assessments/{assessment_id}/analysis-status", response_class=HTMLResponse)
def analysis_status(
    request: Request,
    assessment_id: str,

    db: Session = Depends(get_db),
):
    """Poll endpoint for analysis completion."""
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404)

    if assessment.status == "completed":
        report = db.query(GapReport).filter(GapReport.assessment_id == assessment_id).first()
        return templates.TemplateResponse(
            "partials/analysis_complete.html",
            {
                "request": request,
                "assessment_id": assessment_id,
                "report": report,
                "framework_display": _framework_display(
                    assessment,
                    report_framework_scores(report, assessment) if report else {},
                ),
            },
        )
    elif assessment.status == "error":
        return templates.TemplateResponse(
            "partials/analysis_error.html",
            {"request": request, "assessment_id": assessment_id},
        )

    return templates.TemplateResponse(
        "partials/analysis_running.html",
        {"request": request, "assessment_id": assessment_id},
    )


# --- Report helpers ---

# Ordered prefix → penalty (₹ Crore) under DPDPA 2023 Schedule
_PENALTY_MAP = [
    ("CH2.SECURITY", 250),
    ("BN.NOTIFY",    250),
    ("CH4.CHILD",    200),
    ("CH4.SDF",       50),
    ("CH2.CONSENT",   50),
    ("CM.",           50),
    ("CH2.NOTICE",    50),
    ("CH2.PURPOSE",   50),
    ("CH2.MINIMIZE",  50),
    ("CH2.ACCURACY",  50),
    ("CH3.",          50),
    ("CB.TRANSFER",   50),
]

_DOMAIN_MAP = [
    ("CH2.CONSENT", "Consent Management"),
    ("CM.",         "Consent Management"),
    ("CH2.NOTICE",  "Notice & Transparency"),
    ("CH2.PURPOSE", "Purpose Limitation"),
    ("CH2.MINIMIZE","Data Minimization"),
    ("CH2.SECURITY","Data Security"),
    ("BN.NOTIFY",   "Breach Response"),
    ("CH3.",        "Data Subject Rights"),
    ("CH4.SDF",     "Governance & Oversight"),
    ("CH4.CHILD",   "Children's Data Protection"),
    ("CB.TRANSFER", "Cross-Border Transfers"),
    ("CH2.ACCURACY","Data Accuracy"),
]

_ROOT_CAUSE_LABELS = {
    "policy":     "Policy & Documentation",
    "people":     "People & Training",
    "process":    "Process & Operations",
    "technology": "Technology & Controls",
    "governance": "Governance & Oversight",
}


def _compute_chapter_status_counts(gap_items) -> dict:
    """Per-chapter breakdown of compliance statuses for stacked bar chart."""
    counts: dict[str, dict] = {}
    for item in gap_items:
        ch = item.chapter or "unknown"
        if ch not in counts:
            counts[ch] = {
                "compliant": 0, "partially_compliant": 0,
                "non_compliant": 0, "not_applicable": 0,
                "not_assessed": 0, "total": 0,
            }
        status = item.compliance_status or "not_assessed"
        counts[ch][status] = counts[ch].get(status, 0) + 1
        counts[ch]["total"] += 1
    return counts


def _compute_business_impact(gap_items) -> dict:
    """Regulatory exposure tier, affected domains, and high-severity count."""
    max_penalty = 0
    affected_domains: set[str] = set()
    critical_high_count = 0

    for item in gap_items:
        if item.compliance_status not in ("non_compliant", "partially_compliant"):
            continue
        req_id = item.requirement_id or ""
        for prefix, penalty in _PENALTY_MAP:
            if req_id.startswith(prefix):
                max_penalty = max(max_penalty, penalty)
                break
        else:
            max_penalty = max(max_penalty, 50)
        for prefix, domain in _DOMAIN_MAP:
            if req_id.startswith(prefix):
                affected_domains.add(domain)
                break
        if item.risk_level in ("critical", "high"):
            critical_high_count += 1

    return {
        "max_penalty_cr": max_penalty,
        "affected_domains": sorted(affected_domains),
        "critical_high_count": critical_high_count,
        "has_gaps": max_penalty > 0,
    }


def _compute_root_cause_counts(gap_items) -> dict:
    """Count non-compliant/partial gaps by root cause category, with relative bar widths."""
    raw: dict[str, int] = {}
    for item in gap_items:
        if item.compliance_status not in ("non_compliant", "partially_compliant"):
            continue
        rc = item.root_cause_category
        if rc:
            raw[rc] = raw.get(rc, 0) + 1
    if not raw:
        return {}
    max_count = max(raw.values())
    return {
        rc: {
            "count": count,
            "label": _ROOT_CAUSE_LABELS.get(rc, rc.title()),
            "pct": round(count / max_count * 100),
        }
        for rc, count in sorted(raw.items(), key=lambda x: -x[1])
    }


# --- Report view ---


@router.get("/assessments/{assessment_id}/report", response_class=HTMLResponse)
def assessment_report_page(
    request: Request,
    assessment_id: str,
    view: str | None = None,
    db: Session = Depends(get_db),
):
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404)
    view_mode = view or ("combined" if assessment.is_multi_framework else "per_framework")
    if view_mode not in ("combined", "per_framework"):
        raise HTTPException(400, "view must be 'combined' or 'per_framework'")
    is_htmx = request.headers.get("HX-Request", "").lower() == "true"
    is_boosted = request.headers.get("HX-Boosted", "").lower() == "true"
    if is_htmx and not is_boosted:
        return report_summary(request, assessment_id, view_mode, db)
    return assessment_detail(request, assessment_id, tab="report", db=db)


@router.get("/assessments/{assessment_id}/report-summary", response_class=HTMLResponse)
def report_summary(
    request: Request,
    assessment_id: str,
    view: str | None = None,
    db: Session = Depends(get_db),
):
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404)

    view_mode = view or ("combined" if assessment.is_multi_framework else "per_framework")
    if view_mode not in ("combined", "per_framework"):
        raise HTTPException(400, "view must be 'combined' or 'per_framework'")
    active_framework = request.query_params.get("framework")
    if active_framework not in assessment.frameworks:
        active_framework = assessment.frameworks[0]

    report = db.query(GapReport).filter(GapReport.assessment_id == assessment_id).first()
    if not report:
        return templates.TemplateResponse(
            "partials/no_report.html",
            {"request": request, "assessment_id": assessment_id},
        )

    gap_items = db.query(GapItem).filter(GapItem.report_id == report.id).all()
    chapter_scores = json.loads(report.chapter_scores) if report.chapter_scores else {}

    is_multi_framework = assessment.is_multi_framework
    framework_display = _framework_display(
        assessment,
        report_framework_scores(report, assessment),
    )

    # Count by status
    status_counts: dict[str, int] = {}
    for item in gap_items:
        status_counts[item.compliance_status] = status_counts.get(item.compliance_status, 0) + 1

    # Check if RFI exists
    rfi = db.query(RFIDocument).filter(RFIDocument.assessment_id == assessment_id).first()

    # Derived visualisation data
    chapter_status_counts = _compute_chapter_status_counts(gap_items)
    business_impact = _compute_business_impact(gap_items)
    root_cause_counts = _compute_root_cause_counts(gap_items)

    # Critical findings: non/partial, risk=critical|high, sorted by priority then severity
    _severity_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    critical_findings = sorted(
        [i for i in gap_items
         if i.compliance_status in ("non_compliant", "partially_compliant")
         and i.risk_level in ("critical", "high")],
        key=lambda x: (x.remediation_priority or 3, _severity_rank.get(x.risk_level, 2)),
    )[:5]

    # Quick wins: non/partial, low effort, priority <= 2
    quick_wins = sorted(
        [i for i in gap_items
         if i.compliance_status in ("non_compliant", "partially_compliant")
         and i.remediation_effort == "low"
         and (i.remediation_priority or 99) <= 2],
        key=lambda x: x.remediation_priority or 3,
    )[:4]

    has_dpdpa = "dpdpa" in assessment.frameworks

    applicable_gap_items = [
        item for item in gap_items if item.compliance_status != "not_applicable"
    ]
    remediation_counts = {
        "open": sum(
            1 for item in applicable_gap_items
            if (item.remediation_status or "open") == "open"
        ),
        "in_progress": sum(
            1 for item in applicable_gap_items
            if item.remediation_status == "in_progress"
        ),
        "closed": sum(
            1 for item in applicable_gap_items
            if item.remediation_status == "closed"
        ),
        "accepted_risk": sum(
            1 for item in applicable_gap_items
            if item.remediation_status == "accepted_risk"
        ),
        "total": len(applicable_gap_items),
    }

    comparable_assessments = (
        db.query(Assessment)
        .filter(
            Assessment.company_name == assessment.company_name,
            Assessment.id != assessment_id,
            Assessment.status == "completed",
            Assessment.review_status == "approved",
        )
        .order_by(Assessment.created_at.desc())
        .limit(5)
        .all()
    )

    gap_items_by_chapter = defaultdict(list)
    for item in gap_items:
        gap_items_by_chapter[item.chapter].append(item)

    reviewed_item = next((item for item in gap_items if item.reviewed_by), None)
    timeline_steps = [
        ("Scope", assessment.scope_answers is not None),
        ("Documents", bool(analysis_documents(db, assessment_id))),
        ("Desk Review", assessment.desk_review_status == "completed"),
        (
            "Questionnaire",
            assessment.status in ("questionnaire_done", "analyzing", "completed"),
        ),
        ("Analysis", assessment.status == "completed"),
    ]

    return templates.TemplateResponse(
        "partials/report_summary.html",
        {
            "request": request,
            "assessment_id": assessment_id,
            "report": report,
            "gap_items": gap_items,
            "chapter_scores": chapter_scores,
            "status_counts": status_counts,
            "chapter_status_counts": chapter_status_counts,
            "business_impact": business_impact,
            "root_cause_counts": root_cause_counts,
            "critical_findings": critical_findings,
            "quick_wins": quick_wins,
            "rfi": rfi,
            "is_multi_framework": is_multi_framework,
            "framework_display": framework_display,
            "view_mode": view_mode,
            "active_framework": active_framework,
            "has_dpdpa": has_dpdpa,
            "remediation_counts": remediation_counts,
            "comparable_assessments": comparable_assessments,
            "gap_items_by_chapter": dict(gap_items_by_chapter),
            "review_status": assessment.review_status,
            "reviewed_by": reviewed_item.reviewed_by if reviewed_item else None,
            "reviewed_at": reviewed_item.reviewed_at if reviewed_item else None,
            "timeline_steps": timeline_steps,
        },
    )


@router.get("/assessments/{assessment_id}/review", response_class=HTMLResponse)
def review_page(
    request: Request,
    assessment_id: str,
    db: Session = Depends(get_db),
):
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404, "Assessment not found")

    report = (
        db.query(GapReport)
        .filter(GapReport.assessment_id == assessment_id)
        .first()
    )
    if not report:
        raise HTTPException(400, "No report - run analysis first")

    gap_items = db.query(GapItem).filter(GapItem.report_id == report.id).all()
    draft_count = sum(
        1 for item in gap_items
        if (item.review_status or "draft") == "draft"
    )
    reviewed_item = next((item for item in gap_items if item.reviewed_by), None)

    return templates.TemplateResponse(
        "pages/review.html",
        {
            "request": request,
            "assessment": assessment,
            "gap_items": gap_items,
            "draft_count": draft_count,
            "reviewer_name": reviewed_item.reviewed_by if reviewed_item else "",
        },
    )


def _latest_reviewer_name(db: Session, assessment_id: str) -> str:
    latest_consultant = (
        db.query(ConclusionRevision)
        .join(
            Conclusion,
            ConclusionRevision.conclusion_id == Conclusion.id,
        )
        .filter(
            Conclusion.assessment_id == assessment_id,
            ConclusionRevision.actor.startswith("consultant:"),
        )
        .order_by(
            ConclusionRevision.created_at.desc(),
            literal_column("conclusion_revisions.rowid").desc(),
        )
        .first()
    )
    return (
        latest_consultant.actor.removeprefix("consultant:")
        if latest_consultant
        else ""
    )


@router.get("/assessments/{assessment_id}/conclusions", response_class=HTMLResponse)
def conclusions_page(
    request: Request,
    assessment_id: str,
    db: Session = Depends(get_db),
):
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404, "Assessment not found")

    cards = conclusion_cards(db, assessment_id)
    counts = {
        "pending": sum(card.state == "pending" for card in cards),
        "rejected": sum(card.state == "rejected" for card in cards),
        "approved": sum(
            card.state == "approved" and not card.legacy_bulk_approval
            for card in cards
        ),
        "edited": sum(card.state == "edited" for card in cards),
        "legacy_bulk": sum(card.legacy_bulk_approval for card in cards),
    }
    return templates.TemplateResponse(
        request=request,
        name="pages/conclusions.html",
        context={
            "request": request,
            "assessment": assessment,
            "cards": cards,
            "counts": counts,
            "reviewer_name": _latest_reviewer_name(db, assessment_id),
        },
    )


@router.get("/assessments/{assessment_id}/workpaper", response_class=HTMLResponse)
def workpaper_page(
    request: Request,
    assessment_id: str,
    db: Session = Depends(get_db),
):
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        raise HTTPException(404, "Assessment not found")
    wp = workpaper.build_workpaper(db, assessment)
    return templates.TemplateResponse(
        request=request,
        name="pages/workpaper.html",
        context={"request": request, "assessment": assessment, "wp": wp},
    )


@router.get("/assessments/{assessment_id}/findings", response_class=HTMLResponse)
def findings_page(
    request: Request,
    assessment_id: str,
    db: Session = Depends(get_db),
):
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        raise HTTPException(404, "Assessment not found")
    page = finding_service.findings_page(db, assessment_id)
    return templates.TemplateResponse(
        request=request,
        name="pages/findings.html",
        context={
            "request": request,
            "assessment": assessment,
            "page": page,
            "reviewer_name": _latest_reviewer_name(db, assessment_id),
        },
    )


@router.get(
    "/assessments/{assessment_id}/compare/{other_id}",
    response_class=HTMLResponse,
)
def comparison_page(
    request: Request,
    assessment_id: str,
    other_id: str,
    db: Session = Depends(get_db),
):
    from app.services.scoring import compute_delta

    assessment = require_review_approval(assessment_id, db)
    previous_assessment = require_review_approval(other_id, db)
    if assessment.company_name != previous_assessment.company_name:
        raise HTTPException(400, "Assessments must belong to the same company")
    if assessment.status != "completed" or previous_assessment.status != "completed":
        raise HTTPException(400, "Both assessments must be completed")

    current_report = (
        db.query(GapReport)
        .filter(GapReport.assessment_id == assessment_id)
        .first()
    )
    previous_report = (
        db.query(GapReport)
        .filter(GapReport.assessment_id == other_id)
        .first()
    )
    if not current_report or not previous_report:
        raise HTTPException(404, "Reports not found")

    current_items = (
        db.query(GapItem)
        .filter(GapItem.report_id == current_report.id)
        .all()
    )
    previous_items = (
        db.query(GapItem)
        .filter(GapItem.report_id == previous_report.id)
        .all()
    )
    result = compute_delta(current_items, previous_items)
    current_scores = report_framework_scores(current_report, assessment)
    previous_scores = report_framework_scores(previous_report, previous_assessment)
    framework_names = dict(zip(assessment.frameworks, _selected_framework_names(assessment)))
    framework_deltas = []
    for framework_id in assessment.frameworks:
        current = current_scores.get(framework_id)
        previous = previous_scores.get(framework_id)
        current_score = current.get("overall_score") if current else None
        previous_score = previous.get("overall_score") if previous else None
        framework_deltas.append({
            "framework_id": framework_id,
            "name": framework_names[framework_id],
            "current": current_score,
            "previous": previous_score,
            "delta": (
                round(current_score - previous_score, 1)
                if current_score is not None and previous_score is not None
                else None
            ),
        })

    return templates.TemplateResponse(
        "pages/comparison.html",
        {
            "request": request,
            "assessment": assessment,
            "current_report": current_report,
            "previous_report": previous_report,
            "framework_deltas": framework_deltas,
            "deltas": result["deltas"],
            "delta_summary": result["summary"],
        },
    )


# --- RFI Generation + Download ---


@router.post("/assessments/{assessment_id}/generate-rfi", response_class=HTMLResponse)
def generate_rfi_web(
    request: Request,
    assessment_id: str,
    db: Session = Depends(get_db),
):
    """Generate RFI document from gap analysis results."""
    from app.models.desk_review import DeskReviewFinding
    from app.services.rfi_generator import generate_rfi

    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404)

    report = db.query(GapReport).filter(GapReport.assessment_id == assessment_id).first()
    if not report:
        raise HTTPException(400, "Run gap analysis first")

    gap_items = db.query(GapItem).filter(GapItem.report_id == report.id).all()
    gap_dicts = [
        {
            "requirement_id": g.requirement_id,
            "requirement_title": g.requirement_title,
            "chapter": g.chapter,
            "compliance_status": g.compliance_status,
            "current_state": g.current_state,
            "gap_description": g.gap_description,
            "risk_level": g.risk_level,
            "remediation_action": g.remediation_action,
            "remediation_priority": g.remediation_priority,
            "evidence_quote": g.evidence_quote,
        }
        for g in gap_items
    ]

    # Desk review absences and signals
    absences = [
        {"requirement_id": f.requirement_id, "content": f.content}
        for f in db.query(DeskReviewFinding).filter(
            DeskReviewFinding.assessment_id == assessment_id,
            DeskReviewFinding.finding_type == "absence",
        ).all()
    ]
    signals = [
        {"content": f.content, "severity": f.severity, "requirement_id": f.requirement_id}
        for f in db.query(DeskReviewFinding).filter(
            DeskReviewFinding.assessment_id == assessment_id,
            DeskReviewFinding.finding_type == "signal",
        ).all()
    ]

    try:
        result = generate_rfi(
            assessment_id=assessment_id,
            company_name=assessment.company_name,
            industry=assessment.industry or "other",
            gap_items=gap_dicts,
            desk_review_absences=absences or None,
            desk_review_signals=signals or None,
            framework_names=_selected_framework_names(assessment),
        )
    except Exception as e:
        return HTMLResponse(f'<div class="text-sm text-red-600">RFI generation failed: {e}</div>')

    # Delete existing RFI for this assessment
    existing_rfi = db.query(RFIDocument).filter(RFIDocument.assessment_id == assessment_id).first()
    if existing_rfi:
        db.delete(existing_rfi)

    rfi = RFIDocument(
        assessment_id=assessment_id,
        title=result["title"],
        introduction=result["introduction"],
        evidence_items=json.dumps(result["evidence_items"]),
        response_instructions=result["response_instructions"],
        appendix=result.get("appendix", ""),
        total_items=result["total_items"],
        critical_items=result["critical_items"],
        raw_ai_response=result.get("raw_ai_response"),
    )
    db.add(rfi)
    db.commit()

    response = templates.TemplateResponse(
        "partials/rfi_generated.html",
        {"request": request, "assessment_id": assessment_id, "rfi": rfi},
    )
    return _with_toast(response, "RFI generated")


@router.get("/assessments/{assessment_id}/rfi/pdf")
def download_rfi_pdf(assessment_id: str, db: Session = Depends(get_db)):
    """Download RFI as PDF."""
    from fastapi.responses import Response
    from app.utils.rfi_export import generate_rfi_pdf

    assessment = require_review_approval(assessment_id, db)

    rfi = db.query(RFIDocument).filter(RFIDocument.assessment_id == assessment_id).first()
    if not rfi:
        raise HTTPException(404, "RFI not generated yet")

    evidence_items = json.loads(rfi.evidence_items)
    pdf_bytes = generate_rfi_pdf(
        title=rfi.title,
        company_name=assessment.company_name,
        introduction=rfi.introduction,
        evidence_items=evidence_items,
        response_instructions=rfi.response_instructions,
        generated_at=rfi.generated_at,
        framework_label=", ".join(_selected_framework_names(assessment)),
    )

    filename = f"RFI-{assessment.company_name.replace(' ', '-')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/assessments/{assessment_id}/rfi/docx")
def download_rfi_docx(assessment_id: str, db: Session = Depends(get_db)):
    """Download RFI as DOCX."""
    from fastapi.responses import Response
    from app.utils.rfi_export import generate_rfi_docx

    assessment = require_review_approval(assessment_id, db)

    rfi = db.query(RFIDocument).filter(RFIDocument.assessment_id == assessment_id).first()
    if not rfi:
        raise HTTPException(404, "RFI not generated yet")

    evidence_items = json.loads(rfi.evidence_items)
    docx_bytes = generate_rfi_docx(
        title=rfi.title,
        company_name=assessment.company_name,
        introduction=rfi.introduction,
        evidence_items=evidence_items,
        response_instructions=rfi.response_instructions,
        generated_at=rfi.generated_at,
    )

    filename = f"RFI-{assessment.company_name.replace(' ', '-')}.docx"
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# --- Desk Review (web endpoints) ---


@router.get("/assessments/{assessment_id}/desk-review-status", response_class=HTMLResponse)
def desk_review_status_web(
    request: Request,
    assessment_id: str,
    db: Session = Depends(get_db),
):
    """Return desk review status/findings as HTML partial."""
    from app.models.desk_review import DeskReviewFinding, DeskReviewSummary

    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404)

    summary = (
        db.query(DeskReviewSummary)
        .filter(DeskReviewSummary.assessment_id == assessment_id)
        .first()
    )

    if not summary or summary.status == "not_started":
        return templates.TemplateResponse(
            "partials/desk_review_ready.html",
            {"request": request, "assessment_id": assessment_id},
        )

    if summary.status == "analyzing":
        return templates.TemplateResponse(
            "partials/desk_review_running.html",
            {"request": request, "assessment_id": assessment_id},
        )

    if summary.status == "error":
        return templates.TemplateResponse(
            "partials/desk_review_error.html",
            {"request": request, "assessment_id": assessment_id, "error": summary.error_message},
        )

    # Completed — load findings
    findings = (
        db.query(DeskReviewFinding)
        .filter(DeskReviewFinding.assessment_id == assessment_id)
        .all()
    )
    evidence = [f for f in findings if f.finding_type == "evidence"]
    absences = [f for f in findings if f.finding_type == "absence"]
    signals = [f for f in findings if f.finding_type == "signal"]

    coverage = json.loads(summary.coverage_summary) if summary.coverage_summary else {}
    catalog = json.loads(summary.document_catalog) if summary.document_catalog else []

    return templates.TemplateResponse(
        "partials/desk_review_findings.html",
        {
            "request": request,
            "assessment_id": assessment_id,
            "evidence": evidence,
            "absences": absences,
            "signals": signals,
            "coverage": coverage,
            "catalog": catalog,
            "total_findings": len(findings),
        },
    )


@router.post("/assessments/{assessment_id}/run-desk-review", response_class=HTMLResponse)
def run_desk_review_web(
    request: Request,
    assessment_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Trigger desk review — set analyzing state immediately, run Claude in background."""
    from datetime import datetime, timezone

    from app.database import SessionLocal
    from app.models.desk_review import DeskReviewFinding, DeskReviewSummary
    from app.services.desk_review import run_desk_review

    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404)

    # Commit "analyzing" status synchronously so the polling partial never reverts to "ready"
    summary = (
        db.query(DeskReviewSummary)
        .filter(DeskReviewSummary.assessment_id == assessment_id)
        .first()
    )
    if summary:
        old_findings = db.query(DeskReviewFinding).filter(
            DeskReviewFinding.assessment_id == assessment_id
        ).all()
        if old_findings:
            snapshot = {
                "preserved_at": datetime.now(timezone.utc).isoformat(),
                "label": "desk_review_rerun",
                "findings": [
                    {c.name: getattr(f, c.name) for c in f.__table__.columns}
                    for f in old_findings
                ],
            }
            history = []
            if summary.legacy_history:
                try:
                    history = json.loads(summary.legacy_history)
                    if not isinstance(history, list):
                        history = [history]
                except json.JSONDecodeError:
                    history = []
            history.append(snapshot)
            summary.legacy_history = json.dumps(history, default=str)

        db.query(DeskReviewFinding).filter(
            DeskReviewFinding.assessment_id == assessment_id
        ).delete()
        summary.status = "analyzing"
        summary.error_message = None
        summary.started_at = datetime.now(timezone.utc)
        summary.completed_at = None
    else:
        summary = DeskReviewSummary(
            assessment_id=assessment_id,
            status="analyzing",
            started_at=datetime.now(timezone.utc),
        )
        db.add(summary)
    assessment.desk_review_status = "analyzing"
    db.commit()

    # Run the Claude call in a background task with its own session
    def _bg_run():
        with SessionLocal() as bg_db:
            run_desk_review(assessment_id, bg_db)

    background_tasks.add_task(_bg_run)

    return templates.TemplateResponse(
        "partials/desk_review_running.html",
        {"request": request, "assessment_id": assessment_id},
    )
