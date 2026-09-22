"""Legacy schema retrofit logic, invoked by the Alembic revision that
replaced the old DIY startup migration path (formerly in app/main.py).

Kept as a plain importable module — rather than inlined in
alembic/versions/ — so it can also be unit-tested directly against
isolated in-memory engines (see tests/test_needs_review_ui.py and
tests/test_questionnaire_rebuild.py) without going through the full
multi-table Alembic upgrade pipeline.
"""
import logging

from sqlalchemy import inspect, text
from sqlalchemy.schema import CreateIndex, CreateTable

logger = logging.getLogger(__name__)

VALID_QUESTIONNAIRE_ANSWERS = (
    "fully_implemented",
    "partially_implemented",
    "planned",
    "not_implemented",
    "not_applicable",
)
LEGACY_QUESTIONNAIRE_ANSWER_MAP = {
    "yes": "fully_implemented",
    "partial": "partially_implemented",
    "no": "not_implemented",
}

FK_SPEC: dict[str, list[tuple[str, str, str, str | None]]] = {
    "assessment_documents": [("assessment_id", "assessments", "id", None)],
    "gap_reports": [("assessment_id", "assessments", "id", None)],
    "gap_items": [("report_id", "gap_reports", "id", None)],
    "initiatives": [("report_id", "gap_reports", "id", None)],
    "desk_review_summaries": [("assessment_id", "assessments", "id", None)],
    "desk_review_findings": [
        ("assessment_id", "assessments", "id", None),
        ("document_id", "assessment_documents", "id", "SET NULL"),
    ],
    "rfi_documents": [("assessment_id", "assessments", "id", None)],
    "questionnaire_responses": [("assessment_id", "assessments", "id", None)],
}

FK_REBUILD_ORDER = [
    "assessment_documents",
    "gap_reports",
    "gap_items",
    "initiatives",
    "desk_review_summaries",
    "desk_review_findings",
    "rfi_documents",
    "questionnaire_responses",
]


