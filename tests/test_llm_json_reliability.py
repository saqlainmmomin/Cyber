"""LLM JSON reliability: desk review and evidence extraction ask for JSON,
record a non-JSON reply as a parse failure, and retry it once.

Seen live: 4 of 148 OpenRouter calls returned a Markdown report with
finish_reason="stop"; the call records said "ok" and evidence extraction fell
back to full documents with nothing recording why.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import Base

MARKDOWN = "# Compliance Report\n\n## Summary\n\nThe policy covers access control."
DOCS = [
    {
        "filename": "policy.pdf",
        "category": "policy",
        "text": "Access is reviewed quarterly by the security team.",
    }
]
DESK_RESULT = {
    "document_catalog": [],
    "evidence_map": {},
    "absence_findings": [],
    "signal_flags": [],
    "coverage_summary": {},
}
ZDR_PREFS = {
    "provider": {"data_collection": "deny", "zdr": True},
    "reasoning": {"enabled": False},
}


@pytest.fixture(autouse=True)
def _register_frameworks():
    from app.main import _register_frameworks

    _register_frameworks()


def _usage():
    return SimpleNamespace(prompt_tokens=10, completion_tokens=5, prompt_tokens_details=None)


def _reply(text, stream):
    if stream:
        return iter(
            [
                SimpleNamespace(
                    choices=[SimpleNamespace(delta=SimpleNamespace(content=text), finish_reason="stop")],
                    usage=None,
                ),
                SimpleNamespace(choices=[], usage=_usage()),
            ]
        )
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=text), finish_reason="stop")],
        usage=_usage(),
    )


def _install(monkeypatch, texts):
    """Fake OpenRouter client replying with `texts` in order (last one repeats)."""
    from app.services import llm_client

    captured: list[dict] = []

    def create(**kwargs):
        captured.append(kwargs)
        text = texts[min(len(captured), len(texts)) - 1]
        return _reply(text, kwargs.get("stream", False))

    monkeypatch.setattr(
        llm_client,
        "_client",
        SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create))),
    )
    return captured


# --- llm_client ----------------------------------------------------------------


def test_json_output_requests_json_object_without_narrowing_the_provider_pool(monkeypatch):
    """json_object without require_parameters: ZDR prefs are exactly the plain
    request's, so the routable provider pool cannot shrink."""
    from app.services import llm_client

    captured = _install(monkeypatch, ['{"ok": true}'])
    llm_client.call_llm("judge", system="s", messages=[], max_tokens=10, json_output=True)
    llm_client.call_llm("judge", system="s", messages=[], max_tokens=10)

    assert captured[0]["response_format"] == {"type": "json_object"}
    assert captured[0]["extra_body"] == ZDR_PREFS
    assert "response_format" not in captured[1]
    assert captured[1]["extra_body"] == ZDR_PREFS
    assert llm_client._REQUEST_PREFS == ZDR_PREFS


def test_markdown_reply_is_recorded_as_parse_error_and_retried(monkeypatch):
    from app.services import llm_client

    captured = _install(monkeypatch, [MARKDOWN, '{"ok": true}'])
    with llm_client.collect_calls() as calls, llm_client.call_tag(stage="desk_review"):
        result = llm_client.call_llm(
            "judge", system="s", messages=[], max_tokens=10, json_output=True
        )

    assert result["text"] == '{"ok": true}'
    assert len(captured) == 2
    assert captured[0] == captured[1]
    assert [call["status"] for call in calls] == ["parse_error", "ok"]
    assert calls[0]["error_type"] == "JSONDecodeError"
    assert calls[0]["finish_reason"] == "stop"
    assert calls[0]["output_tokens"] == 5
    assert "attempt" not in calls[0]
    assert calls[1]["attempt"] == 2


def test_persistent_markdown_raises_after_one_retry(monkeypatch):
    from app.services import llm_client

    captured = _install(monkeypatch, [MARKDOWN])
    with llm_client.collect_calls() as calls:
        with pytest.raises(llm_client.LLMOutputParseError, match="not valid JSON after 2 attempts"):
            llm_client.call_llm("extract", system="s", messages=[], max_tokens=10, json_output=True)

    assert len(captured) == 2
    assert [call["status"] for call in calls] == ["parse_error", "parse_error"]
    assert isinstance(llm_client.LLMOutputParseError("x"), ValueError)


