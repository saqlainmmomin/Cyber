"""Contract tests for P6-1 LLM plumbing and restart recovery."""

from __future__ import annotations

import asyncio
import inspect
import json
import subprocess
import threading
import time
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import Base


def _usage(input_tokens: int = 12, output_tokens: int = 7):
    return SimpleNamespace(
        prompt_tokens=input_tokens,
        completion_tokens=output_tokens,
        prompt_tokens_details=SimpleNamespace(cached_tokens=3),
    )


def _response(text: str = '{"ok": true}', *, finish_reason: str = "stop"):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=text),
                finish_reason=finish_reason,
            )
        ],
        usage=_usage(),
    )


def _stream_response(text: str = '{"ok": true}'):
    return iter(
        [
            SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        delta=SimpleNamespace(content=text), finish_reason="stop"
                    )
                ],
                usage=None,
            ),
            SimpleNamespace(choices=[], usage=_usage()),
        ]
    )


@pytest.fixture(autouse=True)
def _register_frameworks():
    from app.main import _register_frameworks

    _register_frameworks()


def test_client_config_uses_timeout_and_retries(monkeypatch):
    from app.services import llm_client

    captured = {}

    class FakeOpenAI:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(llm_client, "OpenAI", FakeOpenAI)
    monkeypatch.setattr(settings, "llm_timeout_seconds", 17.5)
    monkeypatch.setattr(settings, "llm_max_retries", 6)
    monkeypatch.setattr(llm_client, "_client", None)

    assert isinstance(llm_client._get_client(), FakeOpenAI)
    assert captured["timeout"] == 17.5
    assert captured["max_retries"] == 6


def test_no_schema_request_shape_is_unchanged_for_stream_and_non_stream(monkeypatch):
    from app.services import llm_client

    captured = []

    def create(**kwargs):
        captured.append(kwargs)
        return _stream_response() if kwargs.get("stream") else _response()

    fake_client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create))
    )
    monkeypatch.setattr(llm_client, "_client", fake_client)

    llm_client.call_llm("judge", system="sys", messages=[], max_tokens=10)
    llm_client.call_llm("judge", system="sys", messages=[], max_tokens=10, stream=True)

    assert captured == [
        {
            "model": settings.llm_model_judge,
            "messages": [{"role": "system", "content": "sys"}],
            "max_tokens": 10,
            "temperature": 0,
            "extra_body": llm_client._REQUEST_PREFS,
        },
        {
            "model": settings.llm_model_judge,
            "messages": [{"role": "system", "content": "sys"}],
            "max_tokens": 10,
            "temperature": 0,
            "stream": True,
            "stream_options": {"include_usage": True},
            "extra_body": llm_client._REQUEST_PREFS,
        },
    ]


def test_schema_request_is_provider_agnostic_and_does_not_mutate_preferences(monkeypatch):
    from app.services import llm_client

    captured = {}

    def create(**kwargs):
        captured.update(kwargs)
        return _response()

    fake_client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create))
    )
    monkeypatch.setattr(llm_client, "_client", fake_client)
    original_prefs = json.loads(json.dumps(llm_client._REQUEST_PREFS))

    llm_client.call_llm(
        "judge",
        system="sys",
        messages=[],
        max_tokens=10,
        response_schema={"name": "assessment", "schema": {"type": "object"}},
    )

    assert captured["response_format"] == {
        "type": "json_schema",
        "json_schema": {
            "name": "assessment",
            "strict": True,
            "schema": {"type": "object"},
        },
    }
    assert captured["extra_body"]["provider"] == {
        "data_collection": "deny",
        "zdr": True,
        "require_parameters": True,
    }
    assert llm_client._REQUEST_PREFS == original_prefs


