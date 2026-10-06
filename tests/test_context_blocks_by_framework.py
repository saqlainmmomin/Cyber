"""Context-wizard blocks follow the assessment's selected frameworks."""

import json

import pytest

from app.dpdpa.context_questions import CONTEXT_BLOCKS, get_context_blocks
from app.frameworks.definitions.dpdpa import DPDPA_DEFINITION
from app.frameworks.definitions.iso27001 import ISO27001_DEFINITION
from app.frameworks.definitions.nist_csf import NIST_CSF_DEFINITION
from app.frameworks.registry import FrameworkRegistry
from app.services import context_profiler


@pytest.fixture(autouse=True)
def _registry():
    for fw in (DPDPA_DEFINITION, ISO27001_DEFINITION, NIST_CSF_DEFINITION):
        FrameworkRegistry.register(fw)


def _ids(framework_ids):
    return [b["id"] for b in get_context_blocks(framework_ids)]


def test_dpdpa_only_keeps_the_full_base_wizard():
    assert get_context_blocks(["dpdpa"]) == CONTEXT_BLOCKS


def test_iso_only_has_no_personal_data_questions():
    blocks = get_context_blocks(["iso27001"])
    assert "data_landscape" not in [b["id"] for b in blocks]
    qids = {q["id"] for b in blocks for q in b["questions"]}
    assert not qids & {"CTX.DATA.1", "CTX.RISK.2", "CTX.POSTURE.1", "CTX.POSTURE.4"}
    assert {"CTX.ISO.1", "CTX.RISK.3", "CTX.INIT.1"} <= qids


def test_framework_blocks_sit_before_the_initiative_block():
    assert _ids(["nist_csf"])[-2:] == ["cyber_risk_context", "initiative_context"]
    assert _ids(["iso27001", "nist_csf"])[-3:] == [
        "isms_context", "cyber_risk_context", "initiative_context",
    ]


def test_privacy_plus_iso_keeps_data_landscape_and_adds_isms():
    ids = _ids(["dpdpa", "iso27001"])
    assert "data_landscape" in ids and "isms_context" in ids


def test_unfiltered_call_returns_base_list():
    assert get_context_blocks(None) is CONTEXT_BLOCKS


def _run_profile(monkeypatch, frameworks):
    seen = {}

    def fake(prompt):
        seen["prompt"] = prompt
        return json.dumps({
            "risk_tier": "MEDIUM", "priority_chapters": ["chapter_2"],
            "likely_not_applicable": ["CH4.SDF.1"], "industry_context": "", 
            "timeline_pressure": "LOW", "framing_notes": "",
        })

    monkeypatch.setattr(context_profiler, "_call_claude_context_profile", fake)
    profile = context_profiler.derive_risk_profile([], "tech", "small", framework_ids=frameworks)
    return profile, seen["prompt"]


def test_non_dpdpa_profile_drops_dpdpa_only_output(monkeypatch):
    profile, prompt = _run_profile(monkeypatch, ["iso27001"])
    assert profile["likely_not_applicable"] == []
    assert "SDF Candidate" not in prompt and "DPDPA chapters" not in prompt


def test_dpdpa_profile_prompt_is_unchanged(monkeypatch):
    _, prompt = _run_profile(monkeypatch, ["dpdpa"])
    assert "SDF Candidate" in prompt and "Order the DPDPA chapters" in prompt
