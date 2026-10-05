from urllib.parse import unquote

from starlette.requests import Request

from app.routers.design import PREVIEW_PAGES
from app.routers.design_s7_cards import SCREEN_STATES, _render


def request_for(state: str) -> Request:
    return Request({"type": "http", "method": "GET", "path": "/design/pages/b5", "query_string": f"state={state}".encode(), "headers": []})


def body(screen: str, state: str) -> str:
    return _render(request_for(state), screen, state).body.decode()


def test_cards_preview_registry_and_state_matrix():
    assert set(SCREEN_STATES) <= set(PREVIEW_PAGES)
    assert len(SCREEN_STATES["b5-requirement-card"]) == 5
    assert len(SCREEN_STATES["b5-conclusion-card"]) == 11
    assert {"empty", "drafting", "drafted", "edited", "error", "saved"} <= set(SCREEN_STATES["b5-recommended-action"])


def test_requirement_states_preserve_card_contracts():
    for state in SCREEN_STATES["b5-requirement-card"]:
        html = body("b5-requirement-card", state)
        assert 'data-requirement-card' in html
        assert 'data-requirement-source=' in html
        assert 'data-claim-link="F1"' in html or state in {"none", "v1"}
    assert "No analysis run is linked to this conclusion." in body("b5-requirement-card", "none")
    assert "✗" in body("b5-requirement-card", "contradiction")


def test_conclusion_states_render_one_card_and_one_primary_action_maximum():
    for state in SCREEN_STATES["b5-conclusion-card"]:
        html = body("b5-conclusion-card", state)
        assert html.count('data-conclusion-card') == 1
        assert 'id="conclusion-card-conclusion-s7"' in html
        # The blocked state is intentionally non-approvable; every other state has
        # either a primary decision or a non-primary reopen/edit action.
        if state == "blocked":
            assert 'class="btn primary"' not in html
    assert "Legacy bulk approval, not individually reviewed" in body("b5-conclusion-card", "bulk")
    assert "superseded version" in body("b5-conclusion-card", "superseded").lower()


def test_recommended_action_states_and_toast_headers():
    for state in SCREEN_STATES["b5-recommended-action"]:
        response = _render(request_for(state), "b5-recommended-action", state)
        html = response.body.decode()
        assert 'data-recommended-action-field' in html
        assert 'data-remediation-draft-button' in html
        if state in {"gaps-required", "limit", "stale", "not-open", "not-draftable"}:
            assert response.headers["X-Toast-Type"] == "error"
            assert unquote(response.headers["X-Toast-Message"])
        else:
            assert "X-Toast-Message" not in response.headers
    assert "AI draft" in body("b5-recommended-action", "drafted")
    assert "Drafting…" in body("b5-recommended-action", "drafting")
    assert "The AI draft could not be produced" in body("b5-recommended-action", "error")
