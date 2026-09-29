"""Comparison with the previous issued board-report document."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import literal_column, select
from sqlalchemy.orm import Session

from app.frameworks.registry import FrameworkRegistry
from app.models.assessment import Assessment
from app.models.report_snapshot import ReportSnapshot
from app.services import report_snapshots


STATUSES = ("compared", "no_prior", "unavailable")
DIRECTIONS = ("regressed", "improved", "changed", "new", "no_longer_assessed")
DIRECTION_LABELS = {
    "regressed": "Regressed",
    "improved": "Improved",
    "changed": "Changed",
    "new": "Newly assessed",
    "no_longer_assessed": "No longer assessed",
    "unchanged": "Unchanged",
}
COUNT_KEYS = ("improved", "regressed", "unchanged", "changed", "new", "no_longer_assessed")
OUTCOME_RANK = {"non_compliant": 0, "partially_compliant": 1, "compliant": 2}
OUTCOME_LABELS = {
    "compliant": "Compliant",
    "partially_compliant": "Partially Compliant",
    "non_compliant": "Non-Compliant",
    "insufficient_evidence": "Insufficient Evidence",
    "not_applicable": "Not Applicable",
}
TOTAL_KEYS = ("requirements", "gaps", "critical_high_gaps", "insufficient_evidence", "not_applicable")
REQUIREMENT_ID_ALIASES: dict[tuple[str, str], str] = {}
INTRO_TEXT = (
    "Compared with the last issued board report for the previous assessment period in this "
    "engagement. The earlier report is read from its stored, hash-checked document and is never "
    "regenerated. Scores are compared within each framework only."
)
NO_PRIOR_TEXT = (
    "No earlier issued board report for a previous assessment period exists in this engagement, "
    "so there is nothing to compare."
)
UNAVAILABLE_TEXT = "The earlier issued board report {snapshot} failed its integrity check, so no comparison is shown."
SKIPPED_TEXT = (
    "{count} other issued board report(s) in this engagement failed their integrity check and "
    "were not considered."
)
NOT_IN_PRIOR_TEXT = "{name} was not assessed in the earlier report."
EDITION_CHANGED_TEXT = (
    "{name}: the earlier report assessed version {prior}; this report assesses version {current}. "
    "Outcomes are not compared across versions."
)
CRITERIA_CHANGED_TEXT = (
    "{name}: the test criteria changed between periods ({prior} to {current}). Some changes may "
    "reflect the revised criteria rather than a change in the control."
)
CRITERIA_UNKNOWN_TEXT = (
    "{name}: the pack version of one of the two reports was not recorded, so a change in test "
    "criteria cannot be ruled out."
)


@dataclass
class PriorSelection:
    snapshot: ReportSnapshot | None
    document: dict | None
    document_sha256: str | None
    failed: list[ReportSnapshot]


def _empty_selection() -> PriorSelection:
    return PriorSelection(snapshot=None, document=None, document_sha256=None, failed=[])


def _document_period_end(document: dict) -> date | None:
    basis = document.get("basis")
    raw = basis.get("period_end") if isinstance(basis, dict) else None
    if not isinstance(raw, str) or not raw:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


def find_prior(db: Session, assessment: Assessment, *, period_start: date | None) -> PriorSelection:
    if not assessment.engagement_id or period_start is None:
        return _empty_selection()

    candidates = db.execute(
        select(
            ReportSnapshot,
            literal_column("report_snapshots.rowid").label("snapshot_rowid"),
        )
        .join(Assessment, Assessment.id == ReportSnapshot.assessment_id)
        .where(
            ReportSnapshot.type == report_snapshots.BOARD_REPORT_SNAPSHOT_TYPE,
            ReportSnapshot.is_issued.is_(True),
            ReportSnapshot.assessment_id.is_not(None),
            Assessment.engagement_id == assessment.engagement_id,
            Assessment.id != assessment.id,
            Assessment.status != "archived",
        )
        .order_by(literal_column("report_snapshots.rowid"))
    ).all()

    latest_by_assessment: dict[str, tuple[ReportSnapshot, int]] = {}
    for snapshot, rowid in candidates:
        latest_by_assessment[snapshot.assessment_id] = (snapshot, rowid)

    failed: list[ReportSnapshot] = []
    eligible: list[tuple[date, int, ReportSnapshot, dict, str]] = []
    for snapshot, rowid in sorted(latest_by_assessment.values(), key=lambda pair: pair[1]):
        try:
            document = report_snapshots.read_board_report_document(db, snapshot)
            document_sha256 = report_snapshots.generated_event(db, snapshot.id)["document_sha256"]
        except (report_snapshots.SnapshotIntegrityError, KeyError, TypeError):
            failed.append(snapshot)
            continue
        period_end = _document_period_end(document)
        if period_end is not None and period_end < period_start:
            eligible.append((period_end, rowid, snapshot, document, document_sha256))

    if not eligible:
        return PriorSelection(snapshot=None, document=None, document_sha256=None, failed=failed)
    _period_end, _rowid, snapshot, document, document_sha256 = max(
        eligible,
        key=lambda candidate: (candidate[0], candidate[1]),
    )
    return PriorSelection(
        snapshot=snapshot,
        document=document,
        document_sha256=document_sha256,
        failed=failed,
    )


def classify(prior: str | None, current: str | None) -> str:
    if prior is None:
        return "new"
    if current is None:
        return "no_longer_assessed"
    if prior == current:
        return "unchanged"
    if prior in OUTCOME_RANK and current in OUTCOME_RANK:
        return "improved" if OUTCOME_RANK[current] > OUTCOME_RANK[prior] else "regressed"
    return "changed"


def _outcome_label(outcome: str | None) -> str | None:
    if outcome is None:
        return None
    return OUTCOME_LABELS.get(outcome, outcome.replace("_", " ").title())


def _framework_rank(frameworks: list[dict]) -> dict[str, int]:
    return {framework["framework_id"]: rank for rank, framework in enumerate(frameworks)}


def _requirement_ranks(framework_id: str) -> dict[str, int]:
    try:
        controls = FrameworkRegistry.get(framework_id).all_controls()
    except KeyError:
        return {}
    return {control.id: rank for rank, control in enumerate(controls)}


def _comparison_change(
    *,
    framework_id: str,
    framework_name: str,
    requirement_id: str,
    current_row: dict | None,
    prior_row: dict | None,
) -> tuple[str, dict]:
    prior_outcome = prior_row.get("outcome") if prior_row else None
    current_outcome = current_row.get("outcome") if current_row else None
    direction = classify(prior_outcome, current_outcome)
    row = current_row or prior_row or {}
    return direction, {
        "framework_id": framework_id,
        "framework_name": framework_name,
        "requirement_id": requirement_id,
        "requirement_title": row.get("requirement_title"),
        "prior_outcome": prior_outcome,
        "prior_outcome_label": _outcome_label(prior_outcome),
        "current_outcome": current_outcome,
        "current_outcome_label": _outcome_label(current_outcome),
        "direction": direction,
        "direction_label": DIRECTION_LABELS[direction],
    }


def build_comparison(db: Session, assessment: Assessment, current: dict) -> dict:
    raw_period_start = current.get("basis", {}).get("period_start")
    try:
        period_start = date.fromisoformat(raw_period_start) if raw_period_start else None
    except (TypeError, ValueError):
        period_start = None
    selection = find_prior(db, assessment, period_start=period_start)
    if selection.snapshot is None or selection.document is None:
        status = "unavailable" if selection.failed else "no_prior"
        notes = (
            [UNAVAILABLE_TEXT.format(snapshot=selection.failed[-1].id[:8])]
            if selection.failed
            else [NO_PRIOR_TEXT]
        )
        return {
            "status": status,
            "intro": INTRO_TEXT,
            "notes": notes,
            "prior": None,
            "frameworks": [],
            "changes": [],
            "totals": None,
        }

    prior = selection.document
    notes = []
    if selection.failed:
        notes.append(SKIPPED_TEXT.format(count=len(selection.failed)))
    prior_frameworks = {
        framework.get("framework_id"): framework
        for framework in prior.get("frameworks", [])
        if isinstance(framework, dict) and framework.get("framework_id")
    }
    prior_summary = {
        framework.get("framework_id"): framework
        for framework in prior.get("summary", {}).get("frameworks", [])
        if isinstance(framework, dict) and framework.get("framework_id")
    }
    current_summary = {
        framework.get("framework_id"): framework
        for framework in current.get("summary", {}).get("frameworks", [])
        if isinstance(framework, dict) and framework.get("framework_id")
    }
    current_packs = {
        framework["framework_id"]: framework.get("pack_version")
        for framework in current.get("frameworks", [])
    }
    prior_register = prior.get("appendices", {}).get("requirement_register", [])
    current_register = current.get("appendices", {}).get("requirement_register", [])
    framework_rank = _framework_rank(current.get("frameworks", []))
    comparison_frameworks = []
    changes_with_sort = []

    for framework in current.get("frameworks", []):
        framework_id = framework["framework_id"]
        name = framework["name"]
        prior_framework = prior_frameworks.get(framework_id)
        current_summary_row = current_summary.get(framework_id, {})
        prior_summary_row = prior_summary.get(framework_id, {})
        current_pack = current_packs.get(framework_id)
        current_entry = {
            "framework_id": framework_id,
            "name": name,
            "compared": False,
            "prior_version": None,
            "current_version": framework.get("version"),
            "prior_pack_version": None,
            "current_pack_version": current_pack,
            "prior_score": None,
            "current_score": current_summary_row.get("score"),
            "score_delta": None,
            "prior_rating": None,
            "current_rating": current_summary_row.get("rating"),
            "counts": None,
        }
        if prior_framework is None:
            notes.append(NOT_IN_PRIOR_TEXT.format(name=name))
            comparison_frameworks.append(current_entry)
            continue

        prior_version = prior_framework.get("version")
        current_entry["prior_version"] = prior_version
        current_entry["prior_pack_version"] = prior_framework.get("pack_version")
        if prior_version != framework.get("version"):
            notes.append(
                EDITION_CHANGED_TEXT.format(
                    name=name,
                    prior=prior_version,
                    current=framework.get("version"),
                )
            )
            comparison_frameworks.append(current_entry)
            continue

        current_entry["compared"] = True
        current_entry["prior_score"] = prior_summary_row.get("score")
        current_entry["prior_rating"] = prior_summary_row.get("rating")
        if (
            current_summary_row.get("status") == "scored"
            and prior_summary_row.get("status") == "scored"
            and current_summary_row.get("score") is not None
            and prior_summary_row.get("score") is not None
        ):
            current_entry["score_delta"] = round(
                current_summary_row["score"] - prior_summary_row["score"], 1
            )
        if current_pack is None or prior_framework.get("pack_version") is None:
            notes.append(CRITERIA_UNKNOWN_TEXT.format(name=name))
        elif current_pack != prior_framework.get("pack_version"):
            notes.append(
                CRITERIA_CHANGED_TEXT.format(
                    name=name,
                    prior=prior_framework.get("pack_version"),
                    current=current_pack,
                )
            )

        counts = {key: 0 for key in COUNT_KEYS}
        current_rows = {
            row.get("requirement_id"): row
            for row in current_register
            if row.get("framework_id") == framework_id and row.get("requirement_id")
        }
        prior_rows = {}
        for row in prior_register:
            if row.get("framework_id") != framework_id or not row.get("requirement_id"):
                continue
            prior_id = row["requirement_id"]
            mapped_id = REQUIREMENT_ID_ALIASES.get((framework_id, prior_id), prior_id)
            prior_rows[mapped_id] = row
        requirement_ids = list(current_rows)
        requirement_ids.extend(requirement_id for requirement_id in prior_rows if requirement_id not in current_rows)
        requirement_ranks = _requirement_ranks(framework_id)
        for requirement_id in requirement_ids:
            current_row = current_rows.get(requirement_id)
            prior_row = prior_rows.get(requirement_id)
            direction, change = _comparison_change(
                framework_id=framework_id,
                framework_name=name,
                requirement_id=requirement_id,
                current_row=current_row,
                prior_row=prior_row,
            )
            counts[direction] += 1
            if direction != "unchanged":
                changes_with_sort.append(
                    (
                        DIRECTIONS.index(direction),
                        framework_rank.get(framework_id, len(framework_rank)),
                        requirement_ranks.get(requirement_id, 10**9),
                        requirement_id,
                        change,
                    )
                )
        current_entry["counts"] = counts
        comparison_frameworks.append(current_entry)

    changes_with_sort.sort(key=lambda item: item[:4])
    current_totals = current.get("summary", {}).get("totals", {})
    prior_totals = prior.get("summary", {}).get("totals", {})
    return {
        "status": "compared",
        "intro": INTRO_TEXT,
        "notes": notes,
        "prior": {
            "snapshot_id": selection.snapshot.id,
            "assessment_id": selection.snapshot.assessment_id,
            "version_label": prior.get("snapshot", {}).get("version_label"),
            "generated_on": prior.get("snapshot", {}).get("generated_on"),
            "period_label": prior.get("basis", {}).get("period_label"),
            "cutoff_label": prior.get("basis", {}).get("cutoff_label"),
            "document_sha256": selection.document_sha256,
            "schema_version": prior.get("schema_version"),
        },
        "frameworks": comparison_frameworks,
        "changes": [item[4] for item in changes_with_sort],
        "totals": {
            "prior": {key: prior_totals.get(key) for key in TOTAL_KEYS},
            "current": {key: current_totals.get(key) for key in TOTAL_KEYS},
        },
    }
