"""Framework-scoped readers for persisted desk-review findings."""

import json

from app.frameworks.registry import FrameworkRegistry
from app.models.desk_review import DeskReviewFinding, DeskReviewSummary


LEGACY_FINDING_FRAMEWORK_ID = "dpdpa"
GROUNDED_CITATION_LOCATION_TYPE = "text_span"


def finding_has_grounded_citation(finding: DeskReviewFinding) -> bool:
    """True for an evidence row whose quote was located in an evidence version."""
    if finding.finding_type != "evidence" or not (finding.source_quote or "").strip():
        return False
    try:
        citations = json.loads(finding.citations_json or "[]")
    except (json.JSONDecodeError, TypeError):
        return False
    return isinstance(citations, list) and any(
        isinstance(citation, dict)
        and citation.get("location_type") == GROUNDED_CITATION_LOCATION_TYPE
        for citation in citations
    )


def finding_framework_id(finding: DeskReviewFinding) -> str:
    """Return the finding's framework, treating legacy NULL rows as DPDPA."""
    return finding.framework_id or LEGACY_FINDING_FRAMEWORK_ID


def scoped_findings(db, assessment, *, framework_ids: list[str] | None = None) -> list[DeskReviewFinding]:
    """Return this assessment's findings for selected frameworks, ordered by id."""
    selected = framework_ids if framework_ids is not None else assessment.frameworks
    query = db.query(DeskReviewFinding).filter(
        DeskReviewFinding.assessment_id == assessment.id
    )
    if LEGACY_FINDING_FRAMEWORK_ID in selected:
        query = query.filter(
            (DeskReviewFinding.framework_id.in_(selected))
            | (DeskReviewFinding.framework_id.is_(None))
        )
    else:
        query = query.filter(DeskReviewFinding.framework_id.in_(selected))
    return query.order_by(DeskReviewFinding.id).all()


def group_signal_findings(findings) -> list[dict]:
    """Group denormalized signal rows into one dictionary per original signal."""
    groups: dict[str, dict] = {}
    for finding in findings:
        if finding.finding_type != "signal":
            continue
        key = finding.signal_group_id or f"row:{finding.id}"
        if key not in groups:
            groups[key] = {
                "signal_group_id": finding.signal_group_id,
                "framework_id": finding_framework_id(finding),
                "flag_type": finding.flag_type,
                "content": finding.content,
                "severity": finding.severity,
                "source_quote": finding.source_quote,
                "source_location": finding.source_location,
                "document_id": finding.document_id,
                "citations_json": finding.citations_json,
                "requirement_ids": [],
                "requirement_id": None,
            }
        if finding.requirement_id and finding.requirement_id not in groups[key]["requirement_ids"]:
            groups[key]["requirement_ids"].append(finding.requirement_id)

    for group in groups.values():
        group["requirement_id"] = (
            group["requirement_ids"][0] if group["requirement_ids"] else None
        )
    return list(groups.values())


def load_desk_review_data(db, assessment) -> dict | None:
    """Build analyzer desk-review data from findings selected for this assessment."""
    summary = (
        db.query(DeskReviewSummary)
        .filter(
            DeskReviewSummary.assessment_id == assessment.id,
            DeskReviewSummary.status == "completed",
        )
        .first()
    )
    if not summary:
        return None

    findings = scoped_findings(db, assessment)
    control_ids = {
        control.id
        for framework_id in assessment.frameworks
        for control in FrameworkRegistry.get(framework_id).all_controls()
    }
    try:
        raw_coverage = json.loads(summary.coverage_summary or "{}")
    except (json.JSONDecodeError, TypeError):
        raw_coverage = {}
    coverage = {
        key: value for key, value in raw_coverage.items() if key in control_ids
    }
    if not findings and not coverage:
        return None

    signal_groups = group_signal_findings(findings)
    return {
        "coverage_summary": coverage,
        "findings": [
            {
                "type": finding.finding_type,
                "requirement_id": finding.requirement_id,
                "content": finding.content,
                "source_quote": finding.source_quote,
                "framework_id": finding_framework_id(finding),
                "flag_type": finding.flag_type,
            }
            for finding in findings
        ],
        "signal_flags": [
            {
                "content": group["content"],
                "severity": group["severity"],
                "requirement_id": group["requirement_id"],
                "requirement_ids": group["requirement_ids"],
                "framework_id": group["framework_id"],
                "flag_type": group["flag_type"],
            }
            for group in signal_groups
        ],
        "absence_findings": [
            {
                "content": finding.content,
                "requirement_id": finding.requirement_id,
                "framework_id": finding_framework_id(finding),
            }
            for finding in findings
            if finding.finding_type == "absence"
        ],
    }


def failed_desk_review_frameworks(summary: DeskReviewSummary | None) -> list[str]:
    """Return failed framework ids from a versioned desk-review raw response."""
    if not summary or not summary.raw_ai_response:
        return []
    try:
        raw = json.loads(summary.raw_ai_response)
    except (json.JSONDecodeError, TypeError):
        return []
    if (
        not isinstance(raw, dict)
        or raw.get("schema_version") != 2
        or not isinstance(raw.get("frameworks"), dict)
    ):
        return []
    return [
        framework_id
        for framework_id, result in raw["frameworks"].items()
        if isinstance(result, dict) and result.get("status") == "error"
    ]
