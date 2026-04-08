import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.database import Base, engine
import app.models  # noqa: F401 — ensure all models registered before create_all
from app.routers import analysis, assessments, desk_review, documents, questionnaire, reports, web

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
                    submitted_at DATETIME NOT NULL,
                    CONSTRAINT ck_questionnaire_responses_answer_valid
                        CHECK (answer IN ('fully_implemented', 'partially_implemented', 'planned', 'not_implemented', 'not_applicable'))
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO questionnaire_responses (
                    id, assessment_id, question_id, answer, notes, evidence_reference, na_reason, confidence, submitted_at
                )
                SELECT
                    id, assessment_id, question_id, answer, notes, evidence_reference, na_reason, confidence, submitted_at
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
        ],
        "questionnaire_responses": [
            ("na_reason", "TEXT"),
            ("confidence", "TEXT"),
        ],
        "gap_items": [
            ("maturity_level", "INTEGER"),
            ("root_cause_category", "TEXT"),
            ("evidence_quote", "TEXT"),
            ("evidence_confidence", "TEXT"),
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _run_migrations(engine)
    yield


app = FastAPI(
    title="DPDPA Gap Assessment Tool",
    description="AI-powered compliance gap assessment against India's Digital Personal Data Protection Act",
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
app.include_router(desk_review.router)

# Web portal routes
app.include_router(web.router)


@app.get("/health")
def health():
    return {"status": "ok"}
