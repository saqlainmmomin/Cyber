"""Focused contracts for the Yozora S7 findings group (live routes, not preview fixtures)."""

from __future__ import annotations

import re

from app.models.assessment import Assessment
from app.models.conclusion import ConclusionRevision
from design.harness.seed_s4 import _report_basis_event
from design.harness.seed_s7_findings import SCREEN_STATES, apply, route
from tests.yozora_support import (  # noqa: F401 - fixtures are used by name
    _register_frameworks,
    db,
    db_path,
    engine,
    http,
    seed_engagement,
    upload_root,
)

MUST_KEEP_CARD = (
    "data-finding-card",
    "data-finding-origin=",
    "data-source-approved=",
    "data-action-row",
    "data-action-history",
    "data-action-status=",
    "data-history-action=",
)


def _seed(db, screen: str, state: str) -> Assessment:
    _client, engagement, assessment = seed_engagement(
        db,
        client_name=f"Meridian Ledger Technologies {db.query(Assessment).count() + 1}",
        name="FY2026 privacy readiness",
        frameworks=("dpdpa",),
    )
    apply(db, screen, state, assessment, engagement, {"assessments": [assessment]})
    db.add(_report_basis_event(assessment))
    db.commit()
    return assessment


def _get(db, http, screen: str, state: str):
    assessment = _seed(db, screen, state)
    return http.get(route(screen, state, assessment.id))


def _visible_primaries(html: str) -> int:
    """Primary buttons outside hidden blocks (the unopened create forms carry none)."""
    return html.count('class="btn primary')


def test_findings_registry_covers_the_group_states():
    assert SCREEN_STATES["b5-findings"] == ("default", "create", "empty")
    assert SCREEN_STATES["b5-finding-card"] == (
        "open",
        "in-progress",
        "no-evidence",
        "verify",
        "verified",
        "legacy",
        "source-changed",
        "migrated",
        "add-action",
    )
    assert SCREEN_STATES["b7-dark-dense"] == ("dense",)


def test_gate_routes_are_live_routes():
    for screen, states in SCREEN_STATES.items():
        for state in states:
            assert route(screen, state, "a1").startswith("/assessments/a1/findings")


def test_findings_page_has_assessment_and_review_navigation(db, http):
    response = _get(db, http, "b5-findings", "default")

    assert response.status_code == 200
    assert '<nav class="tabs" aria-label="Assessment">' in response.text
    assert all(label in response.text for label in ("Queue", "Conclusions", "Findings", "Workpaper"))
    assert "<h1>Findings and actions</h1>" in response.text
    assert 'id="reviewer-name"' in response.text
    assert "data-board-inputs-link" in response.text
    assert response.text.count("data-finding-row") == 4
    assert "data-finding-card" not in response.text


def test_findings_states_have_one_primary_and_no_numeric_priority(db, http):
    for state in SCREEN_STATES["b5-findings"]:
        response = _get(db, http, "b5-findings", state)

        assert response.status_code == 200
        assert _visible_primaries(response.text) == 1, state
        assert not re.search(r"\bPriority\s+[1-4]\b", response.text)


def test_create_state_opens_one_real_form(db, http):
    response = _get(db, http, "b5-findings", "create")

    assert response.status_code == 200
    assert response.text.count("<h3>New finding from ") == 1
    assert 'hx-post="/api/assessments/' in response.text
    assert 'name="conclusion_version"' in response.text
    # The row's own Create finding button steps back while the form is open.
    assert ">Create finding</a>" not in response.text


def test_several_eligible_conclusions_still_show_one_primary(db, http):
    assessment = _seed(db, "b5-findings", "default")
    from design.harness.seed_s7_findings import _conclusion

    _conclusion(db, assessment, f"conclusion-s7-extra-{assessment.id}", "CH2.CONSENT.1")
    db.commit()
    response = http.get(f"/assessments/{assessment.id}/findings")

    assert response.text.count("data-eligible-conclusion") == 2
    assert _visible_primaries(response.text) == 1
    assert response.text.count(">Create finding</a>") == 2


