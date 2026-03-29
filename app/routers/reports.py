import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.dpdpa.framework import ROOT_CAUSE_CLUSTERS, get_requirement_count
from app.models.assessment import Assessment
from app.models.initiative import Initiative
from app.models.report import GapItem, GapReport
from app.schemas.initiative import InitiativeOut
from app.schemas.report import ChapterScore, GapItemOut, ReportOut, ReportSummary
from app.services.scoring import get_rating
from app.utils.pdf_export import generate_pdf

router = APIRouter(prefix="/api/assessments/{assessment_id}/report", tags=["reports"])


def _get_report(assessment_id: str, db: Session) -> GapReport:
    report = (
        db.query(GapReport)
        .filter(GapReport.assessment_id == assessment_id)
        .first()
    )
    if not report:
        raise HTTPException(404, "No report found. Run analysis first.")
    return report


def _get_gap_items(report_id: str, db: Session) -> list[GapItem]:
    return db.query(GapItem).filter(GapItem.report_id == report_id).all()


def _get_initiatives(report_id: str, db: Session) -> list[Initiative]:
    return (
        db.query(Initiative)
        .filter(Initiative.report_id == report_id)
        .order_by(Initiative.priority)
        .all()
    )


def _item_to_schema(item: GapItem) -> GapItemOut:
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
    )


def _initiative_to_schema(init: Initiative) -> InitiativeOut:
    return InitiativeOut(
        initiative_id=init.initiative_id,
        title=init.title,
        root_cause=init.root_cause,
        root_cause_category=init.root_cause_category,
        requirements_addressed=json.loads(init.requirements_addressed),
        combined_effort=init.combined_effort,
        combined_timeline_weeks=init.combined_timeline_weeks,
        priority=init.priority,
        budget_estimate_band=init.budget_estimate_band,
        suggested_approach=init.suggested_approach,
    )


@router.get("", response_model=ReportOut)
def get_report(assessment_id: str, db: Session = Depends(get_db)):
    report = _get_report(assessment_id, db)
    items = _get_gap_items(report.id, db)
    initiatives = _get_initiatives(report.id, db)

    chapter_scores_raw = json.loads(report.chapter_scores)
    chapter_scores = {k: ChapterScore(**v) for k, v in chapter_scores_raw.items()}

    item_schemas = [_item_to_schema(i) for i in items]

    # Build remediation roadmap grouped by priority
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
        id=report.id,
        assessment_id=report.assessment_id,
        overall_score=report.overall_score,
        overall_rating=get_rating(report.overall_score),
        chapter_scores=chapter_scores,
        executive_summary=report.executive_summary,
        gap_items=item_schemas,
        remediation_roadmap=roadmap,
        initiatives=[_initiative_to_schema(i) for i in initiatives],
        generated_at=report.generated_at,
    )


@router.get("/summary", response_model=ReportSummary)
def get_report_summary(assessment_id: str, db: Session = Depends(get_db)):
    report = _get_report(assessment_id, db)
    items = _get_gap_items(report.id, db)

    chapter_scores_raw = json.loads(report.chapter_scores)
    chapter_scores = {k: ChapterScore(**v) for k, v in chapter_scores_raw.items()}

    counts = {"compliant": 0, "partially_compliant": 0, "non_compliant": 0, "not_assessed": 0}
    critical_gaps = 0
    high_gaps = 0

    for item in items:
        counts[item.compliance_status] = counts.get(item.compliance_status, 0) + 1
        if item.compliance_status in ("non_compliant", "partially_compliant"):
            if item.risk_level == "critical":
                critical_gaps += 1
            elif item.risk_level == "high":
                high_gaps += 1

    return ReportSummary(
        overall_score=report.overall_score,
        overall_rating=get_rating(report.overall_score),
        total_requirements=get_requirement_count(),
        compliant=counts["compliant"],
        partially_compliant=counts["partially_compliant"],
        non_compliant=counts["non_compliant"],
        not_assessed=counts["not_assessed"],
        critical_gaps=critical_gaps,
        high_gaps=high_gaps,
        chapter_scores=chapter_scores,
    )


@router.get("/pdf")
def download_pdf(assessment_id: str, db: Session = Depends(get_db)):
    report = _get_report(assessment_id, db)
    items = _get_gap_items(report.id, db)
    initiatives = _get_initiatives(report.id, db)

    assessment = db.get(Assessment, assessment_id)
    company_name = assessment.company_name if assessment else "Unknown"

    pdf_bytes = generate_pdf(report, items, company_name, initiatives=initiatives)

    filename = f"DPDPA_Assessment_{company_name.replace(' ', '_')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
