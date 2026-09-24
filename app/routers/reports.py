import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.frameworks.registry import FrameworkRegistry
from app.models.assessment import Assessment
from app.models.questionnaire import QuestionnaireResponse
from app.schemas.report import ChapterScore, GapItemOut, ReportOut, ReportSummary
from app.services import approved_report, report_content
from app.services.scoring import compute_delta
from app.utils.pdf_export import generate_pdf
from app.utils.review_gate import require_review_approval

router = APIRouter(prefix="/api/assessments/{assessment_id}/report", tags=["reports"])
comparison_router = APIRouter(prefix="/api/assessments", tags=["reports"])


def _item_to_schema(item: approved_report.ApprovedRow) -> GapItemOut:
    return GapItemOut(
        requirement_id=item.requirement_id,
        chapter=item.chapter,
        requirement_title=item.requirement_title,
        compliance_status=item.compliance_status,
        current_state=item.current_state,
        gap_description=item.gap_description,
        risk_level=item.risk_level,
        remediation_action=item.remediation_action,
        remediation_priority=item.remediation_priority,
        remediation_effort=item.remediation_effort,
        timeline_weeks=item.timeline_weeks,
        maturity_level=item.maturity_level,
        root_cause_category=item.root_cause_category,
        evidence_quote=item.evidence_quote,
        framework_id=item.framework_id,
        conclusion_id=item.conclusion_id,
        conclusion_version=item.conclusion_version,
    )


def _chapter_scores(raw: dict[str, dict]) -> dict[str, ChapterScore]:
    return {key: ChapterScore(**value) for key, value in raw.items()}


def _assessment_and_view(
    assessment_id: str,
    db: Session,
) -> tuple[Assessment, approved_report.ApprovedReport]:
    assessment = require_review_approval(assessment_id, db)
    return assessment, approved_report.build_approved_report(db, assessment)


@router.get("", response_model=ReportOut)
def get_report(assessment_id: str, db: Session = Depends(get_db)):
    assessment, approved = _assessment_and_view(assessment_id, db)
    if approved.report_id is None:
        raise HTTPException(404, "No report found. Run analysis first.")

    item_schemas = [_item_to_schema(item) for item in approved.rows]
    raw_scores = approved.chapter_scores
    chapter_score_models = _chapter_scores(raw_scores)
    roadmap: dict[str, list[GapItemOut]] = {
        "immediate": [],
        "short_term": [],
        "medium_term": [],
        "long_term": [],
    }
    priority_map = {1: "immediate", 2: "short_term", 3: "medium_term", 4: "long_term"}
    for item in item_schemas:
        if item.compliance_status != "compliant":
            bucket = priority_map.get(item.remediation_priority, "long_term")
            roadmap[bucket].append(item)

    return ReportOut(
        id=approved.report_id,
        assessment_id=assessment.id,
        framework_scores=approved.framework_scores,
        chapter_scores=chapter_score_models,
        executive_summary=approved.summary_text,
        gap_items=item_schemas,
        remediation_roadmap=roadmap,
        initiatives=[],
        generated_at=approved.generated_at,
    )


@router.get("/summary", response_model=ReportSummary)
def get_report_summary(assessment_id: str, db: Session = Depends(get_db)):
    assessment, approved = _assessment_and_view(assessment_id, db)
    raw_scores = approved.chapter_scores
    chapter_score_models = _chapter_scores(raw_scores)
    counts = {
        "compliant": 0,
        "partially_compliant": 0,
        "non_compliant": 0,
        "insufficient_evidence": 0,
        "not_applicable": 0,
    }
    critical_gaps = 0
    high_gaps = 0
    for item in approved.rows:
        counts[item.compliance_status] = counts.get(item.compliance_status, 0) + 1
        if item.compliance_status in ("non_compliant", "partially_compliant"):
            if item.risk_level == "critical":
                critical_gaps += 1
            elif item.risk_level == "high":
                high_gaps += 1

    requirement_counts = {
        framework_id: FrameworkRegistry.get(framework_id).control_count()
        for framework_id in assessment.frameworks
    }
    return ReportSummary(
        framework_scores=approved.framework_scores,
        requirement_counts=requirement_counts,
        total_requirements=sum(requirement_counts.values()),
        compliant=counts["compliant"],
        partially_compliant=counts["partially_compliant"],
        non_compliant=counts["non_compliant"],
        not_assessed=counts["insufficient_evidence"],
        insufficient_evidence=counts["insufficient_evidence"],
        not_applicable=counts["not_applicable"],
        critical_gaps=critical_gaps,
        high_gaps=high_gaps,
        chapter_scores=chapter_score_models,
    )


