"""Frozen table DDL used by the historical Alembic retrofit revision
(alembic/versions/6fcd9e575309_retrofit_legacy_columns_fks_and_.py) when it
rebuilds a genuinely legacy, pre-baseline SQLite table to add foreign key
constraints.

This is a hand-written snapshot of each FK-bearing table's final column
set, primary key, foreign keys, and indexes AS OF THAT REVISION -- never a
live lookup of `Base.metadata` / `app.models`. A historical migration must
keep producing the same DDL forever, independent of how the ORM models
change after this PR; otherwise a later revision that adds a column to one
of these tables could collide with (or be silently pre-empted by) this
retrofit rebuild. See app/legacy_migrations.py:_rebuild_table_for_fks,
which takes a frozen Table from FROZEN_TABLES as a parameter instead of
resolving it itself.

Column sets mirror alembic/versions/6fc718bb9f09_baseline_schema.py (also
hand-frozen): by the time PR #16 was written, every column these tables
need already existed in the frozen baseline, since
app.legacy_migrations.run_column_migrations only backfills columns on a
genuinely old, unversioned database that pre-dates the baseline squash.
Future schema changes belong in new Alembic revisions layered on top of
this frozen shape -- never in edits here.
"""
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKeyConstraint,
    Index,
    Integer,
    MetaData,
    PrimaryKeyConstraint,
    String,
    Table,
    Text,
    text,
)

# A private MetaData -- deliberately never Base.metadata -- so these
# definitions can never accidentally pick up live model changes or
# collide with app.models' own table registry.
_metadata = MetaData()


def _table(name: str, *args) -> Table:
    return Table(name, _metadata, *args)


# "assessments" is never itself rebuilt (it isn't in FK_REBUILD_ORDER --
# nothing references it via a column that needs an FK *from* it), but it
# is the FK target for several of the tables below. SQLAlchemy's
# ForeignKeyConstraint needs the target table registered in the same
# MetaData to resolve at DDL-compile time, so it's included here as a
# minimal stub (just the referenced column) -- not the full frozen shape,
# since CreateTable is never called for it.
_table(
    "assessments",
    Column("id", String(length=36), nullable=False),
    PrimaryKeyConstraint("id"),
)

