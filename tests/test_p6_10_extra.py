"""Extra regression coverage for the P6-10 drafting route boundary."""

from __future__ import annotations

from urllib.parse import unquote

import pytest

from app.models.audit_event import AuditEvent
from tests.p6_10_support import (
    REVIEWER,
    _no_network_llm,
    _register_frameworks,
    analysed_assessment,
    db,
    db_path,
    engine,
    gate,
    http,
    upload_root,
)


@pytest.mark.parametrize("expected_version", [None, "not-an-integer"])
def test_stage3_invalid_expected_version_is_a_refusal_without_a_write(
    db, http, gate, monkeypatch, expected_version
):
    assessment, conclusions, dp, _iso = analysed_assessment(db, gate, monkeypatch)
    conclusion = conclusions[("dpdpa", dp[0])]
    before = db.query(AuditEvent).count()
    form = {
        "outcome": conclusion.outcome,
        "gaps_identified": conclusion.gaps_identified,
        "recommended_action": conclusion.recommended_action,
        "reviewer_name": REVIEWER,
    }
    if expected_version is not None:
        form["expected_version"] = expected_version

    response = http.post(
        f"/api/assessments/{assessment.id}/recommended-action-drafts/{conclusion.id}",
        data=form,
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Expected version must be an integer."}
    assert unquote(response.headers["X-Toast-Message"]) == response.json()["detail"]
    assert response.headers["X-Toast-Type"] == "error"
    assert db.query(AuditEvent).count() == before
