"""Debug-only S9 previews for shared system behaviour and components."""

from __future__ import annotations

from fastapi import HTTPException, Request

from app.routers import design
from app.routers.web import templates


SCREEN_STATES = {
    "b7-toasts": ("default",),
    "b7-skeleton-table": ("loading", "loaded"),
    "b7-skeleton-detail": ("loading", "loaded"),
    "b7-htmx-swaps": ("ok", "bad"),
    "b7-modals": ("delete", "purge", "send", "invite", "discard", "failed"),
    "b7-menus-popovers": ("default",),
    "b7-mobile-shell": ("default",),
}

TITLES = {
    "b7-toasts": "Toasts",
    "b7-skeleton-table": "Loading skeleton, table page",
    "b7-skeleton-detail": "Loading skeleton, detail page",
    "b7-htmx-swaps": "HTMX swap states",
    "b7-modals": "Modals and confirm dialogs",
    "b7-menus-popovers": "Menus and popovers",
    "b7-mobile-shell": "Mobile app shell",
}


def _preview(request: Request, screen: str):
    state = request.query_params.get("state", SCREEN_STATES[screen][0])
    if state not in SCREEN_STATES[screen]:
        raise HTTPException(status_code=404, detail="Unknown state")
    return templates.TemplateResponse(
        "pages/design_s9_system.html",
        {
            "request": request,
            "screen": screen,
            "state": state,
            "title": TITLES[screen],
            "dark": "dark" in request.query_params,
        },
    )


for _screen in SCREEN_STATES:
    design.PREVIEW_PAGES[_screen] = lambda request, screen=_screen: _preview(request, screen)
