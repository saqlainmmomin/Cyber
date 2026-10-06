import logging
import re
import secrets
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from alembic import command
from alembic.config import Config
from fastapi import Depends, FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app import database
from app.routers import (
    analysis,
    assessments,
    aws,
    board_inputs,
    conclusions,
    design,
    desk_review,
    drafting,
    documents,
    evidence,
    evidence_reuse,
    findings,
    firm_settings as firm_settings_router,
    integrated_reports,
    magic,
    questionnaire,
    reports,
    requirement_review,
    review,
    retention as retention_router,
    snapshots,
    soa as soa_router,
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
app.include_router(drafting.router, dependencies=_ARCHIVE_GUARD)
app.include_router(review.router, dependencies=_ARCHIVE_GUARD)
app.include_router(conclusions.router, dependencies=_ARCHIVE_GUARD)
app.include_router(requirement_review.router, dependencies=_ARCHIVE_GUARD)
app.include_router(findings.router, dependencies=_ARCHIVE_GUARD)
app.include_router(snapshots.router, dependencies=_ARCHIVE_GUARD)
app.include_router(soa_router.router, dependencies=_ARCHIVE_GUARD)
app.include_router(board_inputs.router, dependencies=_ARCHIVE_GUARD)
app.include_router(integrated_reports.router, dependencies=_ARCHIVE_GUARD)
app.include_router(retention_router.router)
app.include_router(firm_settings_router.router, dependencies=_ARCHIVE_GUARD)  # no engagement in its paths: a no-op guard
app.include_router(design.router)

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


_ENGAGEMENT_PATH = re.compile(r"^/engagements/[^/]+(?:/|$)")


def _reference_code() -> str:
    token = secrets.token_hex(6)
    return "-".join(token[index : index + 4] for index in range(0, 12, 4))


def _wants_json(request: Request) -> bool:
    accept = request.headers.get("accept", "").casefold()
    path = request.url.path
    return path == "/api" or path.startswith("/api/") or "application/json" in accept


def _error_context(request: Request, *, variant: str, reference_code: str) -> dict:
    variants = {
        "page": {
            "crumb": "Page not found",
            "heading": "Page not found",
            "message": "The page may have moved, or the link is out of date.",
            "icon_id": "search",
            "primary_label": "Go to home",
            "primary_href": "/",
            "primary_icon_id": "home",
            "secondary_label": "Go back",
            "secondary_href": "/",
            "secondary_action": "back",
        },
        "engagement": {
            "crumb": "Engagement not found",
            "heading": "Engagement not found",
            "message": "It may have been archived or deleted. Check the engagement list for what is current.",
            "icon_id": "briefcase",
            "primary_label": "View engagements",
            "primary_href": "/engagements",
            "primary_icon_id": "briefcase",
            "secondary_label": "Go back",
            "secondary_href": "/",
            "secondary_action": "back",
        },
        "error": {
            "crumb": "Something went wrong",
            "heading": "This page couldn't be loaded",
            "message": "Something failed on our side. Try again in a moment. If it keeps happening, send the reference to support.",
            "icon_id": "alert",
            "primary_label": "Try again",
            "primary_icon_id": "rotate",
            "primary_action": "retry",
            "primary_href": "/",
            "secondary_label": "Go to home",
            "secondary_href": "/",
        },
    }
    selected = variants.get(variant, variants["error"])
    previous_href = _safe_referrer(request)
    if selected.get("secondary_action") == "back":
        selected = {**selected, "secondary_href": previous_href}
    if selected.get("primary_action") == "retry":
        selected = {**selected, "primary_href": previous_href}
    return {
        "request": request,
        "reference_code": reference_code,
        "variant": variant,
        **selected,
    }


def _safe_referrer(request: Request) -> str:
    """Return a same-origin, path-only referrer for error-page fallbacks."""
    raw_referrer = request.headers.get("referer")
    if not raw_referrer:
        return "/"
    parsed = urlsplit(raw_referrer)
    if parsed.scheme and parsed.scheme not in {"http", "https"}:
        return "/"
    if parsed.netloc and parsed.netloc != request.url.netloc:
        return "/"
    if not parsed.path.startswith("/") or parsed.path.startswith("//"):
        return "/"
    return urlunsplit(("", "", parsed.path or "/", parsed.query, ""))


def _log_error_page(request: Request, exc: Exception, reference_code: str, *, server_error: bool) -> None:
    message = "error_page reference=%s path=%r exception=%s"
    values = (reference_code, request.scope.get("raw_path", request.url.path), type(exc).__name__)
    if server_error and getattr(exc, "__traceback__", None) is not None:
        logger.error(message, *values, exc_info=(type(exc), exc, exc.__traceback__))
    else:
        logger.warning(message, *values)


async def _http_error_page(request: Request, exc: StarletteHTTPException):
    if exc.status_code not in {404, 500} or _wants_json(request):
        return await http_exception_handler(request, exc)
    reference_code = _reference_code()
    _log_error_page(request, exc, reference_code, server_error=exc.status_code >= 500)
    variant = "engagement" if _ENGAGEMENT_PATH.match(request.url.path) else "page"
    if exc.status_code == 500:
        variant = "error"
    return web.templates.TemplateResponse(
        request=request,
        name="pages/error.html",
        context=_error_context(request, variant=variant, reference_code=reference_code),
        status_code=exc.status_code,
    )


async def _unhandled_error_page(request: Request, exc: Exception):
    reference_code = _reference_code()
    _log_error_page(request, exc, reference_code, server_error=True)
    if _wants_json(request):
        return JSONResponse({"detail": "Internal Server Error"}, status_code=500)
    return web.templates.TemplateResponse(
        request=request,
        name="pages/error.html",
        context=_error_context(request, variant="error", reference_code=reference_code),
        status_code=500,
    )


app.add_exception_handler(StarletteHTTPException, _http_error_page)
app.add_exception_handler(Exception, _unhandled_error_page)
