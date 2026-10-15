"""Characterization coverage for LLM call sites outside claude_analyzer.

All six services route through their own module-level `_call_llm` seam (which
delegates to `app.services.llm_client.call_llm`) — patch that seam directly,
same convention `claude_analyzer.py`'s golden tests use.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest


def _response(text: str, **usage_overrides) -> dict:
    usage = {
        "input_tokens": 12,
        "output_tokens": 7,
        "cache_read_input_tokens": 0,
        "cache_creation_input_tokens": 0,
    }
    usage.update(usage_overrides)
    return {"text": text, "usage": usage}


def test_desk_review_call_parses_valid_json():
    from app.services.desk_review import _call_claude_desk_review

    with patch(
        "app.services.desk_review._call_llm",
        return_value=_response('{"document_catalog": []}'),
    ):
        result = _call_claude_desk_review([], "Acme", "saas")

    assert result == {"document_catalog": []}


def test_desk_review_call_rejects_non_json_response():
    from app.services.desk_review import _call_claude_desk_review

    with patch("app.services.desk_review._call_llm", return_value=_response("not json")):
        with pytest.raises(ValueError, match="Failed to parse desk review response"):
            _call_claude_desk_review([], "Acme", "saas")


def test_desk_review_shared_selection_preserves_upload_order_and_budget(monkeypatch):
    from app.services import desk_review
    from app.services.document_selection import select_documents

    monkeypatch.setattr(desk_review.settings, "max_total_document_words", 3)
    documents = [
        {"filename": "first", "category": "other", "text": "one two"},
        {"filename": "second", "category": "privacy_policy", "text": "three four"},
    ]

    expected = [
        {"filename": "first", "category": "other", "text": "one two"},
        {"filename": "second", "category": "privacy_policy", "text": "three\n\n[... truncated ...]"},
    ]
    assert desk_review._truncate_documents(documents) == expected
    assert select_documents(documents, ordering="upload") == expected


def _desk_review_with_documents(monkeypatch, documents, framework_ids):
    from app.main import _register_frameworks
    from app.models.assessment import Assessment
    from app.services import desk_review

    _register_frameworks()
    assessment = Assessment(
        id="assessment", company_name="Acme", industry="saas", company_size="sme",
        selected_frameworks=json.dumps(framework_ids),
    )
    db = MagicMock()
    db.get.return_value = assessment
    db.query.return_value.filter.return_value.first.return_value = None
    monkeypatch.setattr(desk_review.settings, "analysis_pipeline_version", "v1")
    monkeypatch.setattr(desk_review, "analysis_documents", lambda *_args: documents)
    monkeypatch.setattr(desk_review, "control_batches", lambda *_args: ())
    calls = []

    def fake_call(framework_id, **kwargs):
        calls.append((framework_id, kwargs["documents"]))
        raise ValueError("mock failure after capturing input")

    monkeypatch.setattr(desk_review, "_desk_review_call", fake_call)
    summary = desk_review.run_desk_review(assessment.id, db)
    return calls, json.loads(summary.raw_ai_response)


def test_dpdpa_desk_review_uses_upload_order_in_prompt_and_manifest(monkeypatch):
    from app.services import desk_review

    monkeypatch.setattr(desk_review.settings, "max_total_document_words", 3)
    documents = [
        {"id": "1", "legacy_document_id": "1", "filename": "first", "category": "other", "text": "one two"},
        {"id": "2", "legacy_document_id": "2", "filename": "second", "category": "privacy_policy", "text": "three four"},
    ]
    calls, response = _desk_review_with_documents(monkeypatch, documents, ["dpdpa"])

    assert [doc["filename"] for doc in calls[0][1]] == ["first", "second"]
    assert calls[0][1][1]["text"] == "three\n\n[... truncated ...]"
    manifest = response["document_manifest"]["frameworks"]["dpdpa"]
    assert manifest["ordering"] == "upload"
    assert [(entry["filename"], entry["status"]) for entry in manifest["selection"]] == [
        ("first", "read"), ("second", "partial"),
    ]


def test_desk_review_legacy_budget_lists_union_all_frameworks(monkeypatch):
    from app.services import desk_review

    calls = 0
    real_manifest = desk_review.stage_manifest

    def varied_selection(*args, **kwargs):
        nonlocal calls
        manifest = real_manifest(*args, **kwargs)
        if calls:
            manifest["selection"][0]["status"] = "not_read"
            manifest["selection"][1]["status"] = "partial"
        calls += 1
        return manifest

    monkeypatch.setattr(desk_review.settings, "max_total_document_words", 10)
    monkeypatch.setattr(desk_review, "stage_manifest", varied_selection)
    documents = [
        {"id": "1", "legacy_document_id": "1", "filename": "first", "category": "other", "text": "one"},
        {"id": "2", "legacy_document_id": "2", "filename": "second", "category": "other", "text": "two"},
    ]
    _, response = _desk_review_with_documents(monkeypatch, documents, ["dpdpa", "iso27001", "nist_csf"])

    assert response["budget_skipped_filenames"] == ["first"]
    assert response["budget_partial_filenames"] == ["second"]


def test_stage_manifest_shared_quote_is_inside_cut_and_normalizes_documents_once(monkeypatch):
    from app.services import document_selection

    documents = [
        {"id": "1", "filename": "first", "text": "Shared quote"},
        {"id": "2", "filename": "second", "text": "Shared quote with more text"},
    ]
    monkeypatch.setattr(document_selection.settings, "max_total_document_words", 2)
    with patch.object(document_selection, "_normalized", wraps=document_selection._normalized) as normalize:
        manifest = document_selection.stage_manifest(
            documents, [documents[0]], ordering="upload", control_ids=["control"],
            evidence={"control": ["shared quote", "more text"]},
        )

    passages = manifest["judge"]["passages"]["control"]
    assert [entry["outside_cut"] for entry in passages] == [False, False, True]
    assert sum(call.args == (documents[0]["text"],) for call in normalize.call_args_list) == 1
    assert sum(call.args == (documents[1]["text"],) for call in normalize.call_args_list) == 1


def test_screening_call_seam_returns_provider_text():
    from app.services.screening import _call_claude_screening

    with patch(
        "app.services.screening._call_llm",
        return_value=_response('{"inferences": {}}'),
    ):
        assert _call_claude_screening("system", "prompt") == '{"inferences": {}}'


def test_screening_parser_returns_empty_for_malformed_response():
    from app.services.screening import _parse_inferences

    assert _parse_inferences("not json") == {}

def test_screening_parser_normalizes_invalid_enum_and_drops_unknown_requirement():
    from app.services.screening import _parse_inferences

    result = _parse_inferences(
        json.dumps(
            {
                "inferences": {
                    "CH2.CONSENT.1": {
                        "compliance_status": "maybe",
                        "confidence": "certain",
                        "reasoning": "bad enum",
                    },
                    "UNKNOWN.REQUIREMENT": {
                        "compliance_status": "compliant",
                        "confidence": "high",
                    },
                }
            }
        )
    )

    assert result["CH2.CONSENT.1"] == {
        "compliance_status": "not_assessed",
        "confidence": "low",
        "reasoning": "bad enum",
    }
    assert "UNKNOWN.REQUIREMENT" not in result


def test_context_profile_call_seam_returns_provider_text():
    from app.services.context_profiler import _call_claude_context_profile

    with patch(
        "app.services.context_profiler._call_llm",
        return_value=_response('{"risk_tier": "LOW"}'),
    ):
        assert _call_claude_context_profile("prompt") == '{"risk_tier": "LOW"}'


def test_context_profile_merges_deterministic_signals():
    from app.services import context_profiler

    answers = [
        {"question_id": "CTX.RISK.1", "answer": ["processes_childrens_data"]},
        {"question_id": "CTX.DATA.4", "answer": "yes"},
        {"question_id": "CTX.RISK.3", "answer": "no"},
    ]
    with patch.object(
        context_profiler,
        "_call_claude_context_profile",
        return_value='{"risk_tier": "MEDIUM", "priority_chapters": []}',
    ):
        result = context_profiler.derive_risk_profile(answers, "saas", "sme")

    assert result["risk_tier"] == "MEDIUM"
    assert result["processes_children_data"] is True
    assert result["cross_border_transfers"] is True
    assert result["has_breach_response"] is False


def test_context_profile_malformed_json_raises_json_decode_error():
    from app.services import context_profiler

    with patch.object(context_profiler, "_call_claude_context_profile", return_value="not json"):
        with pytest.raises(json.JSONDecodeError):
            context_profiler.derive_risk_profile([], "saas", "sme")


def test_context_profile_filters_unknown_ids_and_caps_likely_not_applicable(caplog):
    from app.frameworks.definitions.dpdpa import DPDPA_DEFINITION
    from app.services import context_profiler

    valid_id = DPDPA_DEFINITION.all_controls()[0].id
    proposed_ids = [valid_id] * (context_profiler.MAX_LIKELY_NOT_APPLICABLE + 1)
    proposed_ids.append("CH4.SDF.100")
    raw = json.dumps({"likely_not_applicable": proposed_ids})

    with patch.object(context_profiler, "_call_claude_context_profile", return_value=raw):
        with caplog.at_level("WARNING"):
            result = context_profiler.derive_risk_profile([], "saas", "sme")

    assert len(result["likely_not_applicable"]) == context_profiler.MAX_LIKELY_NOT_APPLICABLE
    assert set(result["likely_not_applicable"]) == {valid_id}
    assert "CH4.SDF.100" in caplog.text


def test_followup_generation_tags_and_caps_questions():
    from app.services import followup_engine

    raw = json.dumps(
        {
            "followups": [
                {"text": "One", "reason": "First"},
                {"text": "Two", "reason": "Second"},
                {"text": "Three", "reason": "Third"},
            ]
        }
    )
    with patch.object(followup_engine, "_call_claude_followups", return_value=raw):
        result = followup_engine.generate_followups(
            "Is it implemented?",
            "CH2.CONSENT.1",
            "not_implemented",
            "critical",
            ["CH2.CONSENT.1"],
            framework_ids=["dpdpa"],
        )

    assert result == [
        {
            "id": "FU.CH2.CONSENT.1.1",
            "text": "One",
            "reason": "First",
            "parent_question_id": "CH2.CONSENT.1",
        },
        {
            "id": "FU.CH2.CONSENT.1.2",
            "text": "Two",
            "reason": "Second",
            "parent_question_id": "CH2.CONSENT.1",
        },
    ]


def test_followup_generation_returns_empty_for_malformed_response():
    from app.services import followup_engine

    with patch.object(followup_engine, "_call_claude_followups", return_value="not json"):
        result = followup_engine.generate_followups(
            "Is it implemented?", "CH2.CONSENT.1", "planned", "low", [],
            framework_ids=["dpdpa"],
        )

    assert result == []


def test_followup_generation_skips_provider_for_non_triggering_answer():
    from app.services import followup_engine

    with patch.object(followup_engine, "_call_claude_followups") as call:
        result = followup_engine.generate_followups(
            "Is it implemented?", "CH2.CONSENT.1", "not_applicable", "critical", [],
            framework_ids=["dpdpa"],
        )

    assert result == []
    call.assert_not_called()


def test_followup_call_seam_returns_provider_text():
    from app.services.followup_engine import _call_claude_followups

    with patch(
        "app.services.followup_engine._call_llm",
        return_value=_response('{"followups": []}'),
    ):
        assert _call_claude_followups("prompt", system="system") == '{"followups": []}'


def test_vision_call_seam_returns_provider_text():
    from app.services.document_processor import _call_claude_vision

    with patch(
        "app.services.document_processor._call_llm",
        return_value=_response("VISIBLE TEXT: hello"),
    ):
        assert _call_claude_vision("aGVsbG8=", "image/png") == "VISIBLE TEXT: hello"


def test_vision_call_uses_vision_tier_with_openai_shaped_image_block():
    """The vision call is the one call site whose request has structure worth
    asserting directly (an image content block, not just a text prompt): it must
    route through the dedicated `vision` tier (the text tiers aren't vision-capable)
    and send OpenRouter/OpenAI's `image_url` data-URI shape, not Anthropic's native
    `type: image, source: {...}` block — llm_client.call_llm forwards content as-is,
    so a caller sending the wrong shape would silently break at the real provider."""
    from app.services.document_processor import _call_claude_vision

    captured = {}

    def _capture(tier, **kwargs):
        captured["tier"] = tier
        captured.update(kwargs)
        return _response("VISIBLE TEXT: hi")

    with patch("app.services.document_processor.llm_client.call_llm", side_effect=_capture):
        _call_claude_vision("aGVsbG8=", "image/png")

    assert captured["tier"] == "vision"
    content_blocks = captured["messages"][0]["content"]
    image_block = next(block for block in content_blocks if block["type"] == "image_url")
    assert image_block["image_url"] == {"url": "data:image/png;base64,aGVsbG8="}


def test_extract_image_keeps_non_json_vision_text(tmp_path):
    from app.services import document_processor

    image_path = tmp_path / "screen.png"
    image_path.write_bytes(b"not a real png")
    with patch.object(document_processor, "_call_claude_vision", return_value="plain text"):
        result = document_processor._extract_image(str(image_path), "png")

    assert result == "[Screenshot: screen.png]\n\nplain text"


def test_extract_image_passes_empty_image_as_empty_base64_payload(tmp_path):
    from app.services import document_processor

    image_path = tmp_path / "empty.jpg"
    image_path.write_bytes(b"")
    with patch.object(document_processor, "_call_claude_vision", return_value="empty result") as call:
        result = document_processor._extract_image(str(image_path), "jpg")

    call.assert_called_once_with("", "image/jpeg")
    assert result == "[Screenshot: empty.jpg]\n\nempty result"