def test_call_recording_tags_errors_and_nested_collectors(monkeypatch):
    from app.services import llm_client

    should_fail = {"value": False}

    def create(**_kwargs):
        if should_fail["value"]:
            raise TimeoutError("provider timeout")
        return _response()

    fake_client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create))
    )
    monkeypatch.setattr(llm_client, "_client", fake_client)

    with llm_client.collect_calls() as calls:
        with llm_client.call_tag(stage="judge", framework_id="iso27001"):
            llm_client.call_llm("judge", system="sys", messages=[], max_tokens=10)

    assert len(calls) == 1
    assert set(calls[0]) == {
        "tier",
        "model",
        "stage",
        "framework_id",
        "input_tokens",
        "output_tokens",
        "cache_read_input_tokens",
        "latency_ms",
        "finish_reason",
        "status",
        "error_type",
    }
    assert calls[0]["tier"] == "judge"
    assert calls[0]["model"] == settings.llm_model_judge
    assert calls[0]["stage"] == "judge"
    assert calls[0]["framework_id"] == "iso27001"
    assert calls[0]["input_tokens"] == 12
    assert calls[0]["output_tokens"] == 7
    assert calls[0]["cache_read_input_tokens"] == 3
    assert calls[0]["status"] == "ok"
    assert calls[0]["error_type"] is None
    assert calls[0]["latency_ms"] >= 0

    should_fail["value"] = True
    with llm_client.collect_calls() as error_calls:
        with pytest.raises(TimeoutError):
            llm_client.call_llm("judge", system="sys", messages=[], max_tokens=10)
    assert error_calls[0]["status"] == "error"
    assert error_calls[0]["error_type"] == "TimeoutError"
    assert error_calls[0]["input_tokens"] == 0
    assert error_calls[0]["output_tokens"] == 0

    should_fail["value"] = False
    with llm_client.collect_calls() as outer:
        with llm_client.collect_calls() as inner:
            llm_client.call_llm("judge", system="sys", messages=[], max_tokens=10)
    assert outer == []
    assert len(inner) == 1

    with llm_client.collect_calls() as unused:
        pass
    llm_client.call_llm("judge", system="sys", messages=[], max_tokens=10)
    assert unused == []


def test_run_bounded_order_errors_threads_and_context_propagation(monkeypatch):
    from app.services import llm_client
    from app.services.parallel import run_bounded

    caller_thread = threading.get_ident()
    assert run_bounded(lambda item: threading.get_ident(), [1], max_workers=1) == [
        (caller_thread, None)
    ]
    assert run_bounded(
        lambda item: item if item != 2 else (_ for _ in ()).throw(ValueError("bad")),
        [1, 2, 3],
        max_workers=1,
    )[1][1].args == ("bad",)

    barrier = threading.Barrier(3)

    def blocked(item):
        barrier.wait(timeout=2)
        return item

    assert run_bounded(blocked, [1, 2, 3], max_workers=3) == [
        (1, None),
        (2, None),
        (3, None),
    ]

    with llm_client.collect_calls() as calls:
        def worker(item):
            with llm_client.call_tag(stage="judge", framework_id=item):
                return llm_client.call_llm(
                    "judge", system="sys", messages=[], max_tokens=10
                )["text"]

        monkeypatch.setattr(llm_client, "_client", SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(create=lambda **_kwargs: _response())
            )
        ))
        results = run_bounded(worker, ["dpdpa", "iso27001"], max_workers=2)

    assert all(error is None for _, error in results)
    assert {call["framework_id"] for call in calls} == {"dpdpa", "iso27001"}


