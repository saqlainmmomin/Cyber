"""P1-3: one-shot, idempotent migration of legacy assessment data into the target schema.

Claude owns the design and the test suite (``tests/test_migrate_legacy.py``);
this module implements the migration against that executable specification. Do
not change the function signatures without updating the test suite.

What this script does
---------------------
Given any current-schema SQLite database (empty, or holding legacy
``Assessment`` / ``GapReport`` / ``GapItem`` rows), it:

1. Creates one ``Client`` per distinct ``Assessment.company_name`` (case-sensitive
   exact match, no fuzzy matching).
2. Creates one ``Engagement`` per ``Assessment`` — always, even when two
   assessments share a ``company_name``. Same-name assessments are NOT assumed to
   belong to one engagement. ``Engagement.type = "gap_assessment"``;
   ``Engagement.name`` is ``assessment.description`` when present, else
   ``f"Imported: {company_name} ({created_at.date()})"``.
3. Creates one ``AssessmentPack`` per (assessment, framework id from
   ``Assessment.frameworks``), with ``pack_version="unknown"`` (no version
   metadata exists on ``FrameworkDefinition`` yet — "unknown" is correct, not a
   placeholder to be replaced by invented data).
4. Maps every ``GapItem`` to one ``Conclusion`` plus one or two
   ``ConclusionRevision`` rows, and — only when ``remediation_status is not
   None`` — one ``Finding`` and one ``Action``.

It is idempotent: running it twice against the same database creates zero
additional rows the second time.

Mapping table (compliance_status -> Conclusion.outcome)
------------------------------------------------------
    compliant           -> compliant
    partially_compliant -> partially_compliant
    non_compliant       -> non_compliant
    not_applicable      -> not_applicable
    not_assessed        -> insufficient_evidence   (+ logger.warning per row,
                                                    including assessment_id and
                                                    requirement_id, so these are
                                                    flagged for manual review)

Invariants and non-goals
------------------------
* ``Assessment.company_name`` is frozen at migration time: this script only
  *reads* it to derive the ``Client``. ``client.name == assessment.company_name``
  is a **migration-time** invariant, not an ongoing constraint — a consultant may
  later rename a ``Client`` without ``Assessment.company_name`` following it.
* ``gap_reports``, ``gap_items`` and ``initiatives`` are retired-but-preserved:
  never deleted, never mutated by this script. ``Initiative`` rows are NOT
  migrated (no target-schema equivalent).
* ``GapReport.legacy_history`` and ``GapReport.framework_scores`` are read-only
  here — not read, not transformed, not moved.
* ``assessments.engagement_id`` stays nullable (a separate, later task).
* ``evidence``, ``evidence_versions``, ``evidence_uses``, ``citations`` and
  ``magic_links`` are never touched — empty until Phase 2.

OPEN DECISIONS FOR THE IMPLEMENTER (resolve explicitly, document the choice)
---------------------------------------------------------------------------
D-A. ``framework_scores`` has nowhere to go. ``AssessmentPack`` (P1-2, already
     merged) has **no score column**, and this task must not invent one. The
     resolution adopted here is: leave ``GapReport.framework_scores`` in place,
     untouched and authoritative, and have downstream code (P1-5 and later) read
     historical per-framework scores from it until a later phase adds proper
     per-pack score storage. ``tests/test_migrate_legacy.py`` asserts the column
     is byte-identical before and after migration as a regression guard. Do NOT
     "solve" this by extending P1-2's schema.

D-B. ``Conclusion.evidence_summary`` is a **non-nullable** ``Text`` column, but
     its source ``GapItem.evidence_quote`` is nullable. The spec says "carry
     ``None`` through if absent", which the schema forbids. Resolution: coerce
     ``None`` -> ``""`` (no schema change; the empty string honestly means no
     evidence was captured).

D-C. ``Engagement.status`` is non-nullable with no model default, and
     ``Client.industry`` / ``Client.size`` are likewise non-nullable. Resolution:
     use ``Engagement.status="active"``, copy ``Assessment.industry`` /
     ``Assessment.company_size`` into a new ``Client``, and process assessments
     by ``created_at`` so the first assessment for a company wins. A later pass
     never updates the existing ``Client``.

D-D. ``Finding.status`` / ``Action.status`` value sets. Resolution: ``Finding``'s
     target set is ``open|in_progress|resolved|accepted_risk``; any
     ``remediation_status`` that is not in the target set falls back to ``"open"``
     with a ``logger.warning``. ``Action``'s set is
     ``open|in_progress|closed|verified``; migration only ever produces ``open``
     or ``closed`` (``closed`` when ``remediation_closed_at is not None``).
     A later run skips any existing Finding because its Actions are then
     consultant-operated and must not be re-mapped.

Backup safety
-------------
``main()`` MUST call ``scripts.backup.create_backup(db_path, upload_dir, out_dir)``
before any write, and abort with a non-zero exit code if it raises. The
``--skip-backup`` flag exists solely for the test suite and is hidden from
``--help``.

Rollback: ``scripts/rollback_legacy.py``, pointed at the backup directory this
script prints on a successful run.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import json
import logging
from pathlib import Path
import sys

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings
from app.models.action import Action
from app.models.assessment import Assessment
from app.models.assessment_pack import AssessmentPack
from app.models.analysis_run import AnalysisRun
from app.models.client import Client
from app.models.conclusion import Conclusion, ConclusionRevision
from app.models.engagement import Engagement
from app.models.finding import Finding
from app.models.report import GapItem, GapReport
from scripts.backup import create_backup, database_path

logger = logging.getLogger(__name__)

#: Legacy ``GapItem.compliance_status`` -> target ``Conclusion.outcome``.
OUTCOME_MAP: dict[str, str] = {
    "compliant": "compliant",
    "partially_compliant": "partially_compliant",
    "non_compliant": "non_compliant",
    "not_applicable": "not_applicable",
    "not_assessed": "insufficient_evidence",
}

#: Accepted ``Finding.status`` values; anything else falls back to "open".
FINDING_STATUSES: frozenset[str] = frozenset(
    {"open", "in_progress", "resolved", "accepted_risk"}
)

#: Accepted ``Action.status`` values. Migration only ever emits open/closed.
ACTION_STATUSES: frozenset[str] = frozenset({"open", "in_progress", "closed", "verified"})

#: Placeholder pack version — no version metadata exists on FrameworkDefinition.
UNKNOWN_PACK_VERSION = "unknown"

MIGRATION_ACTOR = "system:migration"


@dataclass
class MigrationStats:
    """Counts of rows *created* by a single ``run_migration`` call.

    A second, idempotent run against the same database must return an instance
    where every count is zero.
    """

    clients: int = 0
    engagements: int = 0
    assessment_packs: int = 0
    conclusions: int = 0
    conclusion_revisions: int = 0
    findings: int = 0
    actions: int = 0
    warnings: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return (
            self.clients
            + self.engagements
            + self.assessment_packs
            + self.conclusions
            + self.conclusion_revisions
            + self.findings
            + self.actions
        )


def map_outcome(compliance_status: str, *, assessment_id: str, requirement_id: str) -> str:
    """Map a legacy ``compliance_status`` to a ``Conclusion.outcome``.

    ``not_assessed`` maps to ``insufficient_evidence`` and MUST emit a
    ``logger.warning`` naming ``assessment_id`` and ``requirement_id``.
    """

    outcome = OUTCOME_MAP[compliance_status]
    if compliance_status == "not_assessed":
        logger.warning(
            "Assessment %s requirement %s is not assessed; migrating as "
            "insufficient_evidence",
            assessment_id,
            requirement_id,
        )
    return outcome


def map_finding_status(remediation_status: str | None) -> str:
    """Map ``GapItem.remediation_status`` to ``Finding.status`` (see D-D)."""

    if remediation_status in FINDING_STATUSES:
        return remediation_status
    logger.warning(
        "Unknown remediation status %r; defaulting Finding.status to 'open'",
        remediation_status,
    )
    return "open"


def map_action_status(remediation_status: str | None, remediation_closed_at) -> str:
    """Map remediation state to ``Action.status`` (closed wins, see D-D)."""

    return "closed" if remediation_closed_at is not None else "open"


def run_migration(session: Session) -> MigrationStats:
    """Migrate all legacy rows reachable from ``session`` into the target schema.

    Idempotent: safe to call repeatedly. The caller owns the transaction
    boundary only in the sense of session lifetime — this function commits its
    own work before returning.
    """

    stats = MigrationStats()

    try:
        assessments = list(
            session.execute(
                select(Assessment).order_by(Assessment.created_at, Assessment.id)
        ).scalars()
        )

        for assessment in assessments:
            client = session.execute(
                select(Client).where(Client.name == assessment.company_name)
            ).scalar_one_or_none()
            if client is None:
                client = Client(
                    name=assessment.company_name,
                    industry=assessment.industry,
                    size=assessment.company_size,
                )
                session.add(client)
                session.flush()
                stats.clients += 1

            engagement = (
                session.get(Engagement, assessment.engagement_id)
                if assessment.engagement_id
                else None
            )
            if engagement is None:
                engagement_name = assessment.description or (
                    f"Imported: {assessment.company_name} "
                    f"({assessment.created_at.date()})"
                )
                engagement = Engagement(
                    client_id=client.id,
                    name=engagement_name,
                    type="gap_assessment",
                    status="active",
                )
                session.add(engagement)
                session.flush()
                assessment.engagement_id = engagement.id
                stats.engagements += 1
            for framework_id in assessment.frameworks:
                pack = session.execute(
                    select(AssessmentPack).where(
                        AssessmentPack.assessment_id == assessment.id,
                        AssessmentPack.framework_id == framework_id,
                    )
                ).scalar_one_or_none()
                if pack is None:
                    session.add(
                        AssessmentPack(
                            assessment_id=assessment.id,
                            framework_id=framework_id,
                            pack_version=UNKNOWN_PACK_VERSION,
                        )
                    )
                    session.flush()
                    stats.assessment_packs += 1

            has_analysis_run = session.execute(
                select(AnalysisRun.id)
                .where(AnalysisRun.assessment_id == assessment.id)
                .limit(1)
            ).scalar_one_or_none()
            if has_analysis_run is not None:
                warning = (
                    f"Assessment {assessment.id}: conclusions are owned by the "
                    "analysis pipeline (P2-3); legacy GapItem mapping skipped."
                )
                stats.warnings.append(warning)
                logger.warning(warning)
                continue

            report = session.execute(
                select(GapReport).where(GapReport.assessment_id == assessment.id)
            ).scalar_one_or_none()
            if report is None:
                continue

            items = list(
                session.execute(
                    select(GapItem).where(GapItem.report_id == report.id)
                ).scalars()
            )
            for item in items:
                framework_id = item.framework_id or assessment.frameworks[0]
                remediation_status = item.remediation_status
                conclusion = session.execute(
                    select(Conclusion).where(
                        Conclusion.assessment_id == assessment.id,
                        Conclusion.requirement_id == item.requirement_id,
                        Conclusion.framework_id == framework_id,
                    )
                ).scalar_one_or_none()

                if conclusion is None:
                    outcome = map_outcome(
                        item.compliance_status,
                        assessment_id=assessment.id,
                        requirement_id=item.requirement_id,
                    )
                    conclusion = Conclusion(
                        assessment_id=assessment.id,
                        requirement_id=item.requirement_id,
                        framework_id=framework_id,
                        cluster_id=item.cluster_id,
                        outcome=outcome,
                        rationale=item.gap_description,
                        evidence_summary=item.evidence_quote or "",
                        gaps_identified=item.gap_description,
                        risk_level=item.risk_level,
                        recommended_action=item.remediation_action,
                        ai_proposed=True,
                        version=1,
                    )
                    session.add(conclusion)
                    session.flush()
                    stats.conclusions += 1
                    if item.compliance_status == "not_assessed":
                        stats.warnings.append(
                            f"Assessment {assessment.id} requirement "
                            f"{item.requirement_id} is not assessed; migrating as "
                            "insufficient_evidence"
                        )

                proposed = session.execute(
                    select(ConclusionRevision).where(
                        ConclusionRevision.conclusion_id == conclusion.id,
                        ConclusionRevision.action == "proposed",
                    )
                ).scalar_one_or_none()
                if proposed is None:
                    proposed_values = {
                        "conclusion_id": conclusion.id,
                        "actor": MIGRATION_ACTOR,
                        "action": "proposed",
                        "previous_outcome": None,
                        "previous_rationale": None,
                        "citations_json": None,
                    }
                    if item.reviewed_at is not None:
                        proposed_values["created_at"] = item.reviewed_at - timedelta(
                            microseconds=1
                        )
                    session.add(
                        ConclusionRevision(**proposed_values)
                    )
                    session.flush()
                    stats.conclusion_revisions += 1

                if item.reviewed_at is not None:
                    approved = session.execute(
                        select(ConclusionRevision).where(
                            ConclusionRevision.conclusion_id == conclusion.id,
                            ConclusionRevision.action == "approved",
                        )
                    ).scalar_one_or_none()
                    if approved is None:
                        session.add(
                            ConclusionRevision(
                                conclusion_id=conclusion.id,
                                actor=item.reviewed_by or "unknown",
                                action="approved",
                                previous_outcome=(
                                    item.ai_compliance_status or conclusion.outcome
                                ),
                                previous_rationale=(
                                    item.ai_gap_description or conclusion.rationale
                                ),
                                citations_json=None,
                                created_at=item.reviewed_at,
                            )
                        )
                        session.flush()
                        stats.conclusion_revisions += 1

                if remediation_status is None:
                    continue

                finding = session.execute(
                    select(Finding).where(
                        Finding.assessment_id == assessment.id,
                        Finding.conclusion_id == conclusion.id,
                    )
                ).scalar_one_or_none()
                if finding is not None:
                    # P3-1: an existing Finding and its Actions are consultant-operated; never re-map them.
                    continue
                finding_status = map_finding_status(remediation_status)
                if remediation_status not in FINDING_STATUSES:
                    stats.warnings.append(
                        f"Unknown remediation status {remediation_status!r}; "
                        "defaulting Finding.status to 'open'"
                    )
                finding = Finding(
                    assessment_id=assessment.id,
                    conclusion_id=conclusion.id,
                    title=item.requirement_title,
                    description=item.gap_description,
                    severity=item.risk_level,
                    priority=item.remediation_priority,
                    status=finding_status,
                )
                session.add(finding)
                session.flush()
                stats.findings += 1

                timestamp = datetime.now(timezone.utc).isoformat()
                session.add(
                    Action(
                        finding_id=finding.id,
                        title=item.remediation_action,
                        owner=item.remediation_owner,
                        target_date=item.remediation_target_date,
                        status=map_action_status(
                            remediation_status, item.remediation_closed_at
                        ),
                        history_json=json.dumps(
                            [
                                {
                                    "actor": MIGRATION_ACTOR,
                                    "action": "imported",
                                    "timestamp": timestamp,
                                    "notes": "Migrated from legacy GapItem remediation fields",
                                }
                            ]
                        ),
                    )
                )
                session.flush()
                stats.actions += 1

        session.commit()
    except Exception:
        session.rollback()
        raise

    return stats


def build_arg_parser() -> argparse.ArgumentParser:
    """CLI parser. ``--skip-backup`` is accepted but suppressed from ``--help``."""

    parser = argparse.ArgumentParser(
        description="Migrate legacy CyberAssess assessment data into the target schema."
    )
    parser.add_argument("--db-url", default=settings.database_url)
    parser.add_argument("--upload-dir", default=settings.upload_dir)
    parser.add_argument("--backup-out-dir", default="backups")
    parser.add_argument(
        "--skip-backup",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    Unless ``--skip-backup`` is passed, calls
    ``scripts.backup.create_backup(db_path, upload_dir, out_dir)`` BEFORE opening
    any write transaction and returns a non-zero exit code without writing
    anything if it raises. On success, prints the backup directory path so a
    human can hand it to ``scripts/rollback_legacy.py``.

    Flags: ``--db-url``, ``--upload-dir``, ``--backup-out-dir``,
    ``--skip-backup`` (hidden).
    """

    args = build_arg_parser().parse_args(argv)
    db_path = database_path(args.db_url)
    upload_dir = Path(args.upload_dir)
    backup_dir = None

    if not args.skip_backup:
        try:
            backup_dir = create_backup(
                db_path,
                upload_dir,
                Path(args.backup_out_dir),
            )
        except Exception as exc:
            print(f"Migration backup failed: {exc}", file=sys.stderr)
            return 1

    engine = create_engine(
        args.db_url,
        connect_args={"check_same_thread": False}
        if args.db_url.startswith("sqlite")
        else {},
    )
    try:
        with Session(engine) as session:
            stats = run_migration(session)
    except Exception as exc:
        print(f"Migration failed: {exc}", file=sys.stderr)
        return 1
    finally:
        engine.dispose()

    if backup_dir is not None:
        print(f"Backup: {backup_dir}")
    print(f"Migration complete: {stats.total} rows created")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
