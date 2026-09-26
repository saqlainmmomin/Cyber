"""P6-1d: registry evidence extraction runs alongside desk-review reuse, and
every LLM request turns hidden reasoning off."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from app.config import settings

USAGE = {
    "input_tokens": 0,
    "output_tokens": 0,
    "cache_read_input_tokens": 0,
    "cache_creation_input_tokens": 0,
}
DOCS = [
    {
        "filename": "policy.pdf",
        "category": "policy",
        "text": "Desk quote about policy. Extracted quote about access.",
    }
]


@pytest.fixture(autouse=True)
def _register_frameworks():
    from app.main import _register_frameworks

    _register_frameworks()


def _response(payload):
    return {"text": json.dumps(payload), "usage": dict(USAGE)}


def _analysis_payload(framework_id):
    from app.frameworks.registry import FrameworkRegistry

    return {
        "executive_summary": "ok",
        "assessments": [
            {"requirement_id": control.id, "compliance_status": "not_assessed"}
            for control in FrameworkRegistry.get(framework_id).all_controls()
        ],
    }


def _desk_data(requirement_id, quote):
    return {
        "findings": [
            {"type": "evidence", "requirement_id": requirement_id, "content": "Found", "source_quote": quote}
        ],
        "coverage_summary": {},
        "signal_flags": [],
        "absence_findings": [],
    }


def _run(monkeypatch, framework_ids, desk_data, extract_result):
    from app.services import claude_analyzer

    monkeypatch.setattr(settings, "llm_batch_threshold_controls", 10_000)
    calls = []

    def llm(**kwargs):
        calls.append(kwargs)
        if kwargs["tier"] == "extract":
            if isinstance(extract_result, Exception):
                raise extract_result
            return _response(extract_result)
        if kwargs["tier"] == "judge":
            persona = kwargs["system"][0]["text"]
            fw_id = "dpdpa" if "DPDPA" in persona else "iso27001"
            return _response(_analysis_payload(fw_id))
        return _response({"overall_posture": "ok"})

    monkeypatch.setattr(claude_analyzer, "_call_llm", llm)
    claude_analyzer.run_multi_framework_analysis(
        framework_ids, "Acme", "Technology", "medium", None, [], DOCS,
        desk_review_data=desk_data,
    )
    extracts = [call for call in calls if call["tier"] == "extract"]
    judges = [call["messages"][0]["content"] for call in calls if call["tier"] == "judge"]
    return extracts, judges


def test_registry_extraction_runs_despite_desk_review_evidence_and_merges(monkeypatch):
    extracts, judges = _run(
        monkeypatch,
        ["iso27001"],
        _desk_data("ISO.A5.1", "Desk quote about policy."),
        {
            "evidence": {
                "ISO.A5.1": ["Desk quote about policy.", "Extracted quote about access."],
                "ISO.A5.15": ["Extracted quote about access.", "invented quote"],
            }
        },
    )

    assert len(extracts) == 1
    assert "Desk quote about policy." in extracts[0]["messages"][0]["content"]
    (prompt,) = judges
    assert "## Supporting Documents" not in prompt
    iso_a51 = prompt.split("### ISO.A5.1\n", 1)[1].split("\n\n", 1)[0]
    assert iso_a51 == "> Desk quote about policy.\n> Extracted quote about access."
    assert "### ISO.A5.15\n> Extracted quote about access." in prompt
    assert "invented quote" not in prompt


def test_registry_extraction_failure_keeps_desk_review_evidence(monkeypatch):
    extracts, judges = _run(
        monkeypatch,
        ["iso27001"],
        _desk_data("ISO.A5.1", "Desk quote about policy."),
        RuntimeError("extract down"),
    )

    assert len(extracts) == 1
    (prompt,) = judges
    assert "### ISO.A5.1\n> Desk quote about policy." in prompt


def test_curated_dpdpa_still_skips_extraction_when_desk_review_found_evidence(monkeypatch):
    extracts, judges = _run(
        monkeypatch,
        ["dpdpa"],
        _desk_data("CH2.CONSENT.1", "Desk quote about policy."),
        {"evidence": {}},
    )

    assert extracts == []
    assert "Desk quote about policy." in judges[0]


REASONING_OFF_PREFS = {
    "provider": {"data_collection": "deny", "zdr": True},
    "reasoning": {"enabled": False},
}


def _fake_client(captured, content='{"ok": true}'):
    choice = SimpleNamespace(message=SimpleNamespace(content=content), finish_reason="stop")
    usage = SimpleNamespace(prompt_tokens=1, completion_tokens=1, prompt_tokens_details=None)
    response = SimpleNamespace(choices=[choice], usage=usage)

    def create(**kwargs):
        captured.append(kwargs)
        return response

    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))


def test_every_request_turns_reasoning_off(monkeypatch):
    from app.services import llm_client

    captured = []
    monkeypatch.setattr(llm_client, "_client", _fake_client(captured))

    llm_client.call_llm("judge", system="s", messages=[], max_tokens=10)
    llm_client.call_llm(
        "extract", system="s", messages=[], max_tokens=10,
        response_schema={"name": "x", "schema": {"type": "object"}},
    )

    assert llm_client._REQUEST_PREFS == REASONING_OFF_PREFS
    assert captured[0]["extra_body"] == REASONING_OFF_PREFS
    assert captured[1]["extra_body"]["reasoning"] == {"enabled": False}
    assert captured[1]["extra_body"]["provider"]["require_parameters"] is True


def test_context_profile_and_framework_extraction_send_reasoning_off(monkeypatch):
    from app.services import claude_analyzer, context_profiler, llm_client

    captured = []
    monkeypatch.setattr(
        llm_client,
        "_client",
        _fake_client(captured, '{"evidence": {}, "risk_tier": "LOW"}'),
    )

    context_profiler._call_claude_context_profile("prompt")
    claude_analyzer._run_framework_evidence_extraction("iso27001", DOCS)

    assert len(captured) == 2
    assert all(call["extra_body"] == REASONING_OFF_PREFS for call in captured)
