import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dpdpa.framework import get_all_requirements
from app.models.assessment import Assessment, AssessmentDocument
from app.models.initiative import Initiative
from app.models.questionnaire import QuestionnaireResponse
from app.models.report import GapItem, GapReport
from app.services.claude_analyzer import run_gap_analysis
from app.services.scoring import compute_scores, generate_initiatives

router = APIRouter(prefix="/api/assessments/{assessment_id}", tags=["analysis"])

# Build a requirement title lookup once
_REQ_TITLES = {r["id"]: r["title"] for r in get_all_requirements()}
_REQ_CHAPTERS = {r["id"]: r["chapter"] for r in get_all_requirements()}


@router.post("/analyze")
def trigger_analysis(assessment_id: str, db: Session = Depends(get_db)):
    """Trigger DPDPA gap analysis using Claude."""
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404, "Assessment not found")

    # Gather questionnaire responses
    responses_db = (
        db.query(QuestionnaireResponse)
        .filter(QuestionnaireResponse.assessment_id == assessment_id)
        .all()
    )
    responses = [
        {
            "question_id": r.question_id,
            "answer": r.answer,
            "notes": r.notes,
            "na_reason": r.na_reason,
            "confidence": r.confidence,
        }
        for r in responses_db
    ]

    # Gather documents
    docs_db = (
        db.query(AssessmentDocument)
        .filter(AssessmentDocument.assessment_id == assessment_id)
        .all()
    )
    documents = [
        {
            "filename": d.filename,
            "category": d.document_category,
            "text": d.extracted_text or "",
        }
        for d in docs_db
    ]

    if not responses and not documents:
        raise HTTPException(
            400,
            "Submit questionnaire responses or upload documents before running analysis.",
        )

    # Update status
    assessment.status = "analyzing"
    db.commit()

    # Load context profile if available
    context_profile = None
    if assessment.context_profile:
        context_profile = json.loads(assessment.context_profile)

    # Load desk review findings if available
    desk_review_data = None
    from app.models.desk_review import DeskReviewFinding, DeskReviewSummary
    dr_summary = (
        db.query(DeskReviewSummary)
        .filter(DeskReviewSummary.assessment_id == assessment_id, DeskReviewSummary.status == "completed")
        .first()
    )
    if dr_summary:
        dr_findings = (
            db.query(DeskReviewFinding)
            .filter(DeskReviewFinding.assessment_id == assessment_id)
            .all()
        )
        desk_review_data = {
            "coverage_summary": json.loads(dr_summary.coverage_summary) if dr_summary.coverage_summary else {},
            "findings": [
                {"type": f.finding_type, "requirement_id": f.requirement_id, "content": f.content}
                for f in dr_findings
            ],
            "signal_flags": [
                {"content": f.content, "severity": f.severity, "requirement_id": f.requirement_id}
                for f in dr_findings if f.finding_type == "signal"
            ],
            "absence_findings": [
                {"content": f.content, "requirement_id": f.requirement_id}
                for f in dr_findings if f.finding_type == "absence"
            ],
        }

    # Run Claude analysis
    try:
        result = run_gap_analysis(
            company_name=assessment.company_name,
            industry=assessment.industry,
            company_size=assessment.company_size,
            description=assessment.description,
            responses=responses,
            documents=documents,
            context_profile=context_profile,
            desk_review_data=desk_review_data,
        )
    except Exception as e:
        assessment.status = "error"
        db.commit()
        raise HTTPException(500, f"Analysis failed: {str(e)}")

    parsed = result["parsed"]
    raw = result["raw"]

    # Compute scores
    scores = compute_scores(parsed["assessments"])

    # Delete any existing report + initiatives for this assessment
    existing = (
        db.query(GapReport)
        .filter(GapReport.assessment_id == assessment_id)
        .first()
    )
    if existing:
        db.query(GapItem).filter(GapItem.report_id == existing.id).delete()
        db.query(Initiative).filter(Initiative.report_id == existing.id).delete()
        db.delete(existing)

    # Create report
    report = GapReport(
        assessment_id=assessment_id,
        overall_score=scores["overall_score"],
        chapter_scores=json.dumps(scores["chapter_scores"]),
        executive_summary=parsed.get("executive_summary", ""),
        raw_ai_response=raw,
    )
    db.add(report)
    db.flush()

    # Build evidence confidence lookup from desk review + documents
    _dr_evidence_reqs = set()
    _dr_coverage = {}
    if desk_review_data:
        _dr_coverage = desk_review_data.get("coverage_summary", {})
        for f in desk_review_data.get("findings", []):
            if f.get("type") == "evidence" and f.get("requirement_id"):
                _dr_evidence_reqs.add(f["requirement_id"])

    has_documents = bool(documents)
    _response_ids = {r["question_id"] for r in responses}

    def _compute_evidence_confidence(req_id: str) -> str:
        """strong = document evidence, moderate = self-reported + partial docs, weak = self-reported only."""
        has_dr_evidence = req_id in _dr_evidence_reqs or _dr_coverage.get(req_id) == "adequate"
        has_response = req_id in _response_ids
        if has_dr_evidence and has_response:
            return "strong"
        if has_dr_evidence or (has_response and has_documents):
            return "moderate"
        if has_response:
            return "weak"
        return "weak"

    # Create gap items
    for a in parsed["assessments"]:
        req_id = a["requirement_id"]
        item = GapItem(
            report_id=report.id,
            requirement_id=req_id,
            chapter=_REQ_CHAPTERS.get(req_id, "unknown"),
            requirement_title=_REQ_TITLES.get(req_id, req_id),
            compliance_status=a["compliance_status"],
            current_state=a.get("current_state", ""),
            gap_description=a.get("gap_description", ""),
            risk_level=a.get("risk_level", "medium"),
            remediation_action=a.get("remediation_action", ""),
            remediation_priority=a.get("remediation_priority", 3),
            remediation_effort=a.get("remediation_effort", "medium"),
            timeline_weeks=a.get("timeline_weeks", 8),
            maturity_level=a.get("maturity_level"),
            root_cause_category=a.get("root_cause_category"),
            evidence_quote=a.get("evidence_quote"),
            evidence_confidence=_compute_evidence_confidence(req_id),
        )
        db.add(item)

    # Generate and save initiatives
    initiatives_data = generate_initiatives(parsed["assessments"])
    for init_data in initiatives_data:
        initiative = Initiative(
            report_id=report.id,
            initiative_id=init_data["initiative_id"],
            title=init_data["title"],
            root_cause=init_data["root_cause"],
            root_cause_category=init_data["root_cause_category"],
            requirements_addressed=json.dumps(init_data["requirements_addressed"]),
            combined_effort=init_data["combined_effort"],
            combined_timeline_weeks=init_data["combined_timeline_weeks"],
            priority=init_data["priority"],
            budget_estimate_band=init_data.get("budget_estimate_band"),
            suggested_approach=init_data["suggested_approach"],
        )
        db.add(initiative)

    assessment.status = "completed"
    db.commit()
    db.refresh(report)

    return {
        "report_id": report.id,
        "status": "completed",
        "overall_score": report.overall_score,
        "initiatives_generated": len(initiatives_data),
        "message": "Gap analysis completed successfully",
    }
