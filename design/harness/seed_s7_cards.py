"""Seed metadata for the deterministic S7 cards previews."""

SCREEN_STATES = {
    "b5-requirement-card": ("v2", "v2-draft", "contradiction", "v1", "none"),
    "b5-conclusion-card": ("pending", "edit", "approved", "edited", "rejected", "blocked", "no-citation", "superseded", "locked", "conflict", "bulk"),
    "b5-recommended-action": ("empty", "drafting", "drafted", "edited", "error", "saved", "gaps-required", "limit", "stale", "not-open", "not-draftable"),
}


def apply(db, screen, state, assessment, engagement, data):
    """Keep in-flight card and toast states explicit preview states."""
    return {"data_state": "preview-state", "note": f"Rendered by design_s7_cards for {screen}:{state}"}


def route(screen, state, assessment_id) -> str:
    return f"/design/pages/{screen}?state={state}&assessment_id={assessment_id}"
