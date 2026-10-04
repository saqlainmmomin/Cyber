"""Debug-only Yozora component gallery and template preview routes."""

from collections.abc import Callable

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.routers.web import templates

router = APIRouter(tags=["design"])

# Later slices register preview pages here (for example the unrouted sign-in
# placeholder). S2 deliberately keeps the registry empty.
PREVIEW_PAGES: dict[str, Callable[[Request], Response]] = {}


def login_preview(request: Request) -> Response:
    state = request.query_params.get("state", "default")
    if state not in {"default", "error", "loading"}:
        state = "default"
    return templates.TemplateResponse(
        "pages/login.html",
        {"request": request, "preview_state": state},
    )


PREVIEW_PAGES["login"] = login_preview


def _debug_only() -> None:
    if settings.env.casefold() == "production":
        raise HTTPException(status_code=404, detail="Not found")


@router.get("/design", response_class=HTMLResponse, include_in_schema=False)
def design_gallery(request: Request) -> Response:
    _debug_only()
    return templates.TemplateResponse(
        "pages/design.html",
        {
            "request": request,
            "dark": "dark" in request.query_params,
            "focus": "focus" in request.query_params,
        },
    )


@router.get("/design/pages/{name}", response_class=HTMLResponse, include_in_schema=False)
def design_preview(request: Request, name: str, db: Session = Depends(get_db)) -> Response:
    _debug_only()
    preview = PREVIEW_PAGES.get(name)
    if preview is None:
        raise HTTPException(status_code=404, detail="Not found")
    return preview(request)
