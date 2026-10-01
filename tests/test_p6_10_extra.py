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


from app.services import narrative


def _narrative_ref(alias, finding_id, framework_id, framework_name):
    return narrative.FindingRef(
        alias=alias,
        finding_id=finding_id,
        framework_id=framework_id,
        framework_name=framework_name,
        requirement_id="A.1",
        requirement_title="Access control",
        title="Access reviews",
        description="Reviews are informal.",
        severity="medium",
        priority=1,
        outcome_label="Gap",
        decision_version=1,
    )


@pytest.mark.parametrize("section_id", ["executive", "cross-framework"])
def test_model_non_legal_copy_is_dropped_for_non_framework_sections(section_id):
    sentence = "This requires DPDPA."
    iso = _narrative_ref("F1", "finding-1", "iso27001", "ISO 27001")
    refs = (iso,)
    aliases = [iso.alias]
    if section_id == "cross-framework":
        nist = _narrative_ref("F2", "finding-2", "nist_csf", "NIST CSF")
        refs = (iso, nist)
        aliases = [iso.alias, nist.alias]

    kept, dropped = narrative._clean_model_sentences(
        section_id, refs, [{"text": sentence, "finding_refs": aliases}]
    )

    assert kept == []
    assert dropped == [{"text": sentence, "reason": "framework_copy"}]


@pytest.mark.parametrize("section_id", ["executive", "cross-framework"])
def test_model_non_legal_copy_is_kept_when_closed_set_includes_dpdpa(section_id):
    sentence = "This requires DPDPA."
    dpdpa = _narrative_ref("F1", "finding-1", "dpdpa", "DPDPA")
    refs = (dpdpa,)
    aliases = [dpdpa.alias]
    if section_id == "cross-framework":
        iso = _narrative_ref("F2", "finding-2", "iso27001", "ISO 27001")
        refs = (dpdpa, iso)
        aliases = [dpdpa.alias, iso.alias]

    kept, dropped = narrative._clean_model_sentences(
        section_id, refs, [{"text": sentence, "finding_refs": aliases}]
    )

    assert kept == [{"text": sentence, "finding_ids": [ref.finding_id for ref in refs]}]
    assert dropped == []
