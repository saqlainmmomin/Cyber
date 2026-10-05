"""Focused contracts for the Yozora S7 findings group."""

from __future__ import annotations

import re

from app.models.assessment import Assessment
from design.harness.seed_s4 import _report_basis_event
from design.harness.seed_s7_findings import SCREEN_STATES, apply
from tests.yozora_support import (  # noqa: F401 - fixtures are used by name
    _register_frameworks,
    db,
    db_path,
    engine,
    http,
    seed_engagement,
    upload_root,
)


def _preview(db, http, screen: str, state: str):
    _client, engagement, assessment = seed_engagement(
        db,
        client_name=f"Meridian Ledger Technologies {db.query(Assessment).count() + 1}",
        name="FY2026 privacy readiness",
        frameworks=("dpdpa",),
    )
    apply(db, screen, state, assessment, engagement, {"assessments": [assessment]})
    db.add(_report_basis_event(assessment))
    db.commit()
    return http.get(f"/design/pages/{screen}?state={state}&assessment_id={assessment.id}")


def test_findings_preview_registry_covers_the_group_states():
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


def test_findings_preview_has_assessment_and_review_navigation(db, http):
    response = _preview(db, http, "b5-findings", "default")

    assert response.status_code == 200
    assert '<nav class="tabs" aria-label="Assessment">' in response.text
    assert '<div class="seg">' in response.text
    assert all(label in response.text for label in ("Queue", "Conclusions", "Findings", "Workpaper"))
    assert 'aria-pressed="true" data-href="/assessments/' in response.text
    assert "Findings and actions" in response.text


def test_findings_preview_states_have_one_primary_and_no_numeric_priority(db, http):
    for state in SCREEN_STATES["b5-findings"]:
        response = _preview(db, http, "b5-findings", state)

        assert response.status_code == 200
        assert response.text.count('class="btn primary') == 1
        assert not re.search(r"\bPriority\s+[1-4]\b", response.text)


def test_finding_card_preview_preserves_s4_attributes_and_state_copy(db, http):
    expected = {
        "open": "Update status",
        "in-progress": "Close action",
        "no-evidence": "No closure evidence is on file",
        "verify": "Verify closure",
        "verified": "Closed and verified actions cannot be changed here.",
        "legacy": "Closed without closure evidence (legacy)",
        "source-changed": "The source conclusion is no longer approved",
        "migrated": "Migrated from legacy remediation",
        "add-action": "Add action",
    }
    for state, copy in expected.items():
        response = _preview(db, http, "b5-finding-card", state)

        assert response.status_code == 200
        assert 'data-finding-card' in response.text
        assert 'data-finding-origin=' in response.text
        assert 'data-source-approved=' in response.text
        assert 'data-action-row' in response.text
        assert 'data-action-history' in response.text
        assert 'data-action-status=' in response.text
        assert 'data-history-action=' in response.text
        if state not in {"verified", "no-evidence"}:
            assert 'hx-target="#finding-' in response.text
            assert 'hx-swap="outerHTML"' in response.text
            assert 'hx-include="#reviewer-name"' in response.text
        assert copy in response.text
        assert not re.search(r"\bPriority\s+[1-4]\b", response.text)
        assert response.text.count('class="btn primary') <= 1


def test_finding_card_uses_only_in_scope_framework_copy(db, http):
    response = _preview(db, http, "b5-finding-card", "open")

    assert "DPDPA" in response.text
    assert "ISO 27001" not in response.text


def test_dark_dense_preview_has_expected_rows_and_word_priority(db, http):
    response = _preview(db, http, "b7-dark-dense", "dense")

    assert response.status_code == 200
    assert response.text.count("data-finding-row") == 8
    assert response.text.count('class="pill c-high"') == 2
    assert response.text.count('class="pill c-medium"') == 3
    assert response.text.count('class="pill c-low"') == 3
    assert "Do first" in response.text
    assert "Next" in response.text
    assert not re.search(r"\bPriority\s+[1-4]\b", response.text)
