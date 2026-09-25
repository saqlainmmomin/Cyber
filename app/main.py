import logging
from contextlib import asynccontextmanager
from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app import database
from app.routers import (
    analysis,
    assessments,
    aws,
    conclusions,
    desk_review,
    documents,
    evidence,
    evidence_reuse,
    findings,
    integrated_reports,
    magic,
    questionnaire,
    reports,
    review,
    retention as retention_router,
    snapshots,
    web,
)
from app.services.magic_links import MagicTokenRedactionFilter
from app.services.run_recovery import recover_interrupted_work

logger = logging.getLogger(__name__)

_magic_token_redaction_filter = MagicTokenRedactionFilter()
for _logger_name in ("uvicorn.access", "uvicorn.error"):
    logging.getLogger(_logger_name).addFilter(_magic_token_redaction_filter)

APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parent


def _database_engine_matches_settings() -> bool:
    """Avoid recovery touching a developer DB after tests swap ``DATABASE_URL``."""
    return database.engine.url.render_as_string(hide_password=False) == settings.database_url


def _run_alembic_upgrade():
    """Bring the database schema to head via Alembic (replaces the old DIY migration path)."""
    alembic_cfg = Config(str(REPO_ROOT / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    command.upgrade(alembic_cfg, "head")


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
    _run_alembic_upgrade()
    _register_frameworks()
    _assert_framework_catalog_complete()
    if settings.recover_interrupted_on_startup and _database_engine_matches_settings():
        recover_interrupted_work()
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

_ARCHIVE_GUARD = [Depends(retention_router.archive_write_guard)]

# API routes
app.include_router(assessments.router, dependencies=_ARCHIVE_GUARD)
app.include_router(questionnaire.router, dependencies=_ARCHIVE_GUARD)
app.include_router(documents.router, dependencies=_ARCHIVE_GUARD)
app.include_router(evidence.router, dependencies=_ARCHIVE_GUARD)
app.include_router(analysis.router, dependencies=_ARCHIVE_GUARD)
app.include_router(reports.router, dependencies=_ARCHIVE_GUARD)
app.include_router(reports.comparison_router, dependencies=_ARCHIVE_GUARD)
app.include_router(desk_review.router, dependencies=_ARCHIVE_GUARD)
app.include_router(review.router, dependencies=_ARCHIVE_GUARD)
app.include_router(conclusions.router, dependencies=_ARCHIVE_GUARD)
app.include_router(findings.router, dependencies=_ARCHIVE_GUARD)
app.include_router(snapshots.router, dependencies=_ARCHIVE_GUARD)
app.include_router(integrated_reports.router, dependencies=_ARCHIVE_GUARD)
app.include_router(retention_router.router)

# Web portal routes
app.include_router(aws.router, dependencies=_ARCHIVE_GUARD)
app.include_router(evidence_reuse.router, dependencies=_ARCHIVE_GUARD)
app.include_router(magic.router, dependencies=_ARCHIVE_GUARD)
app.include_router(web.router, dependencies=_ARCHIVE_GUARD)


@app.get("/login", include_in_schema=False)
def login(request: Request):
    """Keep legacy entry links working for the current no-auth deployment."""
    return RedirectResponse(url=request.url_for("dashboard"), status_code=307)


@app.get("/health")
def health():
    return {"status": "ok"}
