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


def _run_migrations(engine):
    """Add new nullable columns to existing tables if they don't exist yet."""
    inspector = inspect(engine)
    migrations = {
        "assessments": [
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