@router.get("/full")
def get_full_report(assessment_id: str, db: Session = Depends(get_db)):
    assessment, approved = _assessment_and_view(assessment_id, db)
    frameworks_info = {}
    for framework_id in assessment.frameworks:
        framework = FrameworkRegistry.get_or_none(framework_id)
        frameworks_info[framework_id] = {
            "name": framework.name if framework else framework_id.upper(),
            "version": framework.version if framework else "",
            "scores": approved.framework_scores[framework_id],
        }

    items_by_framework: dict[str, list[dict]] = {}
    for item in approved.rows:
        items_by_framework.setdefault(item.framework_id, []).append({
            "requirement_id": item.requirement_id,
            "requirement_title": item.requirement_title,
            "compliance_status": item.compliance_status,
            "current_state": item.current_state,
            "gap_description": item.gap_description,
            "risk_level": item.risk_level,
            "remediation_action": item.remediation_action,
            "remediation_priority": item.remediation_priority,
            "remediation_effort": item.remediation_effort,
            "timeline_weeks": item.timeline_weeks,
            "maturity_level": item.maturity_level,
            "root_cause_category": item.root_cause_category,
            "evidence_quote": item.evidence_quote,
            "evidence_confidence": item.evidence_confidence,
            "control_reference": item.control_reference,
            "conclusion_id": item.conclusion_id,
            "conclusion_version": item.conclusion_version,
        })

    return JSONResponse({
        "id": approved.report_id,
        "assessment_id": assessment.id,
        "company_name": assessment.company_name,
        "executive_summary": approved.summary_text,
        "chapter_scores": approved.chapter_scores,
        "frameworks": frameworks_info,
        "gap_items_by_framework": items_by_framework,
        "initiatives": [],
        "generated_at": approved.generated_at.isoformat() if approved.generated_at else None,
    })


@router.get("/pdf")
def download_pdf(assessment_id: str, db: Session = Depends(get_db)):
    return _download_pdf_response(assessment_id, db)


def _download_pdf_response(
    assessment_id: str,
    db: Session,
    *,
    allow_failed_draft: bool = False,
):
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        raise HTTPException(404, "Assessment not found")

    approved = approved_report.build_approved_report(db, assessment)
    if not allow_failed_draft or not any(
        entry.get("status") == "failed" for entry in approved.framework_scores.values()
    ):
        require_review_approval(assessment_id, db)
        approved = approved_report.build_approved_report(db, assessment)
    if approved.report_id is None:
        raise HTTPException(404, "No report found. Run analysis first.")

    answer_source_map: dict[str, str] = {}
    responses = (
        db.query(QuestionnaireResponse)
        .filter(QuestionnaireResponse.assessment_id == assessment_id)
        .all()
    )
    for response in responses:
        answer_source_map[response.question_id] = response.answer_source or "human"

    report_findings = report_content.assessment_findings(db, assessment)
    pdf_bytes = generate_pdf(
        approved.render_report(),
        list(approved.rows),
        assessment.company_name or "Unknown",
        initiatives=None,
        answer_source_map=answer_source_map,
        selected_frameworks=assessment.frameworks,
        assessment=assessment,
        report_findings=report_findings,
    )
    fw_label = "_".join(framework_id.upper() for framework_id in assessment.frameworks[:3])
    filename = f"Compliance_Assessment_{fw_label}_{assessment.company_name.replace(' ', '_')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@comparison_router.get("/{assessment_id}/comparable")
def get_comparable_assessments(assessment_id: str, db: Session = Depends(get_db)):
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404, "Assessment not found")
    candidates = (
        db.query(Assessment)
        .filter(
            Assessment.company_name == assessment.company_name,
            Assessment.id != assessment_id,
            Assessment.status == "completed",
        )
        .order_by(Assessment.created_at.desc())
        .all()
    )
    return [
        {"id": other.id, "created_at": other.created_at.isoformat(), "status": other.status}
        for other in candidates
        if approved_report.is_released(db, other)
    ]


@comparison_router.get("/{assessment_id}/compare/{other_id}")
def compare_assessments(assessment_id: str, other_id: str, db: Session = Depends(get_db)):
    current, current_view = _assessment_and_view(assessment_id, db)
    previous, previous_view = _assessment_and_view(other_id, db)
    if current.company_name != previous.company_name:
        raise HTTPException(400, "Assessments must belong to the same company")
    if current.status != "completed" or previous.status != "completed":
        raise HTTPException(400, "Both assessments must be completed")
    result = compute_delta(list(current_view.rows), list(previous_view.rows))
    framework_deltas = []
    for framework_id in current.frameworks:
        current_score = current_view.framework_scores.get(framework_id, {})
        previous_score = previous_view.framework_scores.get(framework_id, {})
        current_value = (
            current_score.get("overall_score")
            if current_score.get("status") == "scored"
            else None
        )
        previous_value = (
            previous_score.get("overall_score")
            if previous_score.get("status") == "scored"
            else None
        )
        framework = FrameworkRegistry.get_or_none(framework_id)
        framework_deltas.append({
            "framework_id": framework_id,
            "name": framework.name if framework else framework_id.upper(),
            "current": current_value,
            "previous": previous_value,
            "delta": (
                round(current_value - previous_value, 1)
                if current_value is not None and previous_value is not None
                else None
            ),
        })
    return {**result, "framework_deltas": framework_deltas}
