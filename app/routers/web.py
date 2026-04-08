"""Web portal routes — HTML-serving endpoints for the assessment UI."""

import json
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.dpdpa.context_questions import CONTEXT_BLOCKS
from app.dpdpa.questionnaire import ANSWER_OPTIONS, build_questionnaire
from app.dpdpa.scope_questions import SCOPE_QUESTIONS
from app.models.assessment import Assessment, AssessmentDocument
from app.models.questionnaire import QuestionnaireResponse
from app.models.rfi import RFIDocument
from app.services.followup_engine import generate_followups
from app.services.question_engine import build_adaptive_questionnaire
from app.models.report import GapItem, GapReport
from app.schemas.assessment import DocumentCategory
from app.services.document_processor import detect_file_type, extract_text, save_upload

router = APIRouter(tags=["web"])
logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")


# --- Auth dependency ---




# --- Dashboard ---


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    assessments = db.query(Assessment).order_by(Assessment.created_at.desc()).all()
    return templates.TemplateResponse(
        "pages/dashboard.html",
        {"request": request, "assessments": assessments},
    )


# --- Assessment CRUD ---


@router.get("/assessments/new", response_class=HTMLResponse)
def new_assessment_page(request: Request):
    return templates.TemplateResponse("pages/new_assessment.html", {"request": request})