def _run_multi(monkeypatch, concurrency: int, *, fail_iso: bool = False):
    from app.services import claude_analyzer

    monkeypatch.setattr(settings, "llm_max_concurrency", concurrency)
    monkeypatch.setattr(claude_analyzer, "validate_and_filter", lambda parsed, _ids: parsed)
    in_flight = {"value": 0, "max": 0}
    lock = threading.Lock()

    def fake_call(*, tier, system, **_kwargs):
        if tier == "synthesize":
            return {
                "text": json.dumps({"unified_executive_summary": "summary"}),
                "usage": {
                    "input_tokens": 1,
                    "output_tokens": 1,
                    "cache_read_input_tokens": 0,
                    "cache_creation_input_tokens": 0,
                },
            }
        system_text = json.dumps(system)
        framework_id = (
            "iso27001" if "ISO/IEC 27001" in system_text
            else "nist_csf" if "NIST Cybersecurity Framework" in system_text
            else "dpdpa"
        )
        if fail_iso and framework_id == "iso27001":
            raise RuntimeError("iso unavailable")
        with lock:
            in_flight["value"] += 1
            in_flight["max"] = max(in_flight["max"], in_flight["value"])
        time.sleep(0.03)
        with lock:
            in_flight["value"] -= 1
        return {
            "text": json.dumps({"executive_summary": framework_id, "assessments": []}),
            "usage": {
                "input_tokens": 2,
                "output_tokens": 3,
                "cache_read_input_tokens": 0,
                "cache_creation_input_tokens": 0,
            },
        }

    monkeypatch.setattr(claude_analyzer, "_call_llm", fake_call)
    result = claude_analyzer.run_multi_framework_analysis(
        ["dpdpa", "iso27001", "nist_csf"],
        "Acme",
        "technology",
        "small",
        None,
        [],
        [],
    )
    return result, in_flight["max"]


def test_multi_framework_analysis_is_ordered_equivalent_and_concurrent(monkeypatch):
    sequential, sequential_max = _run_multi(monkeypatch, 1)
    concurrent, concurrent_max = _run_multi(monkeypatch, 4)
    assert sequential == concurrent
    assert sequential_max == 1
    assert concurrent_max > 1

    sequential_failed, _ = _run_multi(monkeypatch, 1, fail_iso=True)
    concurrent_failed, _ = _run_multi(monkeypatch, 4, fail_iso=True)
    assert sequential_failed == concurrent_failed
    assert sequential_failed["frameworks"]["iso27001"]["error"] == "iso unavailable"


def test_desk_review_preserves_partial_failure_and_records_calls(monkeypatch, tmp_path):
    from app.models.assessment import Assessment, AssessmentDocument
    from app.services import desk_review, llm_client

    engine = create_engine(f"sqlite:///{tmp_path / 'desk-review.sqlite3'}")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    assessment = Assessment(
        company_name="Acme",
        industry="technology",
        company_size="small",
        selected_frameworks=json.dumps(["dpdpa", "iso27001"]),
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

    result_text = json.dumps(
        {
            "document_catalog": [],
            "evidence_map": {},
            "absence_findings": [],
            "signal_flags": [],
            "coverage_summary": {},
        }
    )

    def create(**kwargs):
        if "ISO" in str(kwargs):
            raise RuntimeError("iso unavailable")
        if kwargs.get("stream"):
            return _stream_response(result_text)
        return _response(result_text)

    monkeypatch.setattr(
        llm_client,
        "_client",
        SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create))),
    )

    monkeypatch.setattr(settings, "llm_max_concurrency", 4)
    summary = desk_review.run_desk_review(assessment.id, db)
    raw = json.loads(summary.raw_ai_response)
    assert summary.status == "completed"
    assert "Desk review failed for" in summary.error_message
    assert raw["frameworks"]["dpdpa"]["status"] == "completed"
    assert raw["frameworks"]["iso27001"]["status"] == "error"
    assert {call["framework_id"] for call in raw["llm_calls"]} == {"dpdpa", "iso27001"}
    assert any(call["status"] == "error" for call in raw["llm_calls"])

    monkeypatch.setattr(settings, "llm_max_concurrency", 1)
    sequential = desk_review.run_desk_review(assessment.id, db)
    sequential_raw = json.loads(sequential.raw_ai_response)
    assert {
        framework_id: value
        for framework_id, value in raw["frameworks"].items()
    } == sequential_raw["frameworks"]
    db.close()


