"""Unit tests for the LLM-output guardrails — validation, grounding, sanity rules.

Pure logic, no network calls: app/schemas/llm_output.py and the two helpers
in app/services/claude_analyzer.py that wrap it.
"""

from app.schemas.llm_output import validate_and_filter
from app.services.claude_analyzer import (
    _flag_unsupported_compliant_items,
    _ground_evidence_quotes,
)

KNOWN_IDS = {"CH2.CONSENT.1", "CH2.CONSENT.2"}


def _item(**overrides):
    base = {
        "requirement_id": "CH2.CONSENT.1",
        "compliance_status": "compliant",
        "current_state": "x",
        "gap_description": "x",
        "risk_level": "low",
        "remediation_action": "x",
        "remediation_priority": 3,
        "remediation_effort": "low",
        "timeline_weeks": 4,
        "maturity_level": 3,
        "root_cause_category": "process",
        "evidence_quote": "some quote",
    }
    base.update(overrides)
    return base


def test_validate_and_filter_drops_unknown_requirement_id():
    parsed = {"executive_summary": "s", "assessments": [_item(requirement_id="HALLUCINATED.99")]}
    result = validate_and_filter(parsed, KNOWN_IDS)
    assert result["assessments"] == []


def test_validate_and_filter_keeps_known_requirement_id():
    parsed = {"executive_summary": "s", "assessments": [_item()]}
    result = validate_and_filter(parsed, KNOWN_IDS)
    assert len(result["assessments"]) == 1
    assert result["assessments"][0]["requirement_id"] == "CH2.CONSENT.1"


def test_validate_and_filter_drops_malformed_item():
    parsed = {
        "executive_summary": "s",
        "assessments": [
            _item(),
            {"compliance_status": "compliant"},  # missing required requirement_id
        ],
    }
    result = validate_and_filter(parsed, KNOWN_IDS)
    assert len(result["assessments"]) == 1
    assert result["assessments"][0]["requirement_id"] == "CH2.CONSENT.1"


def test_validate_and_filter_coerces_unknown_status_to_not_assessed():
    parsed = {"executive_summary": "s", "assessments": [_item(compliance_status="definitely_compliant")]}
    result = validate_and_filter(parsed, KNOWN_IDS)
    assert result["assessments"][0]["compliance_status"] == "not_assessed"


def test_validate_and_filter_coerces_none_optional_fields_to_defaults():
    parsed = {
        "executive_summary": "s",
        "assessments": [_item(evidence_quote=None, current_state=None)],
    }
    result = validate_and_filter(parsed, KNOWN_IDS)
    item = result["assessments"][0]
    assert item["evidence_quote"] == ""
    assert item["current_state"] == ""


def test_validate_and_filter_non_string_executive_summary_becomes_empty():
    parsed = {"executive_summary": None, "assessments": []}
    result = validate_and_filter(parsed, KNOWN_IDS)
    assert result["executive_summary"] == ""


def test_ground_evidence_quotes_keeps_verbatim_match():
    documents = [{"text": "The organization retains records for seven years."}]
    evidence = {"CH2.CONSENT.1": ["retains records for seven years"]}
    result = _ground_evidence_quotes(evidence, documents)
    assert result == {"CH2.CONSENT.1": ["retains records for seven years"]}


def test_ground_evidence_quotes_matches_despite_whitespace_diff():
    documents = [{"text": "The organization   retains records\nfor seven years."}]
    evidence = {"CH2.CONSENT.1": ["retains records for seven years"]}
    result = _ground_evidence_quotes(evidence, documents)
    assert result == {"CH2.CONSENT.1": ["retains records for seven years"]}


def test_ground_evidence_quotes_drops_fabricated_quote():
    documents = [{"text": "The organization retains records for seven years."}]
    evidence = {"CH2.CONSENT.1": ["deletes all data within 24 hours"]}
    result = _ground_evidence_quotes(evidence, documents)
    assert result == {}


def test_ground_evidence_quotes_partial_drop_keeps_the_grounded_one():
    documents = [{"text": "The organization retains records for seven years."}]
    evidence = {
        "CH2.CONSENT.1": [
            "retains records for seven years",
            "deletes all data within 24 hours",
        ]
    }
    result = _ground_evidence_quotes(evidence, documents)
    assert result == {"CH2.CONSENT.1": ["retains records for seven years"]}


def test_flag_unsupported_compliant_items_flags_missing_evidence():
    items = [_item(compliance_status="compliant", evidence_quote="")]
    result = _flag_unsupported_compliant_items(items)
    assert result[0]["needs_review"] is True


def test_flag_unsupported_compliant_items_flags_no_relevant_language_phrase():
    items = [_item(compliance_status="compliant", evidence_quote="No relevant language found")]
    result = _flag_unsupported_compliant_items(items)
    assert result[0]["needs_review"] is True


def test_flag_unsupported_compliant_items_leaves_supported_items_alone():
    items = [_item(compliance_status="compliant", evidence_quote="a real quote")]
    result = _flag_unsupported_compliant_items(items)
    assert "needs_review" not in result[0] or result[0]["needs_review"] is False


def test_flag_unsupported_compliant_items_ignores_non_compliant_status():
    items = [_item(compliance_status="non_compliant", evidence_quote="")]
    result = _flag_unsupported_compliant_items(items)
    assert "needs_review" not in result[0] or result[0]["needs_review"] is False