@router.post("/assessments/new")
def create_assessment(
    request: Request,

    company_name: str = Form(...),
    industry: str = Form(...),
    company_size: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db),
):
    assessment = Assessment(
        company_name=company_name,
        industry=industry,
        company_size=company_size,
        description=description or None,
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return RedirectResponse(f"/assessments/{assessment.id}", status_code=303)


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

    documents = (
        db.query(AssessmentDocument)
        .filter(AssessmentDocument.assessment_id == assessment_id)
        .order_by(AssessmentDocument.uploaded_at.desc())
        .all()
    )

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

    # Default tab: scope if not yet scoped, else documents
    if tab is None:
        tab = "scope" if not scope_done else "documents"

    # Build scope context for the scope tab
    scope_context: dict = {}
    if tab == "scope":
        if scope_done:
            from app.services.scope_profiler import compute_scope
            scope_data = json.loads(assessment.scope_answers)
            result = compute_scope(scope_data, assessment.industry or "", assessment.company_size or "")
            applicable_ids = result["applicable_requirements"]
            from app.dpdpa.framework import get_all_requirements
            total_count = len(get_all_requirements())
            scope_context = {
                "checklist": result["evidence_checklist"],
                "excluded": result["excluded_requirements"],
                "flags": result["flags"],
                "applicable_count": len(applicable_ids),
                "total_count": total_count,
            }
        else:
            existing_scope = {}
            scope_context = {
                "scope_questions": SCOPE_QUESTIONS,
                "existing": existing_scope,
            }

    return templates.TemplateResponse(
        "pages/assessment.html",
        {
            "request": request,
            "assessment": assessment,
            "documents": documents,
            "report": report,
            "gap_items": gap_items,
            "tab": tab,
            "response_count": response_count,
            "context_done": context_done,
            "scope_done": scope_done,
            "context_error": context_error,
            "doc_categories": [c.value for c in DocumentCategory],
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
    db.delete(assessment)
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
    from app.services.scope_profiler import compute_scope
    from app.dpdpa.scope_questions import SCOPE_QUESTIONS

    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404)

    form = await request.form()
    scope_answers = {}
    for q in SCOPE_QUESTIONS:
        value = form.get(q["id"])
        if value:
            scope_answers[q["id"]] = value

    assessment.scope_answers = json.dumps(scope_answers)

    # Compute applicable requirements and cache them
    result = compute_scope(scope_answers, assessment.industry or "", assessment.company_size or "")
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
    from app.services.scope_profiler import compute_scope
    from app.utils.evidence_checklist_export import generate_evidence_checklist_pdf

    assessment = db.get(Assessment, assessment_id)
    if not assessment or not assessment.scope_answers:
        raise HTTPException(404, "Scope not yet defined")

    scope_answers = json.loads(assessment.scope_answers)
    result = compute_scope(scope_answers, assessment.industry or "", assessment.company_size or "")

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
    from app.services.scope_profiler import compute_scope
    from app.utils.evidence_checklist_export import generate_evidence_checklist_docx

    assessment = db.get(Assessment, assessment_id)
    if not assessment or not assessment.scope_answers:
        raise HTTPException(404, "Scope not yet defined")

    scope_answers = json.loads(assessment.scope_answers)
    result = compute_scope(scope_answers, assessment.industry or "", assessment.company_size or "")

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

    file_type = detect_file_type(file.filename or "")
    if not file_type:
        return templates.TemplateResponse(
            "partials/upload_status.html",
            {"request": request, "error": "Unsupported file type. Upload PDF, DOCX, PNG, JPG, JPEG, or WEBP."},
        )

    content = await file.read()
    file_path = save_upload(assessment_id, file.filename or "document", content)
    extracted_text = extract_text(file_path, file_type)

    if not extracted_text.strip():
        return templates.TemplateResponse(
            "partials/upload_status.html",
            {"request": request, "error": "Could not extract text from this document."},
        )

    doc = AssessmentDocument(
        assessment_id=assessment_id,
        filename=file.filename or "document",
        file_path=file_path,
        file_type=file_type,
        document_category=category,
        extracted_text=extracted_text,
    )
    db.add(doc)
    if assessment.status == "created":
        assessment.status = "documents_uploaded"
    db.commit()
    db.refresh(doc)

    # Return updated document list
    documents = (
        db.query(AssessmentDocument)
        .filter(AssessmentDocument.assessment_id == assessment_id)
        .order_by(AssessmentDocument.uploaded_at.desc())
        .all()
    )
    return templates.TemplateResponse(
        "partials/document_list.html",
        {"request": request, "documents": documents, "assessment_id": assessment_id},
    )


@router.delete("/assessments/{assessment_id}/documents/{document_id}", response_class=HTMLResponse)
def delete_document_web(
    request: Request,
    assessment_id: str,
    document_id: str,

    db: Session = Depends(get_db),
):
    doc = db.get(AssessmentDocument, document_id)
    if not doc or doc.assessment_id != assessment_id:
        raise HTTPException(404)
    db.delete(doc)
    db.commit()

    documents = (
        db.query(AssessmentDocument)
        .filter(AssessmentDocument.assessment_id == assessment_id)
        .order_by(AssessmentDocument.uploaded_at.desc())
        .all()
    )
    return templates.TemplateResponse(
        "partials/document_list.html",
        {"request": request, "documents": documents, "assessment_id": assessment_id},
    )


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

    return templates.TemplateResponse(
        "partials/section_saved.html",
        {"request": request, "section_id": section_id, "assessment_id": assessment_id},
    )


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

    return templates.TemplateResponse(
        "partials/analysis_running.html",
        {"request": request, "assessment_id": assessment_id},
    )


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
            {"request": request, "assessment_id": assessment_id, "report": report},
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


@router.get("/assessments/{assessment_id}/report-summary", response_class=HTMLResponse)
def report_summary(
    request: Request,
    assessment_id: str,

    db: Session = Depends(get_db),
):
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404)

    report = db.query(GapReport).filter(GapReport.assessment_id == assessment_id).first()
    if not report:
        return templates.TemplateResponse(
            "partials/no_report.html",
            {"request": request, "assessment_id": assessment_id},
        )

    gap_items = db.query(GapItem).filter(GapItem.report_id == report.id).all()
    chapter_scores = json.loads(report.chapter_scores) if report.chapter_scores else {}

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

    return templates.TemplateResponse(
        "partials/rfi_generated.html",
        {"request": request, "assessment_id": assessment_id, "rfi": rfi},
    )


@router.get("/assessments/{assessment_id}/rfi/pdf")
def download_rfi_pdf(assessment_id: str, db: Session = Depends(get_db)):
    """Download RFI as PDF."""
    from fastapi.responses import Response
    from app.utils.rfi_export import generate_rfi_pdf

    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404)

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

    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404)

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
    db: Session = Depends(get_db),
):
    """Trigger desk review and show running indicator."""
    from app.services.desk_review import run_desk_review

    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404)

    # Run synchronously — desk review typically takes 15-30s
    run_desk_review(assessment_id, db)

    # Return the findings (or error) — redirect to status which will show results
    return templates.TemplateResponse(
        "partials/desk_review_running.html",
        {"request": request, "assessment_id": assessment_id},
    )