def ensure_questionnaire_answer_constraint(conn):
    """Ensure questionnaire responses enforce the allowed answer set."""
    if conn.dialect.name == "sqlite":
        create_sql = conn.execute(
            text("SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'questionnaire_responses'")
        ).scalar()
        if create_sql and "ck_questionnaire_responses_answer_valid" in create_sql:
            return

        for legacy_answer, normalized_answer in LEGACY_QUESTIONNAIRE_ANSWER_MAP.items():
            updated = conn.execute(
                text(
                    "UPDATE questionnaire_responses "
                    "SET answer = :normalized_answer "
                    "WHERE answer = :legacy_answer"
                ),
                {"normalized_answer": normalized_answer, "legacy_answer": legacy_answer},
            )
            if updated.rowcount:
                logger.info(
                    "Migration: normalized %s legacy questionnaire answers from %s",
                    updated.rowcount,
                    legacy_answer,
                )

        invalid_answer_params = {
            f"answer_{idx}": answer for idx, answer in enumerate(VALID_QUESTIONNAIRE_ANSWERS)
        }
        invalid_answer_placeholders = ", ".join(f":answer_{idx}" for idx in range(len(VALID_QUESTIONNAIRE_ANSWERS)))
        deleted = conn.execute(
            text(
                f"DELETE FROM questionnaire_responses WHERE answer NOT IN ({invalid_answer_placeholders})"
            ),
            invalid_answer_params,
        )
        if deleted.rowcount:
            logger.warning(
                "Migration: removed %s questionnaire responses with invalid answers before applying constraint",
                deleted.rowcount,
            )

        conn.execute(text("ALTER TABLE questionnaire_responses RENAME TO questionnaire_responses_old"))
        conn.execute(
            text(
                """
                CREATE TABLE questionnaire_responses (
                    id VARCHAR(36) NOT NULL PRIMARY KEY,
                    assessment_id VARCHAR(36) NOT NULL,
                    question_id VARCHAR(50) NOT NULL,
                    answer VARCHAR(20) NOT NULL,
                    notes TEXT,
                    evidence_reference TEXT,
                    na_reason TEXT,
                    confidence TEXT,
                    cluster_id VARCHAR(80),
                    answer_source VARCHAR(20) DEFAULT 'human',
                    submitted_at DATETIME NOT NULL,
                    CONSTRAINT ck_questionnaire_responses_answer_valid
                        CHECK (answer IN ('fully_implemented', 'partially_implemented', 'planned', 'not_implemented', 'not_applicable')),
                    FOREIGN KEY (assessment_id) REFERENCES assessments(id)
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO questionnaire_responses (
                    id, assessment_id, question_id, answer, notes, evidence_reference, na_reason, confidence, cluster_id, answer_source, submitted_at
                )
                SELECT
                    id, assessment_id, question_id, answer, notes, evidence_reference, na_reason, confidence, cluster_id, answer_source, submitted_at
                FROM questionnaire_responses_old
                """
            )
        )
        conn.execute(text("DROP TABLE questionnaire_responses_old"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_questionnaire_responses_assessment_id ON questionnaire_responses (assessment_id)"))
        logger.info("Migration: rebuilt questionnaire_responses with answer constraint")
        return

    inspector = inspect(conn)
    existing_constraints = {
        constraint["name"] for constraint in inspector.get_check_constraints("questionnaire_responses")
    }
    if "ck_questionnaire_responses_answer_valid" not in existing_constraints:
        conn.execute(
            text(
                """
                ALTER TABLE questionnaire_responses
                ADD CONSTRAINT ck_questionnaire_responses_answer_valid
                CHECK (answer IN ('fully_implemented', 'partially_implemented', 'planned', 'not_implemented', 'not_applicable'))
                """
            )
        )
        logger.info("Migration: added answer constraint to questionnaire_responses")


def run_column_migrations(engine):
    """Add new nullable columns to existing tables if they don't exist yet."""
    inspector = inspect(engine)
    migrations = {
        "assessments": [
            ("scope_answers", "TEXT"),
            ("applicable_requirements", "TEXT"),
            ("context_answers", "TEXT"),
            ("context_profile", "TEXT"),
            ("desk_review_status", "TEXT"),
            ("selected_frameworks", "TEXT"),
            ("screening_status", "TEXT"),
            ("screening_results", "TEXT"),
            ("review_status", "VARCHAR(20)"),
        ],
        "questionnaire_responses": [
            ("na_reason", "TEXT"),
            ("confidence", "TEXT"),
            ("cluster_id", "TEXT"),
            ("answer_source", "VARCHAR(20) DEFAULT 'human'"),
        ],
        "gap_items": [
            ("maturity_level", "INTEGER"),
            ("root_cause_category", "TEXT"),
            ("evidence_quote", "TEXT"),
            ("evidence_confidence", "TEXT"),
            ("framework_id", "TEXT"),
            ("cluster_id", "TEXT"),
            ("control_reference", "TEXT"),
            ("remediation_status", "VARCHAR(20) DEFAULT 'open'"),
            ("remediation_owner", "VARCHAR(255)"),
            ("remediation_target_date", "DATETIME"),
            ("remediation_notes", "TEXT"),
            ("remediation_closed_at", "DATETIME"),
            ("review_status", "VARCHAR(20) DEFAULT 'draft'"),
            ("needs_review", "BOOLEAN DEFAULT 0"),
            ("ai_compliance_status", "TEXT"),
            ("ai_gap_description", "TEXT"),
            ("ai_risk_level", "VARCHAR(20)"),
            ("reviewer_notes", "TEXT"),
            ("reviewed_by", "VARCHAR(255)"),
            ("reviewed_at", "DATETIME"),
        ],
        "gap_reports": [
            ("framework_scores", "TEXT"),
            ("legacy_history", "TEXT"),
        ],
        "desk_review_summaries": [
            ("legacy_history", "TEXT"),
        ],
    }
    with engine.begin() as conn:
        for table_name, columns in migrations.items():
            if not inspector.has_table(table_name):
                continue
            existing = {col["name"] for col in inspector.get_columns(table_name)}
            for col_name, col_type in columns:
                if col_name not in existing:
                    conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"))
                    logger.info(f"Migration: added {col_name} to {table_name}")
        if inspector.has_table("questionnaire_responses"):
            ensure_questionnaire_answer_constraint(conn)
        if inspector.has_table("gap_items"):
            conn.execute(
                text(
                    """
                    UPDATE gap_items
                    SET ai_compliance_status = compliance_status,
                        ai_gap_description = gap_description,
                        ai_risk_level = risk_level
                    WHERE ai_compliance_status IS NULL
                    """
                )
            )
            conn.execute(
                text(
                    """
                    CREATE INDEX IF NOT EXISTS ix_gap_items_null_framework_id
                    ON gap_items (id) WHERE framework_id IS NULL
                    """
                )
            )
            conn.execute(
                text(
                    """
                    UPDATE gap_items
                    SET framework_id = 'dpdpa'
                    WHERE framework_id IS NULL
                    """
                )
            )


def _rebuild_table_for_fks(cursor, table_name, dialect, table):
    """Rebuild a single table to enforce FK constraints, using `table` (a
    caller-supplied, frozen `sqlalchemy.Table`) as the target DDL.

    `table` must be frozen schema owned by the caller -- e.g.
    `app.legacy_migrations_schema.FROZEN_TABLES` for the historical Alembic
    retrofit revision -- never a live lookup of `Base.metadata` at
    migration runtime. A historical migration must keep producing the same
    DDL forever, independent of how the ORM models evolve afterward.
    """
    cursor.execute(f"PRAGMA table_info({table_name})")
    existing_cols = {row[1] for row in cursor.fetchall()}
    common_cols = [c.name for c in table.columns if c.name in existing_cols]
    col_list = ", ".join(common_cols)

    cursor.execute(f"ALTER TABLE {table_name} RENAME TO _{table_name}_pre_fk")
    create_ddl = str(CreateTable(table).compile(dialect=dialect))
    cursor.execute(create_ddl)
    cursor.execute(f"INSERT INTO {table_name} ({col_list}) SELECT {col_list} FROM _{table_name}_pre_fk")
    cursor.execute(f"DROP TABLE _{table_name}_pre_fk")

    for idx in table.indexes:
        idx_sql = str(CreateIndex(idx).compile(dialect=dialect))
        idx_sql = idx_sql.replace("CREATE INDEX", "CREATE INDEX IF NOT EXISTS", 1)
        cursor.execute(idx_sql)

    logger.info("Migration: rebuilt %s with foreign key constraints", table_name)


def compute_fk_tables_to_rebuild(engine) -> list[str]:
    """Read-only: which tables are missing the intended FK set. No writes.

    Split out from the old combined `_ensure_foreign_keys` so callers can
    run this (and the orphan preflight below) *before* any destructive
    migration step, rather than discovering an orphan mid-migration after
    other writes have already landed.
    """
    if engine.dialect.name != "sqlite":
        return []

    dbapi_conn = engine.raw_connection()
    try:
        cursor = dbapi_conn.cursor()
        tables_to_rebuild: list[str] = []
        for table_name in FK_REBUILD_ORDER:
            cursor.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
            )
            if not cursor.fetchone():
                continue

            cursor.execute(f"PRAGMA foreign_key_list({table_name})")
            existing_fks = cursor.fetchall()
            existing_fk_set = {(row[3], row[2], row[4], row[6]) for row in existing_fks}

            for child_col, parent_table, parent_col, on_delete in FK_SPEC[table_name]:
                expected_on_delete = on_delete or "NO ACTION"
                if (child_col, parent_table, parent_col, expected_on_delete) not in existing_fk_set:
                    tables_to_rebuild.append(table_name)
                    break

        return tables_to_rebuild
    finally:
        dbapi_conn.close()


def preflight_fk_orphans(engine) -> None:
    """Read-only: raise RuntimeError if any table covered by FK_SPEC has
    orphaned rows on a non-SET-NULL column.

    Checks every FK_SPEC table that exists in the database, not only
    tables slated for an FK rebuild this run: a table that already has its
    expected FK declared can still carry a non-SET-NULL orphan (e.g. one
    written while FK enforcement was off), and that orphan must block the
    migration even though it isn't the table being rebuilt. Without this,
    a rebuild of a *different* table could commit, and `PRAGMA
    foreign_key_check` would only catch the pre-existing orphan afterward
    — too late to leave the database untouched on abort.

    Must run — and fully complete — before any destructive migration step
    (column adds, questionnaire cleanup/backfill, or the FK rebuild itself)
    so that an abort here leaves the database completely untouched and the
    migration unrecorded, rather than partially applied.
    """
    if engine.dialect.name != "sqlite":
        return

    dbapi_conn = engine.raw_connection()
    try:
        cursor = dbapi_conn.cursor()
        for table_name in FK_REBUILD_ORDER:
            cursor.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
            )
            if not cursor.fetchone():
                continue

            for child_col, parent_table, parent_col, on_delete in FK_SPEC[table_name]:
                if on_delete == "SET NULL":
                    continue
                cursor.execute(
                    f"SELECT COUNT(*) FROM {table_name} c "
                    f"LEFT JOIN {parent_table} p ON c.{child_col} = p.{parent_col} "
                    f"WHERE p.{parent_col} IS NULL AND c.{child_col} IS NOT NULL"
                )
                orphan_count = cursor.fetchone()[0]
                if orphan_count:
                    raise RuntimeError(
                        f"FK migration blocked: {table_name}.{child_col} has {orphan_count} "
                        f"orphaned rows referencing non-existent {parent_table}.{parent_col}. "
                        f"Run 'python scripts/detect_orphans.py' for details and fix manually."
                    )
    finally:
        dbapi_conn.close()


