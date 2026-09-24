"""Read-only report content (P3-3): approved Findings with citations and evidence chain for the gap report, and per-assessment sections for the integrated engagement report. Never writes."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.frameworks.registry import FrameworkRegistry
from app.models.assessment import Assessment
from app.models.assessment_pack import AssessmentPack
from app.models.client import Client
from app.models.engagement import Engagement
from app.models.evidence import EvidenceVersion
from app.models.report import GapReport
from app.services import findings as finding_service
from app.services import report_snapshots
from app.services.scoring import failed_framework_ids, report_framework_scores
from app.services.workpaper import anchor_for

SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}
DECISION_LABELS = {"approved": "Approved", "edited": "Edited and approved"}
ACTION_STATUS_LABELS = {
    "open": "Open",
    "in_progress": "In progress",
    "closed": "Closed, awaiting verification",
    "verified": "Closed and verified",
}
FINDING_STATUS_LABELS = {
    "open": "Open",
    "in_progress": "In progress",
    "resolved": "Resolved",
    "accepted_risk": "Accepted risk",
}
NOT_RELEASED = "Not approved for release"
NO_REPORT = "No analysis report yet"
ANALYSIS_INCOMPLETE = "Analysis failed for at least one framework"
PERIOD_NOT_RECORDED = "not recorded"


@dataclass(frozen=True)
class ReportCitation:
    excerpt: str
    location_ref: str | None
    filename: str | None
    version_number: int | None
    sha256: str | None
    resolved: bool
    is_current: bool


@dataclass(frozen=True)
class ReportAction:
    title: str
    owner: str | None
    target_date: date | None
    status: str
    status_label: str


@dataclass(frozen=True)
class ReportFinding:
    finding_id: str
    title: str
    description: str
    severity: str
    priority: int
    status_label: str
    framework_id: str
    framework_name: str
    requirement_id: str
    requirement_title: str
    outcome_label: str
    decision_label: str
    decided_by: str | None
    decided_at: datetime | None
    decision_version: int
    workpaper_ref: str
    citations_captured: bool
    citations: list[ReportCitation]
    actions: list[ReportAction]


@dataclass(frozen=True)
class AssessmentFindings:
    findings: list[ReportFinding]
    omitted_count: int


@dataclass(frozen=True)
class ScoreLine:
    framework_name: str
    score: float
    rating: str


@dataclass(frozen=True)
class IntegratedSection:
    assessment_id: str
    label: str
    created_at: datetime
    analysed_at: datetime | None
    frameworks: list[tuple[str, str]]
    scope_label: str
    scores: list[ScoreLine]
    findings: AssessmentFindings


@dataclass(frozen=True)
class ExcludedAssessment:
    assessment_id: str
    label: str
    reason: str


@dataclass(frozen=True)
class IntegratedReport:
    engagement_name: str
    client_name: str
    sections: list[IntegratedSection]
    excluded: list[ExcludedAssessment]
    source: dict


def _framework_name(framework_id: str) -> str:
    framework = FrameworkRegistry.get_or_none(framework_id)
    return framework.name if framework else framework_id.upper()


def _scope_label(assessment: Assessment) -> str:
    try:
        applicable = json.loads(assessment.applicable_requirements or "null")
    except (json.JSONDecodeError, TypeError):
        applicable = None
    if isinstance(applicable, list) and applicable:
        return f"{len(applicable)} applicable requirements in scope"
    return "No scope restriction recorded"


def _assessment_label(assessment: Assessment) -> str:
    return f"{assessment.description or assessment.company_name} ({assessment.created_at:%d %b %Y})"


def assessment_findings(db: Session, assessment: Assessment) -> AssessmentFindings:
    page = finding_service.findings_page(db, assessment.id)
    included_views = [
        view
        for view in page.findings
        if view.source_approved
        and view.card is not None
        and not view.card.legacy_bulk_approval
    ]
    omitted_count = len(page.findings) - len(included_views)

    version_ids = {
        citation.get("evidence_version_id")
        for view in included_views
        for citation in view.card.citations
        if citation.get("evidence_version_id")
    }
    hashes = {}
    if version_ids:
        hashes = {
            row.id: row.file_hash_sha256
            for row in db.execute(
                select(EvidenceVersion.id, EvidenceVersion.file_hash_sha256).where(
                    EvidenceVersion.id.in_(version_ids)
                )
            ).all()
        }

    framework_order = list(assessment.frameworks)
    framework_order.extend(
        sorted(
            {
                view.card.conclusion.framework_id
                for view in included_views
                if view.card.conclusion.framework_id not in framework_order
            }
        )
    )
    framework_rank = {
        framework_id: index for index, framework_id in enumerate(framework_order)
    }
    indexed_views = list(enumerate(included_views))
    indexed_views.sort(
        key=lambda pair: (
            framework_rank.get(pair[1].card.conclusion.framework_id, len(framework_rank)),
            SEVERITY_RANK.get(pair[1].finding.severity, 4),
            pair[1].finding.priority,
            pair[0],
        )
    )

    findings = []
    for _original_index, view in indexed_views:
        card = view.card
        conclusion = card.conclusion
        citations = [
            ReportCitation(
                excerpt=citation.get("excerpt") or "",
                location_ref=citation.get("location_ref"),
                filename=citation.get("filename") if citation.get("resolved") else None,
                version_number=(
                    citation.get("version_number") if citation.get("resolved") else None
                ),
                sha256=(
                    hashes.get(citation.get("evidence_version_id"))
                    if citation.get("resolved")
                    else None
                ),
                resolved=bool(citation.get("resolved")),
                is_current=bool(citation.get("is_current")),
            )
            for citation in card.citations
        ]
        last_decision = card.last_decision or {}
        actions = [
            ReportAction(
                title=action_view.action.title,
                owner=action_view.action.owner,
                target_date=(
                    action_view.action.target_date.date()
                    if action_view.action.target_date
                    else None
                ),
                status=action_view.action.status,
                status_label=ACTION_STATUS_LABELS.get(
                    action_view.action.status, action_view.action.status
                ),
            )
            for action_view in view.actions
        ]
        findings.append(
            ReportFinding(
                finding_id=view.finding.id,
                title=view.finding.title,
                description=view.finding.description,
                severity=view.finding.severity,
                priority=view.finding.priority,
                status_label=FINDING_STATUS_LABELS.get(
                    view.finding.status, view.finding.status
                ),
                framework_id=conclusion.framework_id,
                framework_name=_framework_name(conclusion.framework_id),
                requirement_id=conclusion.requirement_id,
                requirement_title=card.requirement_title,
                outcome_label=conclusion.outcome.replace("_", " ").title(),
                decision_label=DECISION_LABELS[card.state],
                decided_by=last_decision.get("actor_display"),
                decided_at=last_decision.get("created_at"),
                decision_version=conclusion.version,
                workpaper_ref=anchor_for(
                    conclusion.framework_id, conclusion.requirement_id
                ),
                citations_captured=card.citations_captured,
                citations=citations,
                actions=actions,
            )
        )
    return AssessmentFindings(findings=findings, omitted_count=omitted_count)


def integrated_report(db: Session, engagement: Engagement) -> IntegratedReport:
    assessments = (
        db.query(Assessment)
        .filter(
            Assessment.engagement_id == engagement.id,
            Assessment.status != "archived",
        )
        .order_by(Assessment.created_at, Assessment.id)
        .all()
    )
    client = db.get(Client, engagement.client_id)
    client_name = client.name if client else ""
    sections: list[IntegratedSection] = []
    excluded: list[ExcludedAssessment] = []

    for assessment in assessments:
        label = _assessment_label(assessment)
        if assessment.review_status != "approved":
            excluded.append(
                ExcludedAssessment(assessment.id, label, NOT_RELEASED)
            )
            continue
        report = (
            db.query(GapReport)
            .filter(GapReport.assessment_id == assessment.id)
            .first()
        )
        if report is None:
            excluded.append(ExcludedAssessment(assessment.id, label, NO_REPORT))
            continue
        if failed_framework_ids(
            report_framework_scores(report, assessment),
            assessment.frameworks,
        ):
            excluded.append(ExcludedAssessment(assessment.id, label, ANALYSIS_INCOMPLETE))
            continue

        packs = {
            pack.framework_id: pack.pack_version
            for pack in db.query(AssessmentPack)
            .filter(AssessmentPack.assessment_id == assessment.id)
            .all()
        }
        frameworks = [
            (_framework_name(framework_id), packs.get(framework_id, "not recorded"))
            for framework_id in assessment.frameworks
        ]
        framework_scores = report_framework_scores(report, assessment)
        scores = []
        for framework_id in assessment.frameworks:
            score_data = framework_scores.get(framework_id)
            if not score_data or score_data.get("overall_score") is None:
                continue
            scores.append(
                ScoreLine(
                    framework_name=_framework_name(framework_id),
                    score=score_data["overall_score"],
                    rating=score_data.get("overall_rating", "N/A"),
                )
            )
        sections.append(
            IntegratedSection(
                assessment_id=assessment.id,
                label=label,
                created_at=assessment.created_at,
                analysed_at=report.generated_at,
                frameworks=frameworks,
                scope_label=_scope_label(assessment),
                scores=scores,
                findings=assessment_findings(db, assessment),
            )
        )

    included_ids = {section.assessment_id for section in sections}
    source_assessments = []
    finding_ids = []
    for section in sorted(sections, key=lambda item: item.assessment_id):
        assessment = db.get(Assessment, section.assessment_id)
        source_assessments.append(
            {
                "assessment_id": assessment.id,
                **report_snapshots.source_manifest(db, assessment),
            }
        )
        finding_ids.extend(
            finding.finding_id for finding in section.findings.findings
        )
    source = {
        "assessments": source_assessments,
        "excluded_assessment_ids": sorted(
            assessment.id for assessment in assessments if assessment.id not in included_ids
        ),
        "finding_ids": sorted(finding_ids),
    }
    return IntegratedReport(
        engagement_name=engagement.name,
        client_name=client_name,
        sections=sections,
        excluded=excluded,
        source=source,
    )
