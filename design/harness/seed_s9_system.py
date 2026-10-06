"""Deterministic S9 system-component preview metadata."""

from __future__ import annotations

SCREEN_STATES = {
    "b7-toasts": ("default",),
    "b7-skeleton-table": ("loading", "loaded"),
    "b7-skeleton-detail": ("loading", "loaded"),
    "b7-htmx-swaps": ("ok", "bad"),
    "b7-modals": ("delete", "purge", "send", "invite", "discard", "failed"),
    "b7-menus-popovers": ("default",),
    "b7-mobile-shell": ("default",),
}


def apply(db, screen: str, state: str, assessment, engagement, data) -> dict:
    """Keep system states preview-only; no fixture rows are needed."""
    assessment.name = "Head office"
    assessment.company_name = "Meridian Ledger Technologies"
    return {"data_state": "preview-state", "note": f"Rendered by design_s9_system for {screen}:{state}."}


def route(screen: str, state: str, assessment_id: str) -> str:
    return f"/design/pages/{screen}?state={state}"