def test_three_framework_desk_review_is_concurrent_and_order_equivalent(monkeypatch, tmp_path):
    from app.models.assessment import Assessment, AssessmentDocument
    from app.services import desk_review

    engine = create_engine(f"sqlite:///{tmp_path / 'desk-review-concurrency.sqlite3'}")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    assessment = Assessment(
        company_name="Acme",
        industry="technology",
        company_size="small",
        selected_frameworks=json.dumps(["dpdpa", "iso27001", "nist_csf"]),
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

    def run_once(concurrency: int):
        active = {"value": 0, "max": 0}
        lock = threading.Lock()
        barrier = threading.Barrier(3)

        def enter():
            with lock:
                active["value"] += 1
                active["max"] = max(active["max"], active["value"])
            if concurrency > 1:
                barrier.wait(timeout=2)

        def leave():
            with lock:
                active["value"] -= 1

        def result(framework_id: str):
            enter()
            try:
                return {
                    "document_catalog": [
                        {
                            "filename": "policy.txt",
                            "document_type": framework_id,
                            "coverage_areas": [],
                            "summary": framework_id,
                        }
                    ],
                    "evidence_map": {},
                    "absence_findings": [],
                    "signal_flags": [],
                    "coverage_summary": {},
                }
            finally:
                leave()

        monkeypatch.setattr(
            desk_review,
            "_call_claude_desk_review",
            lambda **_kwargs: result("dpdpa"),
        )
        monkeypatch.setattr(
            desk_review,
            "_call_framework_desk_review",
            lambda framework_id, *_args, **_kwargs: result(framework_id),
        )
        monkeypatch.setattr(settings, "llm_max_concurrency", concurrency)
        summary = desk_review.run_desk_review(assessment.id, db)
        return json.loads(summary.raw_ai_response)["frameworks"], active["max"]

    sequential, sequential_max = run_once(1)
    concurrent, concurrent_max = run_once(4)
    assert concurrent == sequential
    assert sequential_max == 1
    assert concurrent_max > 1
    db.close()


def test_temperature_zero_and_synthesis_prompt_contract(monkeypatch):
    from app.frameworks.prompts import build_synthesis_prompt
    from app.services import document_processor, screening

    temperatures = []

    def capture(**kwargs):
        temperatures.append(kwargs["temperature"])
        return {"text": "{}", "usage": {}}

    monkeypatch.setattr(screening, "_call_llm", lambda **kwargs: capture(**kwargs))
    monkeypatch.setattr(document_processor, "_call_llm", lambda **kwargs: capture(**kwargs))
    screening._call_claude_screening("system", "prompt")
    document_processor._call_claude_vision("data", "image/png")
    assert temperatures == [0, 0]

    prompt = build_synthesis_prompt({"iso27001": {"assessments": []}}, "Acme", "SaaS")
    assert "framework_comparison" in prompt
    assert "estimated_score" not in prompt
    assert "0-100" not in prompt


def test_analysis_pipeline_explicitly_splits_framework_and_shared_call_records(monkeypatch, tmp_path):
    from app.models.assessment import Assessment
    from app.services import analysis_pipeline
    from app.services import llm_client

    engine = create_engine(f"sqlite:///{tmp_path / 'pipeline.sqlite3'}")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    assessment = Assessment(
        company_name="Acme",
        industry="technology",
        company_size="small",
        selected_frameworks=json.dumps(["dpdpa", "iso27001"]),
    )
    db.add(assessment)
    db.flush()
    context = analysis_pipeline.start_runs(
        db, assessment_id=assessment.id, framework_ids=["dpdpa", "iso27001"]
    )
    monkeypatch.setattr(
        llm_client,
        "_client",
        SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(create=lambda **_kwargs: _response())
            )
        ),
    )
    with llm_client.collect_calls() as calls:
        with llm_client.call_tag(stage="judge", framework_id="dpdpa"):
            llm_client.call_llm("judge", system="sys", messages=[], max_tokens=10)
        with llm_client.call_tag(stage="judge", framework_id="iso27001"):
            llm_client.call_llm("judge", system="sys", messages=[], max_tokens=10)
        with llm_client.call_tag(stage="synthesis"):
            llm_client.call_llm("synthesize", system="sys", messages=[], max_tokens=10)
    analysis_pipeline.record_framework_run(
        db,
        context,
        framework_id="dpdpa",
        assessments=[],
        desk_review_data=None,
        gap_report_id="report",
        llm_calls=calls,
    )
    analysis_pipeline.record_framework_run(
        db,
        context,
        framework_id="iso27001",
        assessments=[],
        desk_review_data=None,
        gap_report_id="report",
        llm_calls=calls,
    )
    db.commit()

    envelopes = [json.loads(run.claims_json) for run in db.query(analysis_pipeline.AnalysisRun).all()]
    assert [len(envelope["llm_calls"]) for envelope in envelopes] == [1, 1]
    assert len(envelopes[0]["shared_llm_calls"]) == 1
    assert "shared_llm_calls" not in envelopes[1]
    db.close()


