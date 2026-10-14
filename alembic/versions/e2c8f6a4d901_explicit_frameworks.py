"""Backfill explicit assessment and finding framework identities.

Revision ID: e2c8f6a4d901
Revises: b7d41c9e2a63
"""
import json

from alembic import op
import sqlalchemy as sa

revision = "e2c8f6a4d901"
down_revision = "b7d41c9e2a63"
branch_labels = None
depends_on = None

# Revision-owned vocabulary must not drift with the application registry.
FRAMEWORK_IDS = ("dpdpa", "iso27001", "gdpr", "hipaa", "nist_csf", "pci_dss")


def preflight(bind) -> dict:
    """Count each backfill rule without modifying the database."""
    selections = {}
    assessment_counts = {
        "null": 0, "invalid_json": 0, "non_list": 0, "empty_list": 0, "unknown_id": 0,
    }
    for assessment_id, stored in bind.execute(sa.text(
        "SELECT id, selected_frameworks FROM assessments"
    )):
        if stored is None:
            assessment_counts["null"] += 1
            selections[assessment_id] = ["dpdpa"]
            continue
        try:
            frameworks = json.loads(stored)
        except (json.JSONDecodeError, TypeError):
            assessment_counts["invalid_json"] += 1
            continue
        if not isinstance(frameworks, list):
            assessment_counts["non_list"] += 1
        elif not frameworks:
            assessment_counts["empty_list"] += 1
        elif any(not isinstance(value, str) or value not in FRAMEWORK_IDS for value in frameworks):
            assessment_counts["unknown_id"] += 1
        else:
            selections[assessment_id] = frameworks

    counts = {"assessments": assessment_counts}
    queries = {
        "desk_review_findings": (
            "SELECT assessment_id FROM desk_review_findings WHERE framework_id IS NULL"
        ),
        "gap_items": (
            "SELECT r.assessment_id FROM gap_items g "
            "LEFT JOIN gap_reports r ON r.id = g.report_id WHERE g.framework_id IS NULL"
        ),
    }
    for table, query in queries.items():
        rows = bind.execute(sa.text(query)).all()
        counts[table] = {
            "null": len(rows),
            "ambiguous": sum("dpdpa" not in selections.get(row[0], []) for row in rows),
        }
    return counts


def upgrade() -> None:
    bind = op.get_bind()
    counts = preflight(bind)
    if (
        any(value for rule, value in counts["assessments"].items() if rule != "null")
        or counts["desk_review_findings"]["ambiguous"]
        or counts["gap_items"]["ambiguous"]
    ):
        raise RuntimeError(
            "Refusing explicit-framework backfill: invalid selections or ambiguous NULL rows. "
            "Preflight counts: " + json.dumps(counts, sort_keys=True)
        )
    bind.execute(sa.text(
        "UPDATE assessments SET selected_frameworks = '[\"dpdpa\"]' "
        "WHERE selected_frameworks IS NULL"
    ))
    bind.execute(sa.text(
        "UPDATE desk_review_findings SET framework_id = 'dpdpa' WHERE framework_id IS NULL"
    ))
    bind.execute(sa.text(
        "UPDATE gap_items SET framework_id = 'dpdpa' WHERE framework_id IS NULL"
    ))


def downgrade() -> None:
    # No schema changed, and framework data stays explicit, so there is nothing to undo.
    pass