def test_eligible_row_shows_the_real_approver_and_date(db, http):
    assessment = _seed(db, "b5-findings", "default")
    for revision in db.query(ConclusionRevision).filter(ConclusionRevision.actor == "consultant:Priya Sharma"):
        revision.actor = "consultant:Asha Rao"
    db.commit()
    response = http.get(f"/assessments/{assessment.id}/findings")

    assert "Approved by Asha Rao on 24 Sep 2026" in response.text
    assert "Priya Sharma" not in response.text


def test_rows_link_to_the_finding_detail_and_old_anchors_redirect(db, http):
    assessment = _seed(db, "b5-findings", "default")
    response = http.get(f"/assessments/{assessment.id}/findings")

    assert f'href="/assessments/{assessment.id}/findings?finding=finding-s7-consent-{assessment.id}"' in response.text
    assert 'location.hash' in response.text and '?finding=' in response.text


def test_finding_detail_states_keep_s4_attributes_and_state_copy(db, http):
    expected = {
        "open": "Update status",
        "in-progress": "Close action",
        "no-evidence": "No closure evidence is on file",
        "verify": "Verify closure",
        "verified": "Closed and verified actions cannot be changed here.",
        "legacy": "Closed without closure evidence (legacy)",
        "source-changed": "The source conclusion is no longer approved",
        "migrated": "Migrated from the earlier remediation tracker",
        "add-action": "Add action",
    }
    for state, copy in expected.items():
        response = _get(db, http, "b5-finding-card", state)

        assert response.status_code == 200
        assert response.text.count("data-finding-card") == 1
        for attribute in MUST_KEEP_CARD:
            assert attribute in response.text, (state, attribute)
        assert 'hx-target="#finding-' in response.text
        assert 'hx-swap="outerHTML"' in response.text
        assert 'hx-include="#reviewer-name"' in response.text
        assert 'id="reviewer-name"' in response.text
        assert copy in response.text, state
        assert not re.search(r"\bPriority\s+[1-4]\b", response.text)
        assert _visible_primaries(response.text) == 1, state
        assert '<nav class="tabs" style="overflow-x:auto;margin-bottom:var(--s-6)" aria-label="Engagement">' in response.text


def test_add_action_steps_aside_while_an_action_awaits_a_decision(db, http):
    for state in ("verify", "legacy", "migrated"):
        assert "&amp;add=1" not in _get(db, http, "b5-finding-card", state).text, state
    assert "btn ghost lead" in _get(db, http, "b5-finding-card", "in-progress").text
    assert "&amp;add=1" in _get(db, http, "b5-finding-card", "verified").text


def test_reviewer_name_sits_in_the_detail_head_not_in_the_flow(db, http):
    html = _get(db, http, "b5-finding-card", "open").text

    assert html.count('id="reviewer-name"') == 1
    assert html.index('class="f-reviewer"') < html.index("data-finding-card")


def test_finding_detail_uses_only_in_scope_framework_copy(db, http):
    response = _get(db, http, "b5-finding-card", "open")

    assert '<span class="chip">DPDPA</span>' in response.text
    assert "ISO 27001" not in response.text


def test_history_timestamps_render_as_dates(db, http):
    response = _get(db, http, "b5-finding-card", "verified")

    assert "30 Sep 2026, Priya Sharma" in response.text
    assert "2026-09-30T" not in response.text


def test_dense_findings_list_has_rows_and_severity_words(db, http):
    response = _get(db, http, "b7-dark-dense", "dense")

    assert response.status_code == 200
    assert response.text.count("data-finding-row") == 8
    assert response.text.count('class="pill c-high"') == 2
    assert response.text.count('class="pill c-medium"') == 3
    assert response.text.count('class="pill c-low"') == 3
    assert not re.search(r"\bPriority\s+[1-4]\b", response.text)
