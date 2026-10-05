"""Focused contracts for the S7 narrative and board-input pages."""

from __future__ import annotations

import importlib
import re
from pathlib import Path
from urllib.parse import unquote

from tests.p6_10_support import (  # noqa: F401 - fixtures are used by name
    REVIEWER,
    _register_frameworks,
    db,
    db_path,
    engine,
    gate,
    http,
    released_assessment,
)


TEMPLATE_ROOT = Path(__file__).resolve().parents[1] / "app" / "templates" / "pages"


def _report_labels(html: str) -> list[str]:
    row = re.search(r'<div class="seg">(.*?)</div>', html, re.DOTALL)
    assert row, "report segmented row missing"
    return re.findall(r'<button[^>]*>([^<]+)</button>', row.group(1))


def test_narrative_and_board_pages_keep_report_row_and_live_contracts(
    db, http, gate, monkeypatch
):
    assessment, *_ = released_assessment(db, http, gate, monkeypatch)

    narrative = http.get(f"/assessments/{assessment.id}/narrative")
    assert narrative.status_code == 200
    assert _report_labels(narrative.text) == [
        "Report",
        "Versions",
        "Applicability",
        "Narrative",
        "Board inputs",
    ]
    assert 'data-narrative-section="executive"' in narrative.text
    assert 'data-narrative-accept-form' in narrative.text
    assert 'hx-post="/api/assessments/' in narrative.text
    assert 'data-finding-ref="F1"' in narrative.text
    assert 'data-narrative-unreleased' not in narrative.text  # released here


    board = http.get(f"/assessments/{assessment.id}/board-inputs")
    assert board.status_code == 200
    assert _report_labels(board.text) == [
        "Report",
        "Versions",
        "Applicability",
        "Narrative",
        "Board inputs",
    ]
    assert 'data-board-finding=' in board.text
    assert 'data-board-action=' in board.text
    assert 'data-board-initiative=' in board.text
    assert 'data-board-asks' in board.text
    assert 'hx-swap="none"' in board.text


def test_report_row_hides_applicability_without_iso(db, http, gate, monkeypatch):
    assessment, *_ = released_assessment(
        db, http, gate, monkeypatch, frameworks=("dpdpa",), findings=True
    )
    page = http.get(f"/assessments/{assessment.id}/narrative")
    assert page.status_code == 200
    assert _report_labels(page.text) == ["Report", "Versions", "Narrative", "Board inputs"]
    assert "Applicability" not in page.text


def test_generating_preview_uses_a_non_primary_loading_button(db, http, gate, monkeypatch):
    assessment, *_ = released_assessment(db, http, gate, monkeypatch)
    page = http.get(
        f"/design/pages/b5-narrative?state=generating&assessment_id={assessment.id}"
    )
    assert page.status_code == 200
    assert 'class="btn secondary loading"' in page.text
    assert 'class="btn primary loading"' not in page.text
    assert 'aria-busy="true"' in page.text


def test_generation_failure_and_limit_toasts_match_mockup_copy(
    db, http, gate, monkeypatch
):
    assessment, *_ = released_assessment(db, http, gate, monkeypatch)
    service = importlib.import_module("app.services.narrative")

    def fail(**_kwargs):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(service, "_call_llm", fail)
    endpoint = f"/api/assessments/{assessment.id}/narrative/generate"
    data = {"section_id": "framework-iso27001", "reviewer_name": REVIEWER}
    expected_failure = (
        "ISO 27001:2022 posture could not be drafted. The section stays as it was. "
        "Write it yourself or try again."
    )
    expected_limit = "Draft limit reached for ISO 27001:2022 posture. Write this section yourself."

    for _ in range(3):
        failed = http.post(endpoint, data=data)
        assert failed.status_code == 200
        assert failed.headers["X-Toast-Type"] == "error"
        assert unquote(failed.headers["X-Toast-Message"]) == expected_failure
        assert "HX-Redirect" not in failed.headers

    limited = http.post(endpoint, data=data)
    assert limited.status_code == 200
    assert limited.headers["X-Toast-Type"] == "error"
    assert unquote(limited.headers["X-Toast-Message"]) == expected_limit
    assert "HX-Redirect" not in limited.headers


def test_unreleased_narrative_keeps_unreleased_marker_and_blockers(
    db, http, gate, monkeypatch
):
    assessment, *_ = released_assessment(db, http, gate, monkeypatch)
    drafting = importlib.import_module("app.routers.drafting")
    monkeypatch.setattr(drafting.approved_report, "is_released", lambda *_a, **_k: False)
    monkeypatch.setattr(
        drafting.narrative, "report_blockers", lambda *_a, **_k: ["Executive overview: not accepted"]
    )
    page = http.get(f"/assessments/{assessment.id}/narrative")
    assert page.status_code == 200
    assert "data-narrative-unreleased" in page.text
    assert "data-narrative-blocker" in page.text


def test_board_error_preview_surfaces_validation_copy(db, http, gate, monkeypatch):
    assessment, *_ = released_assessment(db, http, gate, monkeypatch)
    page = http.get(
        f"/design/pages/b5-board-inputs?state=error&assessment_id={assessment.id}"
    )
    assert page.status_code == 200
    assert 'class="field area invalid"' in page.text
    assert "Recommendation must be 1500 characters or fewer." in page.text
    assert "Initiative title must be 120 characters or fewer." in page.text


def test_s7_seed_states_are_registered():
    from design.harness.seed_s7 import screen_states

    states = screen_states()
    assert states["b5-narrative"] == (
        "empty",
        "generating",
        "drafted",
        "partly-accepted",
        "accepted",
        "error",
        "not-released",
    )
    assert states["b5-board-inputs"] == (
        "empty",
        "partly",
        "complete",
        "dense",
        "error",
    )


def test_s7_templates_follow_the_migrated_template_lint_contract():
    for filename in ("narrative.html", "board_inputs.html"):
        text = (TEMPLATE_ROOT / filename).read_text()
        assert not re.search(r"\buppercase\b|text-transform", text, re.IGNORECASE)
        assert not re.search(r"#[0-9a-f]{3,8}\b|\[[^\]]*(?:px|#)[^\]]*\]", text, re.IGNORECASE)
        assert not re.search(r"background-clip\s*:\s*text|blur-3xl", text, re.IGNORECASE)
        assert not re.search(r"<h[1-6][^>]*>\s*(?:(?:Step\s+)?\d+[.)]|[A-Z][.)])\s", text)
