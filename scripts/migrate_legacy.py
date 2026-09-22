"""P1-3: one-shot, idempotent migration of legacy assessment data into the target schema.

INTERFACE STUB ONLY — every function body raises ``NotImplementedError``.
Claude owns the design + the failing test suite (``tests/test_migrate_legacy.py``);
Codex implements the bodies against those tests. Do not change the signatures
without updating the test suite.

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
     ``None`` through if absent", which the schema forbids. The implementer must
     pick one and document it in this docstring:
       (i)  coerce ``None`` -> ``""`` (recommended: no schema change, and the
            empty string is honestly "no evidence captured"); or
       (ii) make ``conclusions.evidence_summary`` nullable via a new Alembic
            revision (heavier: changes an already-merged P1-2 table).
     The test suite asserts only that the row is created and that
     ``evidence_summary`` is falsy for a ``None`` source, so either choice passes
     — but the choice must be stated, not silently made.

D-C. ``Engagement.status`` is non-nullable with no model default, and
     ``Client.industry`` / ``Client.size`` are likewise non-nullable. The spec
     does not name values for these. Suggested: ``Engagement.status="active"``,
     and copy ``Assessment.industry`` / ``Assessment.company_size`` into the
     ``Client``. When one company_name spans assessments with differing
     industry/size, the first-seen assessment (ordered by ``created_at``) wins —
     the ``Client`` is never updated on a later pass. Document whichever rule is
     implemented.

D-D. ``Finding.status`` / ``Action.status`` value sets. ``Finding``'s target set
     is ``open|in_progress|resolved|accepted_risk`` per the plan's intent; any
     ``remediation_status`` that is not in the target set falls back to ``"open"``
     with a ``logger.warning``. ``Action``'s set is
     ``open|in_progress|closed|verified``; migration only ever produces ``open``
     or ``closed`` (``closed`` when ``remediation_closed_at is not None``).

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
import logging

from sqlalchemy.orm import Session

from scripts.backup import create_backup  # noqa: F401 - main() must call this

logger = logging.getLogger(__name__)

_NOT_IMPLEMENTED = "P1-3: implemented by Codex"

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

    raise NotImplementedError(_NOT_IMPLEMENTED)


def map_finding_status(remediation_status: str | None) -> str:
    """Map ``GapItem.remediation_status`` to ``Finding.status`` (see D-D)."""

    raise NotImplementedError(_NOT_IMPLEMENTED)


def map_action_status(remediation_status: str | None, remediation_closed_at) -> str:
    """Map remediation state to ``Action.status`` (closed wins, see D-D)."""

    raise NotImplementedError(_NOT_IMPLEMENTED)


def run_migration(session: Session) -> MigrationStats:
    """Migrate all legacy rows reachable from ``session`` into the target schema.

    Idempotent: safe to call repeatedly. The caller owns the transaction
    boundary only in the sense of session lifetime — this function commits its
    own work before returning.
    """

    raise NotImplementedError(_NOT_IMPLEMENTED)


def build_arg_parser() -> argparse.ArgumentParser:
    """CLI parser. ``--skip-backup`` is accepted but suppressed from ``--help``."""

    raise NotImplementedError(_NOT_IMPLEMENTED)


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

    raise NotImplementedError(_NOT_IMPLEMENTED)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