def test_analysis_route_persists_own_and_shared_call_records(monkeypatch, tmp_path):
    from app.models.assessment import Assessment
    from app.models.analysis_run import AnalysisRun
    from app.routers import analysis as analysis_router
    from app.services import claude_analyzer
    from app.services import llm_client

    engine = create_engine(f"sqlite:///{tmp_path / 'analysis-route.sqlite3'}")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    assessment = Assessment(
        company_name="Acme",
        industry="technology",
        company_size="small",
        selected_frameworks=json.dumps(["dpdpa", "iso27001"]),
    )
    db.add(assessment)
    db.commit()

    def create(**kwargs):
        text = '{"assessments": [], "executive_summary": ""}'
        return _stream_response(text) if kwargs.get("stream") else _response(text)

    monkeypatch.setattr(
        llm_client,
        "_client",
        SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=create))
        ),
    )
    monkeypatch.setattr(
        claude_analyzer,
        "validate_and_filter",
        lambda _parsed, _known_ids: {"assessments": [], "executive_summary": ""},
    )
    analysis_router._run_multi_framework_analysis(
        assessment=assessment,
        assessment_id=assessment.id,
        responses=[],
        documents=[],
        context_profile=None,
        desk_review_data=None,
        applicable_requirements=None,
        selected_frameworks=["dpdpa", "iso27001"],
        has_documents=False,
        db=db,
    )

    runs = db.query(AnalysisRun).filter_by(assessment_id=assessment.id).all()
    envelopes = {run.framework_id: json.loads(run.claims_json) for run in runs}
    assert len(envelopes["dpdpa"]["llm_calls"]) == 1
    assert len(envelopes["iso27001"]["llm_calls"]) == 1
    assert len(envelopes["dpdpa"]["shared_llm_calls"]) == 1
    assert "shared_llm_calls" not in envelopes["iso27001"]
    assert sum(
        len(envelope["llm_calls"])
        + len(envelope.get("shared_llm_calls", []))
        for envelope in envelopes.values()
    ) == 3
    db.close()


