"""Characterization coverage for LLM call sites outside claude_analyzer.

All six services route through their own module-level `_call_llm` seam (which
delegates to `app.services.llm_client.call_llm`) — patch that seam directly,
same convention `claude_analyzer.py`'s golden tests use.
"""

from __future__ import annotations

import json
from unittest.mock import patch

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


def test_desk_review_truncation_preserves_document_order_and_budget(monkeypatch):
    from app.services import desk_review

    monkeypatch.setattr(desk_review.settings, "max_total_document_words", 3)
    documents = [
        {"filename": "first", "text": "one two"},
        {"filename": "second", "text": "three four"},
    ]

    assert desk_review._truncate_documents(documents) == [
        {"filename": "first", "text": "one two"},
        {"filename": "second", "text": "three\n\n[... truncated ...]"},
    ]


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
            "Is it implemented?", "CH2.CONSENT.1", "planned", "low", []
        )

    assert result == []


def test_followup_generation_skips_provider_for_non_triggering_answer():
    from app.services import followup_engine

    with patch.object(followup_engine, "_call_claude_followups") as call:
        result = followup_engine.generate_followups(
            "Is it implemented?", "CH2.CONSENT.1", "not_applicable", "critical", []
        )

    assert result == []
    call.assert_not_called()


def test_followup_call_seam_returns_provider_text():
    from app.services.followup_engine import _call_claude_followups

    with patch(
        "app.services.followup_engine._call_llm",
        return_value=_response('{"followups": []}'),
    ):
        assert _call_claude_followups("prompt") == '{"followups": []}'


def test_rfi_call_parses_valid_json_and_preserves_raw_text():
    from app.services.rfi_generator import _call_claude_rfi

    raw = '{"items": [{"item_id": "RFI-001", "evidence_requested": "Policy"}]}'
    with patch("app.services.rfi_generator._call_llm", return_value=_response(raw)):
        result = _call_claude_rfi("Acme", "saas", [{
            "item_id": "RFI-001",
            "requirement_id": "CH2.CONSENT.1",
            "requirement_title": "Consent",
            "section_ref": "2.1",
            "priority": "High",
            "current_status": "Missing",
            "gap_description": "No policy",
        }])

    assert result["items"][0]["evidence_requested"] == "Policy"
    assert result["_raw"] == raw


def test_rfi_call_uses_empty_enhancements_for_non_json_response():
    from app.services.rfi_generator import _call_claude_rfi

    with patch("app.services.rfi_generator._call_llm", return_value=_response("not json")):
        result = _call_claude_rfi("Acme", "saas", [])

    assert result["items"] == []
    assert result["introduction"] == ""
    assert result["_raw"] == "not json"


def test_rfi_evidence_items_exclude_compliant_and_not_assessed_gaps():
    from app.services.rfi_generator import _build_evidence_items

    items = _build_evidence_items(
        [
            {"requirement_id": "CH2.CONSENT.1", "compliance_status": "compliant"},
            {"requirement_id": "CH2.CONSENT.2", "compliance_status": "not_assessed"},
            {"requirement_id": "CH2.CONSENT.3", "compliance_status": "non_compliant"},
        ],
        None,
        None,
    )

    assert [item["requirement_id"] for item in items] == ["CH2.CONSENT.3"]


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
