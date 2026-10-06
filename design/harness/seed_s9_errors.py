"""S9 group-A seed metadata for error and empty-state previews."""

from __future__ import annotations

SCREEN_STATES = {
    "b7-404": ("page", "engagement"),
    "b7-500": ("error", "down", "upstream"),
    "b7-empty-states": (
        "engagements",
        "evidence",
        "review",
        "search",
        "findings",
        "report",
    ),
}


def apply(db, screen, state, assessment, engagement, data):
    if screen == "b7-empty-states":
        return {
            "data_state": "database",
            "note": "The empty states use the existing live S3-S8 page routes; no finished state was rebuilt.",
        }
    return {
        "data_state": "preview-state",
        "note": "Error copy and support reference rendered by the preview fixture.",
    }


def route(screen, state, assessment_id):
    return f"/design/pages/{screen}?state={state}&assessment_id={assessment_id}"
