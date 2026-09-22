import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text
from sqlalchemy.schema import CreateIndex, CreateTable
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.database import Base, engine
import app.models  # noqa: F401 — ensure all models registered before create_all
from app.routers import analysis, assessments, desk_review, documents, questionnaire, remediation, reports, review, web

logger = logging.getLogger(__name__)

APP_DIR = Path(__file__).resolve().parent
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


def _ensure_questionnaire_answer_constraint(conn):
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


def _run_migrations(engine):
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
            _ensure_questionnaire_answer_constraint(conn)
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


_FK_SPEC: dict[str, list[tuple[str, str, str, str | None]]] = {
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

_FK_REBUILD_ORDER = [
    "assessment_documents",
    "gap_reports",
    "gap_items",
    "initiatives",
    "desk_review_summaries",
    "desk_review_findings",
    "rfi_documents",
    "questionnaire_responses",
]


def _rebuild_table_for_fks(cursor, table_name, dialect):
    """Rebuild a single table using the SQLAlchemy model DDL to enforce FK constraints."""
    table = Base.metadata.tables[table_name]

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


def _ensure_foreign_keys(engine):
    """Rebuild tables missing FK constraints on legacy SQLite databases.

    Uses a raw DBAPI connection with PRAGMA foreign_keys=OFF so that the
    rename-create-copy-drop cycle is safe.  Runs an orphan preflight before
    any schema change; aborts if orphaned rows would violate a non-nullable FK.
    """
    if engine.dialect.name != "sqlite":
        return

    dbapi_conn = engine.raw_connection()
    try:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=OFF")

        tables_to_rebuild: list[str] = []
        for table_name in _FK_REBUILD_ORDER:
            cursor.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
            )
            if not cursor.fetchone():
                continue

            cursor.execute(f"PRAGMA foreign_key_list({table_name})")
            existing_fks = cursor.fetchall()
            existing_fk_set = {(row[3], row[2], row[4]) for row in existing_fks}

            for child_col, parent_table, parent_col, _on_delete in _FK_SPEC[table_name]:
                if (child_col, parent_table, parent_col) not in existing_fk_set:
                    tables_to_rebuild.append(table_name)
                    break

        if not tables_to_rebuild:
            return

        for table_name in tables_to_rebuild:
            for child_col, parent_table, parent_col, on_delete in _FK_SPEC[table_name]:
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

        cursor.execute("BEGIN")

        for table_name in tables_to_rebuild:
            for child_col, parent_table, parent_col, on_delete in _FK_SPEC[table_name]:
                if on_delete == "SET NULL":
                    cursor.execute(
                        f"UPDATE {table_name} SET {child_col} = NULL "
                        f"WHERE {child_col} IS NOT NULL AND {child_col} NOT IN "
                        f"(SELECT {parent_col} FROM {parent_table})"
                    )

            _rebuild_table_for_fks(cursor, table_name, engine.dialect)

        cursor.execute("COMMIT")

        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA foreign_key_check")
        violations = cursor.fetchall()
        if violations:
            logger.error("FK violations after migration: %s", violations)
            raise RuntimeError(
                f"Foreign key violations detected after migration: {violations}"
            )

        logger.info(
            "Migration: FK enforcement verified for %s",
            ", ".join(tables_to_rebuild),
        )
    finally:
        dbapi_conn.close()
        engine.dispose()


def _register_frameworks():
    """Register all available compliance frameworks."""
    from app.frameworks.definitions.dpdpa import DPDPA_DEFINITION
    from app.frameworks.definitions.gdpr import GDPR_DEFINITION
    from app.frameworks.definitions.hipaa import HIPAA_DEFINITION
    from app.frameworks.definitions.iso27001 import ISO27001_DEFINITION
    from app.frameworks.definitions.nist_csf import NIST_CSF_DEFINITION
    from app.frameworks.definitions.pci_dss import PCI_DSS_DEFINITION
    from app.frameworks.registry import FrameworkRegistry

    FrameworkRegistry.register(DPDPA_DEFINITION)
    FrameworkRegistry.register(ISO27001_DEFINITION)
    FrameworkRegistry.register(GDPR_DEFINITION)
    FrameworkRegistry.register(HIPAA_DEFINITION)
    FrameworkRegistry.register(NIST_CSF_DEFINITION)
    FrameworkRegistry.register(PCI_DSS_DEFINITION)


def _assert_framework_catalog_complete() -> None:
    """Fail startup when registered frameworks drift from the UI catalog."""
    from app.frameworks.registry import FrameworkRegistry

    enabled_ids = web.ENABLED_ASSESSMENT_FRAMEWORKS
    roadmap_ids = web.ROADMAP_FRAMEWORKS
    duplicate_enabled = sorted(
        framework_id
        for framework_id in set(enabled_ids)
        if enabled_ids.count(framework_id) > 1
    )
    duplicate_roadmap = sorted(
        framework_id
        for framework_id in set(roadmap_ids)
        if roadmap_ids.count(framework_id) > 1
    )
    catalog_overlap = sorted(set(enabled_ids) & set(roadmap_ids))
    if duplicate_enabled or duplicate_roadmap or catalog_overlap:
        raise RuntimeError(
            "Framework UI catalog contains duplicate or conflicting entries: "
            f"duplicates_in_enabled={duplicate_enabled}, "
            f"duplicates_in_roadmap={duplicate_roadmap}, "
            f"enabled_roadmap_overlap={catalog_overlap}"
        )

    catalog_ids = set(enabled_ids) | set(roadmap_ids)
    registered_ids = set(FrameworkRegistry.all_ids())
    if catalog_ids != registered_ids:
        raise RuntimeError(
            "Framework registry and UI catalog differ: "
            f"missing_from_ui={sorted(registered_ids - catalog_ids)}, "
            f"missing_from_registry={sorted(catalog_ids - registered_ids)}"
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _register_frameworks()
    _assert_framework_catalog_complete()
    _run_migrations(engine)
    _ensure_foreign_keys(engine)
    yield


app = FastAPI(
    title=settings.firm_name,
    description="AI-powered multi-framework compliance maturity assessment platform (DPDPA, ISO 27001, GDPR, HIPAA, NIST CSF, PCI-DSS)",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(SessionMiddleware, secret_key=settings.session_secret)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")

# API routes
app.include_router(assessments.router)
app.include_router(questionnaire.router)
app.include_router(documents.router)
app.include_router(analysis.router)
app.include_router(reports.router)
app.include_router(reports.comparison_router)
app.include_router(desk_review.router)
app.include_router(remediation.router)
app.include_router(review.router)

# Web portal routes
app.include_router(web.router)


@app.get("/login", include_in_schema=False)
def login(request: Request):
    """Keep legacy entry links working for the current no-auth deployment."""
    return RedirectResponse(url=request.url_for("dashboard"), status_code=307)


@app.get("/health")
def health():
    return {"status": "ok"}
