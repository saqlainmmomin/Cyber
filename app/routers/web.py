"""Web portal routes — HTML-serving endpoints for the assessment UI."""

import json
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.dpdpa.context_questions import CONTEXT_BLOCKS
from app.dpdpa.questionnaire import build_questionnaire
from app.models.assessment import Assessment, AssessmentDocument
from app.models.questionnaire import QuestionnaireResponse
from app.services.followup_engine import generate_followups
from app.services.question_engine import build_adaptive_questionnaire
from app.models.report import GapItem, GapReport
from app.schemas.assessment import DocumentCategory
from app.services.document_processor import detect_file_type, extract_text, save_upload

router = APIRouter(tags=["web"])

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
    tab: str = "documents",
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
            "context_error": context_error,
            "doc_categories": [c.value for c in DocumentCategory],
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
    status_counts = {}
    for item in gap_items:
        status_counts[item.compliance_status] = status_counts.get(item.compliance_status, 0) + 1

    return templates.TemplateResponse(
        "partials/report_summary.html",
        {
            "request": request,
            "assessment_id": assessment_id,
            "report": report,
            "gap_items": gap_items,
            "chapter_scores": chapter_scores,
            "status_counts": status_counts,
        },
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