def test_fenced_json_is_not_a_parse_failure_and_plain_calls_are_not_checked(monkeypatch):
    from app.services import llm_client

    captured = _install(monkeypatch, ["```json\n{\"ok\": true}\n```"])
    with llm_client.collect_calls() as calls:
        llm_client.call_llm("judge", system="s", messages=[], max_tokens=10, json_output=True)
    assert len(captured) == 1 and calls[0]["status"] == "ok"

    captured = _install(monkeypatch, [MARKDOWN])
    with llm_client.collect_calls() as calls:
        assert llm_client.call_llm("vision", system="s", messages=[], max_tokens=10)["text"] == MARKDOWN
    assert len(captured) == 1 and calls[0]["status"] == "ok"


# --- evidence extraction --------------------------------------------------------


@pytest.mark.parametrize("framework_id", ["dpdpa", "nist_csf", "iso27001"])
def test_evidence_extraction_records_parse_failure_retries_and_falls_back(monkeypatch, framework_id):
    from app.services import claude_analyzer, llm_client

    captured = _install(monkeypatch, [MARKDOWN])
    with llm_client.collect_calls() as calls:
        evidence = claude_analyzer._run_framework_evidence_extraction(framework_id, DOCS)

    assert evidence is None  # falls back to full documents
    assert len(captured) == 2
    assert all(call["response_format"] == {"type": "json_object"} for call in captured)
    assert [call["status"] for call in calls] == ["parse_error", "parse_error"]
    assert {call["stage"] for call in calls} == {"evidence_extraction"}


@pytest.mark.parametrize("framework_id", ["dpdpa", "nist_csf"])
def test_evidence_extraction_uses_the_retry_when_it_parses(monkeypatch, framework_id):
    from app.frameworks.registry import FrameworkRegistry
    from app.services import claude_analyzer, llm_client

    control_id = next(iter(FrameworkRegistry.get(framework_id).all_controls())).id
    good = json.dumps({"evidence": {control_id: ["Access is reviewed quarterly"]}})
    _install(monkeypatch, [MARKDOWN, good])
    with llm_client.collect_calls() as calls:
        evidence = claude_analyzer._run_framework_evidence_extraction(framework_id, DOCS)

    assert evidence and control_id in evidence
    assert [call["status"] for call in calls] == ["parse_error", "ok"]


# --- desk review -----------------------------------------------------------------


def test_curated_desk_review_retries_once_and_uses_the_retry(monkeypatch):
    from app.services import desk_review, llm_client

    captured = _install(monkeypatch, [MARKDOWN, json.dumps(DESK_RESULT)])
    with llm_client.collect_calls() as calls:
        result = desk_review._call_claude_desk_review(DOCS, "Acme", "saas")

    assert result == DESK_RESULT
    assert len(captured) == 2
    assert captured[0]["response_format"] == {"type": "json_object"}
    assert captured[0]["extra_body"] == ZDR_PREFS
    assert [call["status"] for call in calls] == ["parse_error", "ok"]


def test_framework_desk_review_stream_records_parse_failure_and_fails(monkeypatch):
    from app.services import desk_review, llm_client

    monkeypatch.setattr(settings, "llm_batch_threshold_controls", 10_000)
    captured = _install(monkeypatch, [MARKDOWN])
    with llm_client.collect_calls() as calls:
        with pytest.raises(llm_client.LLMOutputParseError):
            desk_review._call_framework_desk_review("iso27001", DOCS, "Acme", "saas")

    assert len(captured) == 2 and all(call["stream"] for call in captured)
    assert [call["status"] for call in calls] == ["parse_error", "parse_error"]


def test_stored_desk_review_call_records_show_the_parse_failure(monkeypatch, tmp_path):
    """The records persisted in raw_ai_response["llm_calls"] (the same records
    the analysis envelopes and llm_usage aggregation read) carry the failure."""
    from app.models.assessment import Assessment, AssessmentDocument
    from app.services import desk_review

    engine = create_engine(f"sqlite:///{tmp_path / 'desk-review.sqlite3'}")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    assessment = Assessment(
        company_name="Acme",
        industry="technology",
        company_size="small",
        selected_frameworks=json.dumps(["dpdpa"]),
    )
    db.add(assessment)
    db.flush()
    db.add(
        AssessmentDocument(
            assessment_id=assessment.id,
            filename="policy.txt",
            file_path="policy.txt",
            file_type="txt",
            document_category="privacy_policy",
            extracted_text="A policy document.",
        )
    )
    db.commit()

    _install(monkeypatch, [MARKDOWN])
    summary = desk_review.run_desk_review(assessment.id, db)
    raw = json.loads(summary.raw_ai_response)

    assert summary.status == "error"
    assert "not valid JSON after 2 attempts" in raw["frameworks"]["dpdpa"]["error"]
    assert [call["status"] for call in raw["llm_calls"]] == ["parse_error", "parse_error"]
    assert all(call["error_type"] == "JSONDecodeError" for call in raw["llm_calls"])
