"""P6-1c: registry-path framework calls use a configurable output ceiling.

Live smoke 2026-09-25: the ISO judge hit the old hard-coded 16,384-token cap
(finish_reason=length) and failed closed. The curated DPDPA single-framework
path keeps its original limits so the golden recordings stay byte-identical.
"""

import json

from app.config import settings
from app.frameworks.registry import FrameworkRegistry
from app.services import claude_analyzer, desk_review

import pytest


@pytest.fixture(autouse=True)
def _frameworks():
    from app.main import _register_frameworks

    if not FrameworkRegistry.is_registered("iso27001"):
        _register_frameworks()


def _judge_json(framework_id: str) -> str:
    return json.dumps(
        {
            "executive_summary": "x",
            "assessments": [
                {"requirement_id": control.id, "compliance_status": "compliant", "evidence_quote": "q"}
                for control in FrameworkRegistry.get(framework_id).all_controls()
            ],
        }
    )


def test_default_ceiling_is_well_above_old_cap():
    assert settings.llm_max_output_tokens_framework >= 65536


def test_multi_framework_judge_and_extraction_use_setting(monkeypatch):
    monkeypatch.setattr(settings, "llm_batch_threshold_controls", 10_000)  # P6-1b: pins the unbatched call shape this test characterises (D-P6-1b-L)
    monkeypatch.setattr(settings, "llm_max_output_tokens_framework", 40000)
    seen: list[tuple[str, int]] = []

    def fake(*, tier, stream=False, **request):
        seen.append((tier, request["max_tokens"]))
        if tier == "extract":
            return {"text": json.dumps({"evidence": {}}), "usage": {"input_tokens": 1, "output_tokens": 1, "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0}}
        return {"text": _judge_json("iso27001"), "usage": {"input_tokens": 1, "output_tokens": 1, "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0}}

    monkeypatch.setattr(claude_analyzer, "_call_llm", fake)
    claude_analyzer.run_multi_framework_analysis(
        framework_ids=["iso27001"],
        company_name="Acme",
        industry="saas",
        company_size="sme",
        description=None,
        responses=[],
        documents=[{"filename": "p.txt", "category": "other", "text": "policy text"}],
    )
    assert ("judge", 40000) in seen
    assert ("extract", 40000) in seen


def test_framework_desk_review_uses_setting(monkeypatch):
    monkeypatch.setattr(settings, "llm_max_output_tokens_framework", 50000)
    captured = {}

    def fake(*, tier, stream=False, **request):
        captured.update(request)
        return {"text": "{}", "usage": {"input_tokens": 1, "output_tokens": 1, "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0}}

    monkeypatch.setattr(desk_review, "_call_llm", fake)
    desk_review._call_framework_desk_review("iso27001", [{"filename": "p.txt", "category": "other", "text": "t"}], "Acme", "saas")
    assert captured["max_tokens"] == 50000


def test_curated_dpdpa_paths_keep_original_limits(monkeypatch):
    monkeypatch.setattr(settings, "llm_max_output_tokens_framework", 99999)
    captured = {}

    def fake(*, tier, stream=False, **request):
        captured.update(request)
        return {"text": "{}", "usage": {"input_tokens": 1, "output_tokens": 1, "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0}}

    monkeypatch.setattr(desk_review, "_call_llm", fake)
    desk_review._call_claude_desk_review([{"filename": "p.txt", "category": "other", "text": "t"}], "Acme", "saas")
    assert captured["max_tokens"] == 16000
