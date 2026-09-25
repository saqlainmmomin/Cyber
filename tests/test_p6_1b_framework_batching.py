"""Contract tests for P6-1b v1 framework batching."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import threading
import time
from contextlib import contextmanager
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import Base
from app.frameworks.batching import control_batches
from app.frameworks.registry import FrameworkRegistry
from app.frameworks.schema import Control, Domain, FrameworkDefinition, Section
from app.schemas.llm_output import IncompleteAssessmentError
from app.services import claude_analyzer, desk_review, llm_client


@pytest.fixture(autouse=True)
def _frameworks():
    from app.main import _register_frameworks

    _register_frameworks()


def _usage(input_tokens: int = 2, output_tokens: int = 3) -> dict[str, int]:
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_read_input_tokens": 0,
        "cache_creation_input_tokens": 0,
    }


def _item(requirement_id: str, status: str = "compliant") -> dict:
    return {
        "requirement_id": requirement_id,
        "compliance_status": status,
        "current_state": "state",
        "gap_description": "gap",
        "risk_level": "low",
        "remediation_action": "action",
        "remediation_priority": 3,
        "remediation_effort": "low",
        "timeline_weeks": 4,
        "maturity_level": 3,
        "root_cause_category": "process",
        "evidence_quote": "quote",
    }


def _response(ids: list[str], *, summary: str = "model", statuses=None) -> str:
    return json.dumps(
        {
            "executive_summary": summary,
            "assessments": [
                _item(control_id, statuses(index, control_id) if statuses else "compliant")
                for index, control_id in enumerate(ids)
            ],
        }
    )


def _system_text(system) -> str:
    if isinstance(system, list):
        return "\n".join(block.get("text", "") for block in system)
    return str(system)


def _prompt_control_ids(system) -> list[str]:
    text = _system_text(system)
    result = []
    for framework_id in ("dpdpa", "iso27001", "nist_csf"):
        for control in FrameworkRegistry.get(framework_id).all_controls():
            if f"**{control.id}**" in text:
                result.append(control.id)
    return result


def _framework_for_ids(ids: list[str]) -> str:
    for framework_id in ("dpdpa", "iso27001", "nist_csf"):
        if ids and ids[0] in {c.id for c in FrameworkRegistry.get(framework_id).all_controls()}:
            return framework_id
    return "unknown"


def _run_analysis(monkeypatch, fake, framework_ids=("dpdpa", "iso27001", "nist_csf"), **kwargs):
    monkeypatch.setattr(claude_analyzer, "_call_llm", fake)
    return claude_analyzer.run_multi_framework_analysis(
        list(framework_ids),
        "Acme",
        "saas",
        "sme",
        None,
        [],
        [],
        **kwargs,
    )


def test_threshold_call_counts_and_full_coverage(monkeypatch):
    monkeypatch.setattr(settings, "llm_max_concurrency", 1)
    calls = []

    def fake(*, tier, system, **_kwargs):
        ids = _prompt_control_ids(system)
        calls.append((tier, ids))
        if tier == "synthesize":
            return {"text": '{"unified_executive_summary": "summary"}', "usage": _usage()}
        return {"text": _response(ids), "usage": _usage()}

    result = _run_analysis(monkeypatch, fake)
    judge_calls = [ids for tier, ids in calls if tier == "judge"]
    assert [_framework_for_ids(ids) for ids in judge_calls].count("dpdpa") == 1
    assert [_framework_for_ids(ids) for ids in judge_calls].count("iso27001") == 6
    assert [_framework_for_ids(ids) for ids in judge_calls].count("nist_csf") == 6
    assert sum(tier == "synthesize" for tier, _ in calls) == 1
    for framework_id in ("dpdpa", "iso27001", "nist_csf"):
        expected = {c.id for c in FrameworkRegistry.get(framework_id).all_controls()}
        actual = {a["requirement_id"] for a in result["frameworks"][framework_id]["parsed"]["assessments"]}
        assert actual == expected

    calls.clear()
    monkeypatch.setattr(settings, "llm_batch_threshold_controls", 10_000)
    _run_analysis(monkeypatch, fake)
    assert sum(tier == "judge" for tier, _ in calls) == 3

    calls.clear()
    monkeypatch.setattr(settings, "llm_batch_threshold_controls", 40)
    _run_analysis(monkeypatch, fake, framework_ids=("dpdpa",))
    assert len([ids for tier, ids in calls if tier == "judge"]) == len(control_batches("dpdpa"))
    assert len(control_batches("dpdpa")) > 1


def test_unbatched_prompt_fingerprints_and_dpdpa_request_shape(monkeypatch):
    from app.frameworks import prompts

    kw = dict(
        company_name="Acme",
        industry="saas",
        company_size="sme",
        description="d",
        responses=[{"question_id": "SINGLE.ISO.A5.1", "answer": "yes"}],
        documents=[{"filename": "a.pdf", "category": "other", "text": "t"}],
        context_profile={"risk_tier": "HIGH", "industry_context": "x"},
        evidence={"ISO.A5.1": ["q"], "NIST.GV.OC.01": ["q"], "CH2.CONSENT.1": ["q"]},
        desk_review_summary={"coverage_summary": {"ISO.A5.1": "partial"}, "signal_flags": []},
        applicable_controls=None,
    )
    expected = {
        ("dpdpa", "system"): "3fc4f1c3ff6b62124716f6ca5ef29e1dd39461817d168fa4b047c2bef92e4ea6",
        ("dpdpa", "user"): "de658c512943c954425ea004165af0dd1cd88ade82f7376ac98d08aa957b3751",
        ("iso27001", "system"): "3c3bad7bd8818c1d5b28730e4462bbf91f2208b1eae32b89459e8e2d698116b3",
        ("iso27001", "user"): "6fe08745ef96857b893c623d0f468d2abca2aa6c3395affc64145807acedfd61",
        ("iso27001", "desk"): "9d2e926bae35b23030085da6e528b03df63c9352006cb0bb8948800a251222b2",
        ("nist_csf", "system"): "c8ddf65a8220b571733a65298503f3aff65be22ca6c21413216282f982ddf121",
        ("nist_csf", "user"): "9fa1ded32cda08bb882873f83bb2d13e1b20a9a1b0fa84c45690569e02bb283f",
        ("nist_csf", "desk"): "14705771d2e67febe08ab3a58e022039aea1a4360aef37a0ae0595fa25d414ec",
    }
    digest = lambda value: hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
    for framework_id in ("dpdpa", "iso27001", "nist_csf"):
        assert digest(prompts.build_framework_system_prompt(framework_id)) == expected[(framework_id, "system")]
        assert digest(prompts.build_framework_user_prompt(framework_id, **kw)) == expected[(framework_id, "user")]
        if framework_id != "dpdpa":
            assert digest(prompts.build_framework_desk_review_system_prompt(framework_id)) == expected[(framework_id, "desk")]

    seen = []

    def fake(*, tier, **request):
        seen.append((tier, request))
        ids = _prompt_control_ids(request["system"])
        return {"text": _response(ids), "usage": _usage()}

    monkeypatch.setattr(settings, "llm_batch_threshold_controls", 10_000)
    _run_analysis(monkeypatch, fake, framework_ids=("dpdpa",))
    first = seen[0][1]
    seen.clear()
    monkeypatch.setattr(settings, "llm_batch_threshold_controls", 50)
    _run_analysis(monkeypatch, fake, framework_ids=("dpdpa",))
    assert first == seen[0][1]


def test_deterministic_batch_table_and_synthetic_split(monkeypatch):
    expected = {
        "iso27001": [
            ("organizational", ("policies", "threat_intelligence", "access_identity", "supplier_relations"), 23, "ISO.A5.1", "ISO.A5.23"),
            ("organizational", ("incident_continuity", "legal_compliance"), 14, "ISO.A5.24", "ISO.A5.37"),
            ("people", ("screening_employment", "remote_work"), 8, "ISO.A6.1", "ISO.A6.8"),
            ("physical", ("perimeter_access", "equipment"), 14, "ISO.A7.1", "ISO.A7.14"),
            ("technological", ("tech_access", "tech_operations", "tech_logging"), 24, "ISO.A8.1", "ISO.A8.24"),
            ("technological", ("tech_sdlc",), 10, "ISO.A8.25", "ISO.A8.34"),
        ],
        "nist_csf": [
            ("govern", ("gv_oc", "gv_rm", "gv_rr", "gv_po", "gv_ov", "gv_sc"), 23, "NIST.GV.OC.01", "NIST.GV.SC.05"),
            ("identify", ("id_am", "id_ra", "id_im"), 16, "NIST.ID.AM.01", "NIST.ID.IM.03"),
            ("protect", ("pr_aa", "pr_at", "pr_ds", "pr_ps", "pr_ir"), 22, "NIST.PR.AA.01", "NIST.PR.IR.04"),
            ("detect", ("de_cm", "de_ae"), 11, "NIST.DE.CM.01", "NIST.DE.AE.08"),
            ("respond", ("rs_ma", "rs_an", "rs_co", "rs_mi"), 14, "NIST.RS.MA.01", "NIST.RS.MI.02"),
            ("recover", ("rc_rp", "rc_co"), 8, "NIST.RC.RP.01", "NIST.RC.CO.04"),
        ],
    }
    for framework_id, rows in expected.items():
        batches = control_batches(framework_id)
        assert [
            (b.domain_key, b.section_keys, len(b.control_ids), b.control_ids[0], b.control_ids[-1])
            for b in batches
        ] == rows
        assert [b.label for b in batches] == [f"{i}/6" for i in range(1, 7)]
        controls = [c.id for c in FrameworkRegistry.get(framework_id).all_controls()]
        assert [control_id for b in batches for control_id in b.control_ids] == controls
        assert control_batches(framework_id) == control_batches(framework_id)
    assert control_batches("dpdpa") == ()

    controls = [Control(f"SYN.{i}", f"C{i}", "d", "r", "low") for i in range(31)]
    synthetic = FrameworkDefinition(
        id="synthetic_p6_1b",
        name="Synthetic",
        version="1",
        domains={
            "domain": Domain(
                "domain",
                "Domain",
                1.0,
                {"large": Section("large", "Large", 0.5, controls[:30]), "one": Section("one", "One", 0.5, controls[30:])},
            )
        },
    )
    FrameworkRegistry.register(synthetic)
    try:
        monkeypatch.setattr(settings, "llm_batch_threshold_controls", 0)
        monkeypatch.setattr(settings, "llm_batch_max_controls", 25)
        batches = control_batches("synthetic_p6_1b")
        assert [len(batch.control_ids) for batch in batches] == [25, 6]
        assert batches[1].section_keys == ("large", "one")
    finally:
        FrameworkRegistry._frameworks.pop("synthetic_p6_1b", None)


def test_merge_order_is_definition_order_under_jitter(monkeypatch):
    monkeypatch.setattr(settings, "llm_max_concurrency", 4)
    controls = [c.id for c in FrameworkRegistry.get("iso27001").all_controls()]

    def fake(*, tier, system, **_kwargs):
        ids = _prompt_control_ids(system)
        time.sleep((len(ids) % 5) * 0.002)
        return {"text": _response(list(reversed(ids))), "usage": _usage()}

    result = _run_analysis(monkeypatch, fake, framework_ids=("iso27001",))
    assert [a["requirement_id"] for a in result["frameworks"]["iso27001"]["parsed"]["assessments"]] == controls


def test_missing_ids_retry_invalid_json_and_unbatched_fail_closed(monkeypatch):
    batches = control_batches("iso27001")
    batch_two = set(batches[1].control_ids)
    calls = []
    omitted = False

    @contextmanager
    def capture_tags(**kwargs):
        calls.append(("tag", kwargs))
        with original_call_tag(**kwargs):
            yield

    original_call_tag = llm_client.call_tag
    monkeypatch.setattr(llm_client, "call_tag", capture_tags)

    def fake(*, tier, system, **_kwargs):
        nonlocal omitted
        ids = _prompt_control_ids(system)
        calls.append((tier, ids))
        if set(ids) == batch_two and not omitted:
            omitted = True
            ids = ids[:-2]
        return {"text": _response(ids), "usage": _usage()}

    result = _run_analysis(monkeypatch, fake, framework_ids=("iso27001",))
    assert "error" not in result["frameworks"]["iso27001"]
    assert len(result["frameworks"]["iso27001"]["parsed"]["assessments"]) == 93
    assert any(tag.get("batch") == "2/6+retry" for kind, tag in calls if kind == "tag")
    retry_prompts = [ids for kind, ids in calls if kind == "judge" and len(ids) == 2]
    assert retry_prompts == [list(batches[1].control_ids)[-2:]]

    invalid_calls = []
    invalid_done = False

    def invalid_fake(*, tier, system, **_kwargs):
        nonlocal invalid_done
        ids = _prompt_control_ids(system)
        invalid_calls.append(ids)
        if len(ids) == len(batches[2].control_ids) and not invalid_done:
            invalid_done = True
            return {"text": "not json", "usage": _usage()}
        return {"text": _response(ids), "usage": _usage()}

    result = _run_analysis(monkeypatch, invalid_fake, framework_ids=("iso27001",))
    assert "error" not in result["frameworks"]["iso27001"]
    assert any(len(ids) == len(batches[2].control_ids) for ids in invalid_calls)
    assert any(len(ids) == len(batches[2].control_ids) for ids in invalid_calls[6:])

    dpdpa_calls = []

    def incomplete_legacy(*, tier, **_kwargs):
        dpdpa_calls.append(tier)
        return {"text": _response(["CH2.CONSENT.1"]), "usage": _usage()}

    monkeypatch.setattr(claude_analyzer, "_call_llm", incomplete_legacy)
    with pytest.raises(IncompleteAssessmentError, match="missing 40 of 41"):
        claude_analyzer.run_gap_analysis("Acme", "saas", "sme", None, [], [])
    assert dpdpa_calls == ["judge"]


def test_failure_semantics_keep_other_frameworks_and_synthesis(monkeypatch):
    batches = control_batches("iso27001")
    first = True
    retry = True
    calls = []

    def fake(*, tier, system, **_kwargs):
        nonlocal first, retry
        ids = _prompt_control_ids(system)
        calls.append((tier, ids))
        if tier == "synthesize":
            return {"text": '{"unified_executive_summary": "survivors"}', "usage": _usage()}
        if set(ids) == set(batches[1].control_ids) and first:
            first = False
            return {"text": _response(ids[:-1]), "usage": _usage()}
        if len(ids) == 1 and retry:
            retry = False
            return {"text": _response([]), "usage": _usage()}
        return {"text": _response(ids), "usage": _usage()}

    result = _run_analysis(monkeypatch, fake)
    iso = result["frameworks"]["iso27001"]
    assert set(iso) == {"parsed", "raw", "usage", "error"}
    assert iso["error"].startswith("Gap analysis for ISO 27001")
    assert "batch 2/6" in iso["error"]
    assert "error" not in result["frameworks"]["dpdpa"]
    assert "error" not in result["frameworks"]["nist_csf"]
    assert result["synthesis"] is not None

    def raising_fake(*, tier, system, **_kwargs):
        ids = _prompt_control_ids(system)
        if ids and set(ids) == set(batches[2].control_ids):
            raise RuntimeError("transport down")
        if tier == "synthesize":
            return {"text": '{"unified_executive_summary": "survivors"}', "usage": _usage()}
        return {"text": _response(ids), "usage": _usage()}

    result = _run_analysis(monkeypatch, raising_fake, framework_ids=("iso27001",))
    assert "failed in batch 3/6" in result["frameworks"]["iso27001"]["error"]


def test_route_marks_failed_framework_and_keeps_batch_call_records(monkeypatch, tmp_path):
    from app.models.analysis_run import AnalysisRun
    from app.models.assessment import Assessment
    from app.models.report import GapReport
    from app.routers import analysis as analysis_router
    from app.services.scoring import failed_framework_scores

    engine = create_engine(f"sqlite:///{tmp_path / 'route.sqlite3'}")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    assessment = Assessment(
        company_name="Acme",
        industry="saas",
        company_size="sme",
        selected_frameworks=json.dumps(["dpdpa", "iso27001"]),
    )
    db.add(assessment)
    db.commit()
    batch_two = set(control_batches("iso27001")[1].control_ids)
    first = True
    retry = True

    def create(**kwargs):
        nonlocal first, retry
        tier = "synthesize" if kwargs["max_tokens"] == 4096 else "judge"
        if tier == "synthesize":
            text = '{"unified_executive_summary": "partial"}'
        else:
            ids = _prompt_control_ids(kwargs["messages"][0]["content"])
            if set(ids) == batch_two and first:
                first = False
                ids = ids[:-1]
            elif len(ids) == 1 and retry:
                retry = False
                ids = []
            text = _response(ids)
        usage = SimpleNamespace(prompt_tokens=2, completion_tokens=3, prompt_tokens_details=SimpleNamespace(cached_tokens=0))
        chunks = [
            SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=text), finish_reason="stop")], usage=None),
            SimpleNamespace(choices=[], usage=usage),
        ]
        return iter(chunks)

    monkeypatch.setattr(llm_client, "_client", SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create))))
    result = analysis_router._run_multi_framework_analysis(
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
    assert "Analysis failed for ISO 27001" in result["message"]
    report = db.query(GapReport).filter_by(assessment_id=assessment.id).one()
    assert json.loads(report.framework_scores)["iso27001"] == failed_framework_scores()
    runs = {run.framework_id: run for run in db.query(AnalysisRun).filter_by(assessment_id=assessment.id).all()}
    assert runs["iso27001"].status == "failed"
    assert json.loads(runs["iso27001"].claims_json)["error"] == {"type": "FrameworkAnalysisError"}
    assert all(call.get("batch") for call in json.loads(runs["iso27001"].claims_json)["llm_calls"])
    db.close()


def test_batched_summary_uses_scope_and_dpdpa_model_summary(monkeypatch):
    statuses = ["compliant", "partially_compliant", "non_compliant", "not_assessed"]

    def fake(*, tier, system, **_kwargs):
        ids = _prompt_control_ids(system)
        return {
            "text": _response(ids, summary="model summary", statuses=lambda index, _id: statuses[index % 4]),
            "usage": _usage(),
        }

    controls = [c.id for c in FrameworkRegistry.get("iso27001").all_controls()]
    result = _run_analysis(
        monkeypatch,
        fake,
        framework_ids=("iso27001",),
        applicable_controls=controls[:10],
    )
    summary = result["frameworks"]["iso27001"]["parsed"]["executive_summary"]
    assert summary == (
        "ISO 27001 (2022): AI-proposed outcomes for 93 controls, assessed in 6 batches: "
        "3 compliant, 3 partially compliant, 2 non-compliant, 2 not assessed, 83 not applicable. "
        "All outcomes are proposals pending consultant review."
    )

    dpdpa = _run_analysis(monkeypatch, fake, framework_ids=("dpdpa",))
    assert dpdpa["frameworks"]["dpdpa"]["parsed"]["executive_summary"] == "model summary"


def _desk_result(ids: list[str], *, duplicate_signal=True) -> dict:
    first = ids[0] if ids else "ISO.A5.1"
    return {
        "document_catalog": [{"filename": "policy.pdf", "document_type": "Policy", "coverage_areas": [first], "summary": "summary"}],
        "evidence_map": {first: [{"quote": "quoted", "document": "policy.pdf", "location": "1"}], "ISO.OUTSIDE": [{"quote": "drop", "document": "policy.pdf"}]},
        "absence_findings": [{"requirement_id": first, "description": "absence", "severity": "medium"}, {"description": "general", "severity": "low"}],
        "signal_flags": [{"flag_type": "generic_policy_documents", "description": "signal", "severity": "high", "source_quote": "Same  quote", "document": "policy.pdf", "requirement_ids": [first]}] if duplicate_signal else [],
        "coverage_summary": {control_id: "adequate" for control_id in ids},
    }


def _desk_db(tmp_path, frameworks):
    engine = create_engine(f"sqlite:///{tmp_path / 'desk.sqlite3'}")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    from app.models.assessment import Assessment, AssessmentDocument

    assessment = Assessment(
        company_name="Acme",
        industry="saas",
        company_size="sme",
        selected_frameworks=json.dumps(frameworks),
    )
    db.add(assessment)
    db.flush()
    db.add(AssessmentDocument(
        assessment_id=assessment.id,
        filename="policy.pdf",
        file_path="policy.pdf",
        file_type="pdf",
        document_category="privacy_policy",
        extracted_text="A policy.",
    ))
    db.commit()
    return db, assessment


def test_desk_review_batch_merge_persistence_and_partial_failure(monkeypatch, tmp_path):
    db, assessment = _desk_db(tmp_path, ["dpdpa", "iso27001"])
    iso_batches = control_batches("iso27001")
    seen = []

    monkeypatch.setattr(desk_review, "_call_claude_desk_review", lambda **_kwargs: _desk_result([]))

    def generic(framework_id, *_args, **kwargs):
        ids = list(kwargs["control_ids"])
        seen.append(ids)
        return _desk_result(ids)

    monkeypatch.setattr(desk_review, "_call_framework_desk_review", generic)
    summary = desk_review.run_desk_review(assessment.id, db)
    raw = json.loads(summary.raw_ai_response)
    merged = raw["frameworks"]["iso27001"]["result"]
    assert len(seen) == 6
    assert len(merged["document_catalog"]) == 1
    assert len(merged["document_catalog"][0]["coverage_areas"]) == 6
    assert len(merged["signal_flags"]) == 1
    assert len(merged["signal_flags"][0]["requirement_ids"]) == 6
    assert set(merged["coverage_summary"]) == {c.id for c in FrameworkRegistry.get("iso27001").all_controls()}
    assert "ISO.OUTSIDE" not in merged["evidence_map"]
    from app.models.desk_review import DeskReviewFinding

    assert db.query(DeskReviewFinding).filter_by(assessment_id=assessment.id, framework_id="iso27001").count() > 0

    def failing(framework_id, *_args, **kwargs):
        ids = list(kwargs["control_ids"])
        if ids == list(iso_batches[2].control_ids):
            raise RuntimeError("batch unavailable")
        return _desk_result(ids)

    monkeypatch.setattr(desk_review, "_call_framework_desk_review", failing)
    summary = desk_review.run_desk_review(assessment.id, db)
    raw = json.loads(summary.raw_ai_response)
    assert summary.status == "completed"
    assert "Desk review failed for ISO 27001" in summary.error_message
    assert raw["frameworks"]["iso27001"]["status"] == "error"
    assert raw["frameworks"]["dpdpa"]["status"] == "completed"
    assert db.query(DeskReviewFinding).filter_by(assessment_id=assessment.id, framework_id="dpdpa").count() > 0
    db.close()


def test_concurrency_equivalence_and_flattened_bound(monkeypatch, tmp_path):
    active = 0
    max_active = 0
    lock = threading.Lock()

    def fake(*, tier, system, **_kwargs):
        nonlocal active, max_active
        ids = _prompt_control_ids(system)
        with lock:
            active += 1
            max_active = max(max_active, active)
        time.sleep(0.003)
        with lock:
            active -= 1
        return {"text": _response(ids), "usage": _usage()}

    monkeypatch.setattr(settings, "llm_max_concurrency", 1)
    sequential = _run_analysis(monkeypatch, fake)
    monkeypatch.setattr(settings, "llm_max_concurrency", 4)
    concurrent = _run_analysis(monkeypatch, fake)
    assert sequential == concurrent
    assert max_active > 1
    assert max_active <= 4

    db, assessment = _desk_db(tmp_path, ["dpdpa", "iso27001"])
    monkeypatch.setattr(desk_review, "_call_claude_desk_review", lambda **_kwargs: _desk_result([]))
    monkeypatch.setattr(desk_review, "_call_framework_desk_review", lambda _framework_id, *_args, **kwargs: _desk_result(list(kwargs["control_ids"])))
    monkeypatch.setattr(settings, "llm_max_concurrency", 1)
    sequential_desk = json.loads(desk_review.run_desk_review(assessment.id, db).raw_ai_response)["frameworks"]
    monkeypatch.setattr(settings, "llm_max_concurrency", 4)
    concurrent_desk = json.loads(desk_review.run_desk_review(assessment.id, db).raw_ai_response)["frameworks"]
    assert sequential_desk == concurrent_desk
    db.close()


def test_call_record_tags_are_optional_and_batch_visible(monkeypatch):
    def create(**kwargs):
        ids = _prompt_control_ids(kwargs["messages"][0]["content"])
        text = _response(ids)
        usage = SimpleNamespace(prompt_tokens=2, completion_tokens=3, prompt_tokens_details=SimpleNamespace(cached_tokens=0))
        chunks = [SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=text), finish_reason="stop")], usage=None), SimpleNamespace(choices=[], usage=usage)]
        return iter(chunks)

    monkeypatch.setattr(llm_client, "_client", SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create))))
    with llm_client.collect_calls() as calls:
        with llm_client.call_tag(stage="judge", framework_id="iso27001"):
            with llm_client.call_tag(batch="1/6"):
                llm_client.call_llm("judge", system="sys", messages=[], max_tokens=10, stream=True)
    assert calls[0]["stage"] == "judge"
    assert calls[0]["framework_id"] == "iso27001"
    assert calls[0]["batch"] == "1/6"

    with llm_client.collect_calls() as calls:
        with llm_client.call_tag(stage="judge", framework_id="iso27001"):
            llm_client.call_llm("judge", system="sys", messages=[], max_tokens=10, stream=True)
    assert set(calls[0]) == {
        "tier", "model", "stage", "framework_id", "input_tokens", "output_tokens",
        "cache_read_input_tokens", "latency_ms", "finish_reason", "status", "error_type",
    }

    monkeypatch.setattr(settings, "llm_batch_threshold_controls", 50)
    with llm_client.collect_calls() as calls:
        claude_analyzer.run_multi_framework_analysis(
            ["iso27001"], "Acme", "saas", "sme", None, [], []
        )
    assert len(calls) == 6
    assert all(call.get("batch") for call in calls)
    assert {call["batch"] for call in calls} == {f"{i}/6" for i in range(1, 7)}


def test_protected_surface_guard_uses_three_dot_diff():
    result = subprocess.run(
        [
            "git", "diff", "--stat", "main...HEAD", "--",
            "tests/fixtures", "tests/support", "app/dpdpa", "app/frameworks/schema.py",
            "app/frameworks/definitions", "app/services/scoring.py",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout == ""