def apply_fk_rebuild(engine, tables_to_rebuild: list[str], frozen_tables: dict) -> None:
    """Perform the actual FK retrofit (SET NULL cleanup + table rebuild),
    then unconditionally verify full FK integrity.

    Assumes `preflight_fk_orphans` has already been run and did not raise.

    `frozen_tables` maps table name -> a frozen `sqlalchemy.Table` for
    every table that may need a rebuild. The caller owns freezing this
    (see app.legacy_migrations_schema.FROZEN_TABLES for the historical
    Alembic revision) -- this function never reads live ORM metadata.

    The `PRAGMA foreign_key_check` at the end always runs, even when
    `tables_to_rebuild` is empty (a retry after a table was already fixed,
    or a database that already has every intended FK). Every retry is an
    integrity boundary: a database must never be recorded as Alembic head
    while an FK violation remains, whether or not this particular run
    needed to rebuild anything.

    Runs the rebuild transaction under `PRAGMA legacy_alter_table=ON`: SQLite's
    default `ALTER TABLE ... RENAME` behavior rewrites the FK clause of every
    OTHER table that references the table being renamed to point at its new
    name. `_rebuild_table_for_fks` renames the table being rebuilt to
    `_{table_name}_pre_fk` and later drops it -- so without this pragma, a
    sibling table that already has its correct FK to the table being
    rebuilt (and is therefore NOT itself in `tables_to_rebuild`) would have
    that FK silently rewritten to reference the soon-to-be-dropped temp
    table, leaving it dangling the moment this (non-transactional, SQLite
    DDL) transaction commits.
    """
    if engine.dialect.name != "sqlite":
        return

    dbapi_conn = engine.raw_connection()
    try:
        cursor = dbapi_conn.cursor()

        if tables_to_rebuild:
            cursor.execute("PRAGMA foreign_keys=OFF")
            # SQLite's default ALTER TABLE ... RENAME behavior rewrites the
            # FK clause of every OTHER table that references the table being
            # renamed, to point at its new (temporary) name. _rebuild_table_
            # for_fks renames a table to `_{table_name}_pre_fk`, recreates it
            # under its original name, then drops the temp table -- so
            # without this pragma, a sibling table that already has a
            # correct FK to the table being rebuilt (and is therefore NOT
            # itself in tables_to_rebuild) ends up with its FK silently
            # rewritten to reference `_{table_name}_pre_fk`, which is then
            # dropped -- leaving that sibling with a dangling FK the moment
            # this transaction commits. `legacy_alter_table=ON` disables
            # that cross-table rewrite, so a sibling's FK clause keeps
            # referencing the table by its original (soon to be restored)
            # name throughout the rebuild.
            cursor.execute("PRAGMA legacy_alter_table=ON")
            cursor.execute("BEGIN")

            for table_name in tables_to_rebuild:
                for child_col, parent_table, parent_col, on_delete in FK_SPEC[table_name]:
                    if on_delete == "SET NULL":
                        cursor.execute(
                            f"UPDATE {table_name} SET {child_col} = NULL "
                            f"WHERE {child_col} IS NOT NULL AND {child_col} NOT IN "
                            f"(SELECT {parent_col} FROM {parent_table})"
                        )

                _rebuild_table_for_fks(cursor, table_name, engine.dialect, frozen_tables[table_name])

            cursor.execute("COMMIT")
            cursor.execute("PRAGMA legacy_alter_table=OFF")
            cursor.execute("PRAGMA foreign_keys=ON")

        cursor.execute("PRAGMA foreign_key_check")
        violations = cursor.fetchall()
        if violations:
            logger.error("FK violations after migration: %s", violations)
            raise RuntimeError(
                f"Foreign key violations detected after migration: {violations}"
            )

        if tables_to_rebuild:
            logger.info(
                "Migration: FK enforcement verified for %s",
                ", ".join(tables_to_rebuild),
            )
        else:
            logger.info("Migration: FK enforcement verified (no tables required rebuilding)")
    finally:
        dbapi_conn.close()
        engine.dispose()


def run_fk_retrofit(engine, frozen_tables: dict | None = None):
    """Convenience wrapper: compute + preflight + apply in one call.

    Kept for direct callers/tests that want the old combined behavior in
    isolation. The Alembic revision itself calls the three steps separately
    so the orphan preflight can run before `run_column_migrations`.

    `frozen_tables` defaults to `app.legacy_migrations_schema.FROZEN_TABLES`
    (the frozen DDL owned by the historical retrofit revision). Callers may
    pass their own mapping, but this function never derives one from live
    ORM metadata itself.
    """
    if engine.dialect.name != "sqlite":
        return
    if frozen_tables is None:
        from app.legacy_migrations_schema import FROZEN_TABLES

        frozen_tables = FROZEN_TABLES
    tables_to_rebuild = compute_fk_tables_to_rebuild(engine)
    preflight_fk_orphans(engine)
    apply_fk_rebuild(engine, tables_to_rebuild, frozen_tables)
