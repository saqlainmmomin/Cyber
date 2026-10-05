"""Focused contracts for the S7 analysis group templates and fixtures."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from jinja2 import Environment, FileSystemLoader


TEMPLATE_ROOT = Path(__file__).parents[1] / "app" / "templates"
ENVIRONMENT = Environment(loader=FileSystemLoader(TEMPLATE_ROOT))


def _render(name: str, **context) -> str:
    return ENVIRONMENT.get_template(name).render(**context)


def _assessment():
    return SimpleNamespace(id="assessment-1")


def _basis(**overrides):
    values = {
        "period_start": date(2025, 4, 1),
        "period_end": date(2026, 3, 31),
        "evidence_cutoff": date(2026, 3, 15),
        "prepared_by": "Arjun Mehta",
        "reviewed_by": "Priya Sharma",
        "period_recorded": True,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _release(**overrides):
    values = {
        "released": False,
        "stale": False,
        "blockers": (),
        "released_by": None,
        "released_at": None,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _finding(**overrides):
    values = {
        "id": "item-1",
        "framework_id": "dpdpa",
        "chapter": "Consent",
        "requirement_id": "CH2.CONSENT.3",
        "requirement_title": "Consent withdrawal mechanism",
        "review_status": "draft",
        "risk_level": "high",
        "ai_compliance_status": "non_compliant",
        "compliance_status": "non_compliant",
        "ai_risk_level": "high",
        "evidence_confidence": "weak",
        "ai_gap_description": "Users cannot withdraw consent in the product.",
        "gap_description": "Users cannot withdraw consent in the product.",
        "evidence_quote": "Changes are requested through the data protection officer.",
        "reviewer_notes": None,
        "needs_review": False,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_analysis_states_keep_polling_contract_and_one_primary():
    running = _render(
        "partials/analysis_running.html",
        assessment_id="assessment-1",
        document_count=14,
        response_count=212,
    )
    assert 'hx-get="/assessments/assessment-1/analysis-status"' in running
    assert 'hx-trigger="every 3s"' in running
    assert 'hx-swap="outerHTML"' in running
    assert "Reading 14 documents and 212 questionnaire responses" in running
    assert 'class="btn primary' not in running

    complete = _render(
        "partials/analysis_complete.html",
        assessment_id="assessment-1",
        report=object(),
        framework_display={
            "dpdpa": {
                "name": "DPDPA 2023",
                "status": "pending_review",
                "coverage": {"eligible": 2, "in_scope": 3},
                "failed": False,
                "score": None,
            },
            "iso27001": {
                "name": "ISO 27001:2022",
                "status": "pending_review",
                "coverage": {"eligible": 1, "in_scope": 3},
                "failed": False,
                "score": None,
            },
        },
    )
    assert "2 of 3 conclusions approved" in complete
    assert 'data-review-conclusions-link' in complete
    assert complete.count('class="btn primary') == 1

    error = _render(
        "partials/analysis_error.html",
        assessment_id="assessment-1",
        framework_display={
            "iso27001": {"name": "ISO 27001:2022", "failed": True},
            "dpdpa": {"name": "DPDPA 2023", "failed": False},
        },
    )
    assert 'data-analysis-failed-frameworks' in error
    assert "Analysis failed for ISO 27001:2022" in error
    assert 'hx-target="#analysis-area"' in error
    assert error.count('class="btn primary') == 1

    gate = _render(
        "partials/analysis_gate_blocked.html",
        assessment_id="assessment-1",
        message="The questionnaire has 24 required questions without an answer.",
        show_override=True,
        override_reasons={"client_answers_pending": "The client has not answered yet"},
    )
    assert 'data-completion-gate-blocked' in gate
    assert 'data-completion-override-form' in gate
    assert 'id="override_reason"' in gate
    assert 'name="reviewer_name"' in gate
    assert 'class="btn primary' not in gate


def test_release_panel_preserves_states_and_single_primary():
    blocked = _render(
        "partials/release_panel.html",
        assessment=_assessment(),
        release=_release(blockers=("3 in-scope conclusions are not approved", "The assessment period is not recorded")),
    )
    assert 'data-release-state="not_released"' in blocked
    assert 'data-release-blockers' in blocked
    assert 'data-release-form' not in blocked
    assert 'class="btn primary' not in blocked

    ready = _render(
        "partials/release_panel.html",
        assessment=_assessment(),
        release=_release(),
        counts=SimpleNamespace(approved=6, edited=0, pending=0, rejected=0, legacy_bulk=0),
    )
    assert "All 6 in-scope conclusions are individually approved." in ready
    assert 'data-release-form' in ready
    assert ready.count('class="btn primary') == 1

    confirm = _render(
        "partials/release_panel.html",
        assessment=_assessment(),
        release=_release(),
        counts=SimpleNamespace(approved=6, edited=0, pending=0, rejected=0, legacy_bulk=0),
        release_confirm=True,
    )
    assert 'role="dialog"' in confirm
    assert "Exports will use the conclusions exactly as they are approved now." in confirm
    assert confirm.count('class="btn primary') == 1

    released = _render(
        "partials/release_panel.html",
        assessment=_assessment(),
        release=_release(
            released=True,
            released_by="Priya Sharma",
            released_at=datetime(2026, 9, 24, tzinfo=timezone.utc),
        ),
    )
    assert "Released by Priya Sharma on 24 Sep 2026" in released
    assert "Download PDF" in released
    assert 'data-release-form' not in released


def test_report_basis_keeps_form_contract_and_lock_has_no_primary():
    empty = _render(
        "partials/report_basis_panel.html",
        assessment=_assessment(),
        report_basis=_basis(
            period_start=None,
            period_end=None,
            evidence_cutoff=None,
            prepared_by=None,
            reviewed_by=None,
            period_recorded=False,
        ),
        period_locked=False,
    )
    assert 'data-report-basis-panel' in empty
    assert 'data-period-recorded="no"' in empty
    assert 'data-report-basis-form' in empty
    assert 'hx-post="/api/assessments/assessment-1/report-basis"' in empty
    assert 'hx-swap="none"' in empty
    assert 'class="btn primary' in empty

    invalid = _render(
        "partials/report_basis_panel.html",
        assessment=_assessment(),
        report_basis=_basis(period_end=date(2025, 3, 31)),
        period_locked=False,
        field_errors={"period_end": "The period end must be after the period start."},
    )
    assert 'class="field invalid"' in invalid
    assert "The period end must be after the period start." in invalid

    locked = _render(
        "partials/report_basis_panel.html",
        assessment=_assessment(),
        report_basis=_basis(),
        period_locked=True,
    )
    assert 'data-period-locked="yes"' in locked
    assert "Locked while conclusions are approved" in locked
    assert 'class="btn primary' not in locked


def test_review_finding_card_has_expected_states_and_htmx_contract():
    draft = _render("partials/review_finding_card.html", assessment=_assessment(), item=_finding())
    assert 'id="review-card-item-1"' in draft
    assert 'data-review-card' in draft
    assert 'data-review-status="draft"' in draft
    assert 'data-risk-level="high"' in draft
    assert 'hx-patch="/api/assessments/assessment-1/review/items/item-1"' in draft
    assert 'hx-target="#review-card-item-1"' in draft
    assert 'class="btn primary' in draft
    assert "Accept" in draft and "Reject" in draft

    flagged = _render(
        "partials/review_finding_card.html",
        assessment=_assessment(),
        item=_finding(evidence_quote=None, needs_review=True),
    )
    assert "No evidence" in flagged
    assert 'class="warn"' in flagged
    assert "Needs review" in flagged

    notes = _render(
        "partials/review_finding_card.html",
        assessment=_assessment(),
        item=_finding(),
        notes_open=True,
    )
    assert "Reviewer notes" in notes
    assert 'name="reviewer_notes"' in notes
    assert "Save notes" in notes

    accepted = _render(
        "partials/review_finding_card.html",
        assessment=_assessment(),
        item=_finding(review_status="accepted"),
    )
    assert "Accepted" in accepted
    assert "Change decision" in accepted
    assert 'class="btn primary' not in accepted

    rejected = _render(
        "partials/review_finding_card.html",
        assessment=_assessment(),
        item=_finding(
            review_status="rejected",
            reviewer_notes="The mechanism exists in the mobile app.",
        ),
    )
    assert "Rejected" in rejected
    assert "The mechanism exists in the mobile app." in rejected
    assert 'class="btn primary' not in rejected


def test_s7_analysis_seed_registers_every_group_state():
    from design.harness.seed_s7 import screen_states

    states = screen_states()
    assert states["b5-analysis"] == (
        "running",
        "complete",
        "error",
        "error-all",
        "gate",
        "gate-no-override",
    )
    assert states["b5-release"] == ("blocked", "ready", "confirm", "released", "stale")
    assert states["b5-basis"] == ("empty", "filled", "invalid", "locked", "saved")
    assert states["b5-review-finding-card"] == (
        "draft",
        "needs-review",
        "notes",
        "accepted",
        "rejected",
    )