FROZEN_TABLES: dict[str, Table] = {
    "assessment_documents": _table(
        "assessment_documents",
        Column("id", String(length=36), nullable=False),
        Column("assessment_id", String(length=36), nullable=False),
        Column("filename", String(length=255), nullable=False),
        Column("file_path", String(length=500), nullable=False),
        Column("file_type", String(length=10), nullable=False),
        Column("document_category", String(length=50), nullable=False),
        Column("extracted_text", Text(), nullable=True),
        Column("uploaded_at", DateTime(timezone=True), nullable=False),
        ForeignKeyConstraint(["assessment_id"], ["assessments.id"]),
        PrimaryKeyConstraint("id"),
        Index("ix_assessment_documents_assessment_id", "assessment_id", unique=False),
    ),
    "gap_reports": _table(
        "gap_reports",
        Column("id", String(length=36), nullable=False),
        Column("assessment_id", String(length=36), nullable=False),
        Column("overall_score", Float(), nullable=False),
        Column("chapter_scores", Text(), nullable=False),
        Column("executive_summary", Text(), nullable=False),
        Column("raw_ai_response", Text(), nullable=False),
        Column("framework_scores", Text(), nullable=True),
        Column("legacy_history", Text(), nullable=True),
        Column("generated_at", DateTime(timezone=True), nullable=False),
        ForeignKeyConstraint(["assessment_id"], ["assessments.id"]),
        PrimaryKeyConstraint("id"),
        Index("ix_gap_reports_assessment_id", "assessment_id", unique=True),
    ),
    "gap_items": _table(
        "gap_items",
        Column("id", String(length=36), nullable=False),
        Column("report_id", String(length=36), nullable=False),
        Column("requirement_id", String(length=50), nullable=False),
        Column("framework_id", String(length=30), nullable=True),
        Column("cluster_id", String(length=80), nullable=True),
        Column("control_reference", String(length=100), nullable=True),
        Column("chapter", String(length=50), nullable=False),
        Column("requirement_title", String(length=255), nullable=False),
        Column("compliance_status", String(length=30), nullable=False),
        Column("current_state", Text(), nullable=False),
        Column("gap_description", Text(), nullable=False),
        Column("risk_level", String(length=20), nullable=False),
        Column("remediation_action", Text(), nullable=False),
        Column("remediation_priority", Integer(), nullable=False),
        Column("remediation_effort", String(length=20), nullable=False),
        Column("timeline_weeks", Integer(), nullable=False),
        Column("maturity_level", Integer(), nullable=True),
        Column("root_cause_category", String(length=30), nullable=True),
        Column("evidence_quote", Text(), nullable=True),
        Column("evidence_confidence", String(length=20), nullable=True),
        Column("remediation_status", String(length=20), nullable=True),
        Column("remediation_owner", String(length=255), nullable=True),
        Column("remediation_target_date", DateTime(), nullable=True),
        Column("remediation_notes", Text(), nullable=True),
        Column("remediation_closed_at", DateTime(timezone=True), nullable=True),
        Column("review_status", String(length=20), nullable=True),
        Column("needs_review", Boolean(), server_default="0", nullable=True),
        Column("ai_compliance_status", Text(), nullable=True),
        Column("ai_gap_description", Text(), nullable=True),
        Column("ai_risk_level", String(length=20), nullable=True),
        Column("reviewer_notes", Text(), nullable=True),
        Column("reviewed_by", String(length=255), nullable=True),
        Column("reviewed_at", DateTime(timezone=True), nullable=True),
        ForeignKeyConstraint(["report_id"], ["gap_reports.id"]),
        PrimaryKeyConstraint("id"),
        Index("ix_gap_items_report_id", "report_id", unique=False),
        # Partial index over rows still awaiting the framework_id backfill.
        # Must be declared here too (mirroring the frozen baseline's own
        # declaration -- see 6fc718bb9f09_baseline_schema.py) so a legacy
        # gap_items rebuild recreates it: `_rebuild_table_for_fks` drops the
        # old table (and every index on it, including this one, which
        # run_column_migrations creates ad hoc before the rebuild) and
        # creates only what's declared on this frozen `Table`.
        Index(
            "ix_gap_items_null_framework_id",
            "id",
            unique=False,
            sqlite_where=text("framework_id IS NULL"),
        ),
    ),
    "initiatives": _table(
        "initiatives",
        Column("id", String(length=36), nullable=False),
        Column("report_id", String(length=36), nullable=False),
        Column("initiative_id", String(length=20), nullable=False),
        Column("title", String(length=255), nullable=False),
        Column("root_cause", Text(), nullable=False),
        Column("root_cause_category", String(length=30), nullable=False),
        Column("requirements_addressed", Text(), nullable=False),
        Column("combined_effort", String(length=20), nullable=False),
        Column("combined_timeline_weeks", Integer(), nullable=False),
        Column("priority", Integer(), nullable=False),
        Column("budget_estimate_band", String(length=50), nullable=True),
        Column("suggested_approach", Text(), nullable=False),
        ForeignKeyConstraint(["report_id"], ["gap_reports.id"]),
        PrimaryKeyConstraint("id"),
        Index("ix_initiatives_report_id", "report_id", unique=False),
    ),
    "desk_review_summaries": _table(
        "desk_review_summaries",
        Column("id", Integer(), autoincrement=True, nullable=False),
        Column("assessment_id", String(length=36), nullable=False),
        Column("document_catalog", Text(), nullable=True),
        Column("coverage_summary", Text(), nullable=True),
        Column("raw_ai_response", Text(), nullable=True),
        Column("status", String(length=20), nullable=False),
        Column("error_message", Text(), nullable=True),
        Column("started_at", DateTime(timezone=True), nullable=True),
        Column("completed_at", DateTime(timezone=True), nullable=True),
        Column("legacy_history", Text(), nullable=True),
        ForeignKeyConstraint(["assessment_id"], ["assessments.id"]),
        PrimaryKeyConstraint("id"),
        Index("ix_desk_review_summaries_assessment_id", "assessment_id", unique=True),
    ),
    "desk_review_findings": _table(
        "desk_review_findings",
        Column("id", Integer(), autoincrement=True, nullable=False),
        Column("assessment_id", String(length=36), nullable=False),
        Column("finding_type", String(length=20), nullable=False),
        Column("requirement_id", String(length=30), nullable=True),
        Column("document_id", String(length=36), nullable=True),
        Column("content", Text(), nullable=False),
        Column("severity", String(length=20), nullable=False),
        Column("source_quote", Text(), nullable=True),
        Column("source_location", String(length=200), nullable=True),
        Column("created_at", DateTime(timezone=True), nullable=False),
        ForeignKeyConstraint(["assessment_id"], ["assessments.id"]),
        ForeignKeyConstraint(
            ["document_id"], ["assessment_documents.id"], ondelete="SET NULL"
        ),
        PrimaryKeyConstraint("id"),
        Index("ix_desk_review_findings_assessment_id", "assessment_id", unique=False),
    ),
    "rfi_documents": _table(
        "rfi_documents",
        Column("id", String(length=36), nullable=False),
        Column("assessment_id", String(length=36), nullable=False),
        Column("title", String(length=255), nullable=False),
        Column("introduction", Text(), nullable=False),
        Column("evidence_items", Text(), nullable=False),
        Column("response_instructions", Text(), nullable=False),
        Column("appendix", Text(), nullable=True),
        Column("total_items", Integer(), nullable=False),
        Column("critical_items", Integer(), nullable=False),
        Column("raw_ai_response", Text(), nullable=True),
        Column("generated_at", DateTime(timezone=True), nullable=False),
        ForeignKeyConstraint(["assessment_id"], ["assessments.id"]),
        PrimaryKeyConstraint("id"),
        Index("ix_rfi_documents_assessment_id", "assessment_id", unique=True),
    ),
    "questionnaire_responses": _table(
        "questionnaire_responses",
        Column("id", String(length=36), nullable=False),
        Column("assessment_id", String(length=36), nullable=False),
        Column("question_id", String(length=50), nullable=False),
        Column("answer", String(length=20), nullable=False),
        Column("notes", Text(), nullable=True),
        Column("evidence_reference", Text(), nullable=True),
        Column("na_reason", String(length=50), nullable=True),
        Column("confidence", String(length=20), nullable=True),
        Column("cluster_id", String(length=80), nullable=True),
        Column("answer_source", String(length=20), nullable=True),
        Column("submitted_at", DateTime(timezone=True), nullable=False),
        CheckConstraint(
            "answer IN ('fully_implemented', 'partially_implemented', 'planned', "
            "'not_implemented', 'not_applicable')",
            name="ck_questionnaire_responses_answer_valid",
        ),
        ForeignKeyConstraint(["assessment_id"], ["assessments.id"]),
        PrimaryKeyConstraint("id"),
        Index("ix_questionnaire_responses_assessment_id", "assessment_id", unique=False),
    ),
}