def test_recovery_is_idempotent_and_lifespan_setting_can_disable_it(monkeypatch, tmp_path):
    from app import database, main
    from app.models.analysis_run import AnalysisRun
    from app.models.assessment import Assessment
    from app.models.desk_review import DeskReviewSummary
    from app.services.run_recovery import recover_interrupted_work

    engine = create_engine(f"sqlite:///{tmp_path / 'recovery.sqlite3'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    seed = factory()
    active = Assessment(
        company_name="Active",
        industry="technology",
        company_size="small",
        status="analyzing",
        desk_review_status="analyzing",
    )
    terminal = Assessment(
        company_name="Terminal",
        industry="technology",
        company_size="small",
        status="completed",
        desk_review_status="completed",
    )
    seed.add_all([active, terminal])
    seed.flush()
    started = datetime(2026, 1, 1, tzinfo=timezone.utc)
    interrupted = AnalysisRun(
        assessment_id=active.id,
        framework_id="dpdpa",
        status="running",
        claims_json=json.dumps({"claims": ["old"], "error": None}),
        model_id="model",
        started_at=started,
    )
    completed = AnalysisRun(
        assessment_id=terminal.id,
        framework_id="dpdpa",
        status="completed",
        claims_json=json.dumps({"claims": ["keep"], "error": None}),
        model_id="model",
        started_at=started,
        completed_at=started,
    )
    seed.add_all([
        interrupted,
        completed,
        DeskReviewSummary(assessment_id=active.id, status="analyzing"),
        DeskReviewSummary(assessment_id=terminal.id, status="completed", error_message="keep"),
    ])
    seed.commit()
    interrupted_id = interrupted.id
    completed_id = completed.id
    active_id = active.id
    terminal_id = terminal.id
    before_terminal = (
        terminal.status,
        terminal.desk_review_status,
        completed.status,
        completed.claims_json,
        completed.completed_at,
    )
    seed.close()

    monkeypatch.setattr(database, "SessionLocal", factory)
    assert recover_interrupted_work() == {
        "analysis_runs": 1,
        "assessments": 1,
        "desk_review_assessments": 1,
        "desk_review_summaries": 1,
    }
    check = factory()
    assert check.get(AnalysisRun, interrupted_id).status == "failed"
    interrupted_env = json.loads(check.get(AnalysisRun, interrupted_id).claims_json)
    assert interrupted_env == {"claims": [], "error": {"type": "Interrupted"}}
    assert check.get(AnalysisRun, interrupted_id).completed_at is not None
    assert check.get(Assessment, active_id).status == "error"
    assert check.get(Assessment, active_id).desk_review_status == "error"
    active_summary = check.query(DeskReviewSummary).filter_by(assessment_id=active_id).one()
    assert active_summary.error_message == (
        "Desk review was interrupted by a restart. Run desk review again."
    )
    terminal_row = check.get(Assessment, terminal_id)
    terminal_run = check.get(AnalysisRun, completed_id)
    assert (
        terminal_row.status,
        terminal_row.desk_review_status,
        terminal_run.status,
        terminal_run.claims_json,
        terminal_run.completed_at,
    ) == before_terminal
    check.close()
    assert recover_interrupted_work() == {
        "analysis_runs": 0,
        "assessments": 0,
        "desk_review_assessments": 0,
        "desk_review_summaries": 0,
    }

    monkeypatch.setattr(main.settings, "recover_interrupted_on_startup", False)
    monkeypatch.setattr(main, "_run_alembic_upgrade", lambda: None)
    monkeypatch.setattr(main, "_register_frameworks", lambda: None)
    monkeypatch.setattr(main, "_assert_framework_catalog_complete", lambda: None)
    monkeypatch.setattr(
        main,
        "recover_interrupted_work",
        lambda: pytest.fail("recovery should be disabled"),
    )

    async def start_app():
        async with main.lifespan(None):
            pass

    asyncio.run(start_app())


def test_golden_surfaces_and_harness_wrapper(monkeypatch):
    from app.services import llm_client

    diff = subprocess.run(
        # Three-dot diff: only this branch's own changes since it left main, so the
        # guard stays true after merge instead of going stale.
        ["git", "diff", "--stat", "main...HEAD", "--", "tests/fixtures", "tests/support"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert diff.stdout.strip() == ""

    monkeypatch.setattr(llm_client, "_client", SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=lambda **_kwargs: _response())
        )
    ))
    original = llm_client.call_llm
    original_signature = inspect.signature(original)

    def wrapper(tier, **kwargs):
        return original(tier, **kwargs)

    monkeypatch.setattr(llm_client, "call_llm", wrapper)
    with llm_client.collect_calls() as calls:
        wrapper("judge", system="sys", messages=[], max_tokens=10)
    assert len(calls) == 1
    assert original_signature.parameters["response_schema"].default is None
