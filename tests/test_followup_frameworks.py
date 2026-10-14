"""WP 1.4 part 2b: follow-up requests follow the assessment's framework scope.

DPDPA-only assessments keep their original request byte for byte; every other
scope gets its own framework names and no DPDPA wording.
"""

from __future__ import annotations

import hashlib
import json
from unittest.mock import patch

import pytest

from app.frameworks.registry import FrameworkRegistry
from app.main import _register_frameworks
from app.services import followup_engine

ALL_FRAMEWORKS = ["dpdpa", "iso27001", "gdpr", "hipaa", "nist_csf", "pci_dss"]

# sha256 of the DPDPA-only request (system + messages) before part 2b.
DPDPA_REQUEST_SHA256 = "fe9310ac385439c7f5393344325316e2503f71fe00588936f95e264957640b88"


@pytest.fixture(autouse=True)
def _frameworks():
    _register_frameworks()


def _capture(framework_ids: list[str], guidance: str = "Keep a record.") -> dict:
    captured = {}

    def fake_call_llm(*, tier, stream=False, **request):
        captured.update(request, tier=tier)
        return {"text": "[]"}

    with patch.object(followup_engine, "_call_llm", side_effect=fake_call_llm):
        followup_engine.generate_followups(
            "Is it implemented?",
            "Q.1",
            "not_implemented",
            "critical",
            ["Q.1"],
            desk_review_evidence=[{"content": "Policy found", "source_quote": "We log access."}],
            desk_review_note="Policy is undated.",
            guidance=guidance,
            framework_ids=framework_ids,
        )
    return captured


def _fingerprint(request: dict) -> str:
    payload = json.dumps(
        {"system": request["system"], "messages": request["messages"]}, sort_keys=True
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def test_dpdpa_only_request_is_unchanged():
    request = _capture(["dpdpa"])
    assert request["system"].startswith("You are an expert DPDPA compliance auditor")
    assert "**DPDPA Guidance:** Keep a record." in request["messages"][0]["content"]
    assert _fingerprint(request) == DPDPA_REQUEST_SHA256


@pytest.mark.parametrize("framework_id", [f for f in ALL_FRAMEWORKS if f != "dpdpa"])
def test_non_dpdpa_request_names_its_framework(framework_id):
    request = _capture([framework_id])
    name = FrameworkRegistry.get(framework_id).name
    prompt = request["messages"][0]["content"]
    assert name in request["system"]
    assert "DPDPA" not in request["system"]
    assert "DPDPA" not in prompt
    assert "**Guidance:** Keep a record." in prompt
    assert request["tier"] == "extract"


def test_mixed_scope_names_every_framework_without_dpdpa_persona():
    request = _capture(["iso27001", "nist_csf", "dpdpa"])
    assert "ISO 27001, NIST CSF, India DPDPA" in request["system"]
    assert "expert DPDPA compliance auditor" not in request["system"]
    assert "**Guidance:**" in request["messages"][0]["content"]


def test_missing_framework_scope_is_refused():
    with pytest.raises(ValueError):
        followup_engine.generate_followups(
            "Is it implemented?", "Q.1", "not_implemented", "critical", [],
            framework_ids=[],
        )
