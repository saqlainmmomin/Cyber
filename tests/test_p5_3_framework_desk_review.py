"""Contract tests for P5-3 framework-aware desk review and evidence handling.

The scenarios correspond one-for-one with the handoff at
``tasks/handoffs/2026-09-24-p5-3-framework-aware-desk-review.md``.  The suite
uses an Alembic-built SQLite database, deterministic upload extraction, and
patches every LLM seam; it never uses the development database or network.
"""

from __future__ import annotations

import inspect as pyinspect
import json
import subprocess
from pathlib import Path
from unittest.mock import call

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, inspect, text, update
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.config import settings
from app.models.assessment import Assessment
from app.models.client import Client
from app.models.desk_review import DeskReviewFinding, DeskReviewSummary
from app.models.engagement import Engagement
from app.models.questionnaire import QuestionnaireResponse


REPO_ROOT = Path(__file__).resolve().parents[1]
REVISION = "8b2d5f7e1c34"
PREVIOUS_REVISION = "4e8c1a9d2b57"
SYSTEM_SHA256 = "21b365d6eac8d3ad2171ac86773567dcee0306b3968a6da993ee67a8bd4e1d93"
REQUEST_KEY = "3e7f8d2a1c9ce76110f25d26e4c7ae86e52b633b441746d5d4d16b82438f1c86"
DOCS = [
    {
        "id": "d1",
        "filename": "policy.pdf",
        "category": "privacy_policy",
        "text": "We obtain consent before processing.",
    }
]
USAGE = {
    "input_tokens": 0,
    "output_tokens": 0,
    "cache_read_input_tokens": 0,
    "cache_creation_input_tokens": 0,
}


@pytest.fixture(scope="module", autouse=True)
def _register_frameworks():
    from app.main import _register_frameworks as register

    register()


def _cfg(path: Path) -> Config:
    cfg = Config(str(REPO_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{path}")
    return cfg


@pytest.fixture(autouse=True)
def upload_root(tmp_path, monkeypatch):
    root = tmp_path / "uploads"
    root.mkdir()
    monkeypatch.setattr(settings, "upload_dir", str(root))
    return root


@pytest.fixture()
def db_path(tmp_path):
    path = tmp_path / "p5_3.sqlite3"
    command.upgrade(_cfg(path), "head")
    return path


@pytest.fixture()
def engine(db_path):
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def _foreign_keys(connection, _record):  # pragma: no cover
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    yield engine
    engine.dispose()


@pytest.fixture()
def db(engine):
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def http(db, db_path, monkeypatch):
    from app.database import get_db
    from app.main import app
    from app.routers.web import templates
    from app.template_config import configure_templates

    configure_templates(templates)
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{db_path}")

    def override():
        yield db

    app.dependency_overrides[get_db] = override
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture()
def texts(monkeypatch):
    from app.services import evidence

    values: dict[bytes, str] = {}
    monkeypatch.setattr(
        evidence,
        "extract_text",
        lambda path, _file_type: values.get(Path(path).read_bytes(), "Nothing relevant."),
    )
    return values


def _seed(db, frameworks=("dpdpa",), *, industry="it_services"):
    ordinal = db.query(Client).count()
    company_name = "Acme" if ordinal == 0 else f"Acme {ordinal + 1}"
    client = Client(name=company_name, industry="Technology", size="medium")
    db.add(client)
    db.flush()
    engagement = Engagement(client_id=client.id, name="Acme gap", status="active")
    db.add(engagement)
    db.flush()
    assessment = Assessment(
        company_name=company_name,
        industry=industry,
        company_size="medium",
        selected_frameworks=json.dumps(list(frameworks)),
        engagement_id=engagement.id,
    )
    db.add(assessment)
    db.commit()
    return assessment


def _upload(db, texts, assessment, *, body="Grounded exact quote.", filename="policy.pdf"):
    from app.services.evidence import ingest_upload

    payload = b"%PDF-1.4\n% p5-3 deterministic\n%%EOF\n"
    texts[payload] = body
    return ingest_upload(
        db,
        assessment_id=assessment.id,
        filename=filename,
        content=payload,
        category="privacy_policy",
    )


def _result(*, coverage=None, evidence=None, signals=None, absences=None, catalog=None):
    return {
        "document_catalog": catalog or [],
        "evidence_map": evidence or {},
        "absence_findings": absences or [],
        "signal_flags": signals or [],
        "coverage_summary": coverage or {},
    }


def _all_questions(questionnaire):
    return [q for section in questionnaire["sections"] for q in section.get("questions", [])]


def _response(text_value):
    return {"text": json.dumps(text_value), "usage": dict(USAGE)}


def _analysis_payload(framework_id):
    from app.frameworks.registry import FrameworkRegistry

    return {
        "executive_summary": "ok",
        "assessments": [
            {
                "requirement_id": control.id,
                "compliance_status": "not_assessed",
                "current_state": "Unknown",
                "gap_description": "Insufficient information",
                "risk_level": "medium",
                "remediation_action": "Review",
                "remediation_priority": 2,
                "remediation_effort": "medium",
                "timeline_weeks": 4,
                "maturity_level": 0,
                "root_cause_category": "governance",
                "evidence_quote": "No relevant language found",
            }
            for control in FrameworkRegistry.get(framework_id).all_controls()
        ],
    }


def test_scenario_1_alembic_schema_backfill_and_guarded_downgrade(tmp_path):
    """Scenario 1: P5-3 is the sole head, backfills legacy rows, and refuses lossy downgrades."""
    scripts = ScriptDirectory.from_config(_cfg(tmp_path / "unused.sqlite3"))
    assert scripts.get_current_head() == REVISION
    assert scripts.get_revision(REVISION).down_revision == PREVIOUS_REVISION

    legacy = tmp_path / "legacy.sqlite3"
    cfg = _cfg(legacy)
    command.upgrade(cfg, PREVIOUS_REVISION)
    eng = create_engine(f"sqlite:///{legacy}")
    with eng.begin() as conn:
        conn.execute(text(
            "INSERT INTO assessments "
            "(id, company_name, industry, company_size, status, created_at, updated_at, version) "
            "VALUES ('a1', 'Acme', 'Technology', 'medium', 'created', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1)"
        ))
        conn.execute(text(
            "INSERT INTO desk_review_findings "
            "(assessment_id, finding_type, requirement_id, content, severity, created_at) VALUES "
            "('a1', 'evidence', 'CH2.CONSENT.1', 'quote', 'info', CURRENT_TIMESTAMP), "
            "('a1', 'signal', 'CH2.CONSENT.1', 'flag', 'high', CURRENT_TIMESTAMP)"
        ))
    command.upgrade(cfg, "head")
    columns = {c["name"]: c for c in inspect(eng).get_columns("desk_review_findings")}
    assert str(columns["framework_id"]["type"]) == "VARCHAR(50)"
    assert str(columns["flag_type"]["type"]) == "VARCHAR(100)"
    assert str(columns["signal_group_id"]["type"]) == "VARCHAR(36)"
    assert all(columns[name]["nullable"] for name in ("framework_id", "flag_type", "signal_group_id"))
    with eng.connect() as conn:
        rows = conn.execute(text(
            "SELECT framework_id, flag_type, signal_group_id FROM desk_review_findings ORDER BY id"
        )).all()
    assert rows == [("dpdpa", None, None), ("dpdpa", None, None)]
    command.downgrade(cfg, PREVIOUS_REVISION)
    assert "framework_id" not in {c["name"] for c in inspect(eng).get_columns("desk_review_findings")}
    with eng.connect() as conn:
        assert conn.scalar(text("SELECT COUNT(*) FROM desk_review_findings")) == 2
    eng.dispose()

    for column, value in (
        ("flag_type", "scope_gap"),
        ("signal_group_id", "group-1"),
        ("framework_id", "iso27001"),
    ):
        path = tmp_path / f"guard-{column}.sqlite3"
        case_cfg = _cfg(path)
        command.upgrade(case_cfg, "head")
        case_eng = create_engine(f"sqlite:///{path}")
        with case_eng.begin() as conn:
            conn.execute(text(
                "INSERT INTO assessments "
                "(id, company_name, industry, company_size, status, created_at, updated_at, version) "
                "VALUES ('a1', 'Acme', 'Technology', 'medium', 'created', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1)"
            ))
            conn.execute(text(
                "INSERT INTO desk_review_findings "
                "(assessment_id, finding_type, content, severity, framework_id, created_at) "
                "VALUES ('a1', 'signal', 'flag', 'high', 'dpdpa', CURRENT_TIMESTAMP)"
            ))
            conn.execute(text(f"UPDATE desk_review_findings SET {column} = :value"), {"value": value})
        with pytest.raises(RuntimeError, match="Refusing to downgrade past P5-3 revision 8b2d5f7e1c34"):
            command.downgrade(case_cfg, PREVIOUS_REVISION)
        case_eng.dispose()


def test_scenario_2_registry_prompts_and_flag_vocabulary(monkeypatch):
    """Scenario 2: generic prompts enumerate framework controls and deterministic flag keys."""
    from app.dpdpa.prompts import DESK_REVIEW_FLAG_TYPES, build_desk_review_system_prompt
    from app.frameworks import prompts
    from app.frameworks.registry import FrameworkRegistry

    expected = {
        "iso27001": [
            "certification_without_evidence_of_operational_controls",
            "statement_of_applicability_gaps",
            "generic_policy_documents",
            "no_management_review_evidence",
            "risk_assessment_staleness",
        ],
        "nist_csf": [
            "govern_function_absence",
            "tier_mismatch_with_claims",
            "detection_without_response_capability",
            "asset_inventory_gaps",
            "supply_chain_blind_spots",
            "recovery_plan_never_tested",
            "profile_without_action",
        ],
    }
    for fw_id, keys in expected.items():
        fw = FrameworkRegistry.get(fw_id)
        assert [prompts.red_flag_key(rf) for rf in fw.red_flag_patterns] == keys
        blocks = prompts.build_framework_desk_review_system_prompt(fw_id)
        assert len(blocks) == 2
        assert blocks[0]["text"] == prompts._FRAMEWORK_PERSONAS[fw_id]
        assert blocks[1]["cache_control"] == {"type": "ephemeral"}
        body = blocks[1]["text"]
        assert all(c.id in body for c in fw.all_controls())
        assert all(rf.pattern in body and f'flag_type: "{key}"' in body for rf, key in zip(fw.red_flag_patterns, keys))
        assert f"Include ALL {fw.control_count()} control IDs" in body
        assert '"evidence_map": {' in body
        assert not any(term in body for term in ("DPDPA", "Data Protection Board", "data principal"))

    for fw_id in FrameworkRegistry.all_ids():
        keys = [prompts.red_flag_key(rf) for rf in FrameworkRegistry.get(fw_id).red_flag_patterns]
        assert len(keys) == len(set(keys))
        assert all(len(key) <= 100 for key in keys)

    iso = FrameworkRegistry.get("iso27001")
    monkeypatch.setattr(iso, "red_flag_patterns", [])
    no_flags = prompts.build_framework_desk_review_system_prompt("iso27001")[1]["text"]
    assert "This framework defines no red-flag patterns." in no_flags
    assert '"signal_flags": []' in no_flags
    monkeypatch.undo()

    assert prompts.desk_review_flag_types("dpdpa") == DESK_REVIEW_FLAG_TYPES
    curated = "\n".join(block["text"] for block in build_desk_review_system_prompt())
    assert all(f'(flag_type: "{value}")' in curated for value in DESK_REVIEW_FLAG_TYPES)
    extraction = prompts.build_framework_evidence_extraction_prompt("iso27001", DOCS)
    assert all(c.id in extraction for c in FrameworkRegistry.get("iso27001").all_controls())
    assert "Omit controls for which no relevant language exists" in extraction
    assert "DPDPA" not in extraction


def test_scenario_3_dpdpa_request_is_byte_identical(db, texts, monkeypatch):
    """Scenario 3: the curated DPDPA prompt, call seam, and request bytes stay unchanged."""
    import hashlib

    from app.dpdpa.prompts import build_desk_review_system_prompt
    from app.services import desk_review
    from tests.support.analyzer_mock import analyzer_request_key

    digest = hashlib.sha256(json.dumps(build_desk_review_system_prompt(), sort_keys=True).encode()).hexdigest()
    assert digest == SYSTEM_SHA256
    captured = {}

    def fake_llm(**kwargs):
        captured.update(kwargs)
        return _response({})

    monkeypatch.setattr(desk_review, "_call_llm", fake_llm)
    desk_review._call_claude_desk_review(DOCS, "Acme", "saas")
    assert analyzer_request_key((), captured) == REQUEST_KEY

    assessment = _seed(db)
    _upload(db, texts, assessment)
    seen = []
    monkeypatch.setattr(desk_review, "_call_claude_desk_review", lambda **kw: seen.append(kw) or _result())
    monkeypatch.setattr(desk_review, "_call_framework_desk_review", lambda *_a, **_k: pytest.fail("generic call"))
    desk_review.run_desk_review(assessment.id, db)
    assert len(seen) == 1
    assert set(seen[0]) == {"documents", "company_name", "industry"}
    assert seen[0]["company_name"] == "Acme" and seen[0]["industry"] == "it_services"
    assert seen[0]["documents"][0]["filename"] == "policy.pdf"


def test_scenario_4_calls_each_framework_in_order_and_normalizes(db, texts, monkeypatch):
    """Scenario 4: one ordered call per selected framework is normalized and aggregated."""
    from app.services import desk_review
    from app.services.desk_review_findings import group_signal_findings

    assessment = _seed(db, ("dpdpa", "iso27001", "nist_csf"))
    _upload(db, texts, assessment)
    seen = []
    monkeypatch.setattr(
        desk_review,
        "_call_claude_desk_review",
        lambda **_kw: seen.append("dpdpa") or _result(
            coverage={"CH2.CONSENT.1": "partial"},
            catalog=[{"filename": "policy.pdf", "document_type": "Policy", "coverage_areas": ["CH2.CONSENT.1"], "summary": "D"}],
        ),
    )

    def generic(fw_id, *_args):
        seen.append(fw_id)
        if fw_id == "iso27001":
            return _result(
                evidence={"CH2.CONSENT.1": [{"quote": "bad"}]},
                signals=[{
                    "requirement_ids": ["ISO.A5.1", "CH2.CONSENT.1", "ISO.A5.1"],
                    "flag_type": "made_up",
                    "description": "signal",
                }],
                coverage={"ISO.A5.1": "adequate", "NIST.GV.OC.01": "absent"},
                catalog=[{"filename": "policy.pdf", "document_type": "ISMS", "coverage_areas": ["ISO.A5.1"], "summary": "I"}],
            )
        return _result(
            coverage={"NIST.GV.OC.01": "adequate"},
            catalog=[{"filename": "nist.pdf", "document_type": "Profile", "coverage_areas": ["NIST.GV.OC.01"], "summary": "N"}],
        )

    monkeypatch.setattr(desk_review, "_call_framework_desk_review", generic)
    # P6-1: sequential order + normalization contract is independent of concurrency.
    monkeypatch.setattr(settings, "llm_max_concurrency", 1)
    summary = desk_review.run_desk_review(assessment.id, db)
    assert seen == ["dpdpa", "iso27001", "nist_csf"]
    rows = db.query(DeskReviewFinding).filter_by(assessment_id=assessment.id).all()
    assert {r.framework_id for r in rows} == {"iso27001"}
    assert not any(r.framework_id == "iso27001" and r.requirement_id == "CH2.CONSENT.1" for r in rows)
    grouped = group_signal_findings(rows)
    assert grouped[0]["requirement_ids"] == ["ISO.A5.1"]
    assert grouped[0]["flag_type"] == "unclassified"
    assert json.loads(summary.coverage_summary) == {
        "CH2.CONSENT.1": "partial",
        "ISO.A5.1": "adequate",
        "NIST.GV.OC.01": "adequate",
    }
    catalog = json.loads(summary.document_catalog)
    assert catalog[0]["coverage_areas"] == ["CH2.CONSENT.1", "ISO.A5.1"]
    assert len([entry for entry in catalog if entry["filename"] == "policy.pdf"]) == 1
    raw = json.loads(summary.raw_ai_response)
    assert raw["schema_version"] == 2
    assert [item["status"] for item in raw["frameworks"].values()] == ["completed"] * 3

    single = _seed(db, ("iso27001",))
    _upload(db, texts, single)
    literal = [{"filename": "policy.pdf", "custom": "untouched"}]
    monkeypatch.setattr(desk_review, "_call_framework_desk_review", lambda *_a: _result(catalog=literal))
    assert json.loads(desk_review.run_desk_review(single.id, db).document_catalog) == literal


def test_scenario_5_multi_requirement_signal_reaches_all_consumers(db, texts, http, monkeypatch):
    """Scenario 5: one signal is stored per requirement but grouped on signal-facing surfaces."""
    from app.dpdpa.prompts import build_user_prompt
    from app.services import analysis_pipeline, desk_review, question_engine, workpaper
    from app.services.auto_answer import persist_document_answers
    from app.services.citations import loads_citations, validate_citations
    from app.services.desk_review_findings import load_desk_review_data

    assessment = _seed(db)
    _upload(db, texts, assessment, body="This policy intentionally contains no quoted flag text.")
    fake = _result(
        coverage={"CH2.CONSENT.1": "adequate"},
        evidence={"CH2.CONSENT.1": [{"quote": "not grounded", "document": "policy.pdf", "location": "S1"}]},
        signals=[{
            "requirement_ids": ["CH2.NOTICE.1", "CH2.CONSENT.1"],
            "flag_type": "buried_consent",
            "description": "Terms hide the choice",
            "severity": "high",
            "source_quote": "",
            "document": "policy.pdf",
            "location": "Section 2",
        }],
    )
    monkeypatch.setattr(desk_review, "_call_claude_desk_review", lambda **_kw: fake)
    desk_review.run_desk_review(assessment.id, db)
    signals = db.query(DeskReviewFinding).filter_by(assessment_id=assessment.id, finding_type="signal").order_by(DeskReviewFinding.id).all()
    assert [r.requirement_id for r in signals] == ["CH2.NOTICE.1", "CH2.CONSENT.1"]
    assert len({r.signal_group_id for r in signals}) == 1
    assert all(r.flag_type == "buried_consent" and r.content == "Terms hide the choice" for r in signals)
    assert signals[0].citations_json == signals[1].citations_json
    for row in signals:
        citations = loads_citations(row.citations_json)
        validate_citations(db, citations, assessment_id=assessment.id)
        assert citations[0]["location_type"] == "whole_item"
    assert persist_document_answers(assessment.id, db) == 0
    assert db.query(QuestionnaireResponse).filter_by(assessment_id=assessment.id).count() == 0

    questionnaire = question_engine.build_adaptive_questionnaire(assessment.id, db)
    by_id = {q["id"]: q for q in _all_questions(questionnaire)}
    for req in ("CH2.NOTICE.1", "CH2.CONSENT.1"):
        assert by_id[req]["status"] == "deepened"
        assert "Signal detected" in by_id[req]["desk_review_note"]
    data = load_desk_review_data(db, assessment)
    assert data["signal_flags"][0]["requirement_ids"] == ["CH2.NOTICE.1", "CH2.CONSENT.1"]
    assert len([f for f in data["findings"] if f["type"] == "signal"]) == 2
    for req in ("CH2.NOTICE.1", "CH2.CONSENT.1"):
        red_flags, _absence = analysis_pipeline._desk_review_quality(data, req)
        assert red_flags == 1
    rendered = build_user_prompt("Acme", "it_services", "medium", None, [], [], desk_review_summary=data)
    assert "(affects CH2.NOTICE.1, CH2.CONSENT.1)" in rendered
    desk_rows = workpaper._desk_findings(db, assessment.id)
    assert any(r["content"] == "Terms hide the choice" for r in desk_rows["CH2.NOTICE.1"])
    assert any(r["content"] == "Terms hide the choice" for r in desk_rows["CH2.CONSENT.1"])

    api = http.get(f"/api/assessments/{assessment.id}/desk-review").json()
    assert api["signal_count"] == 1
    assert api["findings"]["signals"][0]["requirement_ids"] == ["CH2.NOTICE.1", "CH2.CONSENT.1"]
    assert api["findings"]["signals"][0]["flag_type"] == "buried_consent"
    assert api["findings"]["signals"][0]["citations"][0]["location_type"] == "whole_item"
    partial = http.get(f"/assessments/{assessment.id}/desk-review-status").text
    assert "Red Flags (1)" in partial
    assert "Related: CH2.NOTICE.1, CH2.CONSENT.1" in partial

    from app.frameworks.prompts import build_framework_user_prompt

    iso_data = {
        "coverage_summary": {},
        "signal_flags": [{
            "content": "ISO signal", "severity": "high", "requirement_id": "ISO.A5.1",
            "requirement_ids": ["ISO.A5.1", "ISO.A5.2"], "framework_id": "iso27001", "flag_type": "generic_policy_documents",
        }],
    }
    iso_prompt = build_framework_user_prompt("iso27001", "Acme", "Technology", "medium", None, [], [], desk_review_summary=iso_data)
    assert "### Red Flags" in iso_prompt and "ISO signal" in iso_prompt


def test_scenario_6_framework_failures_are_isolated(db, texts, http, monkeypatch):
    """Scenario 6: partial and total desk-review failures have the specified status and messages."""
    from app.frameworks.registry import FrameworkRegistry
    from app.services import desk_review
    from app.services.desk_review_findings import failed_desk_review_frameworks

    assessment = _seed(db, ("dpdpa", "iso27001", "nist_csf"))
    _upload(db, texts, assessment)
    monkeypatch.setattr(desk_review, "_call_claude_desk_review", lambda **_kw: _result(absences=[{"requirement_id": "CH2.CONSENT.1", "description": "D"}]))

    def partial(fw_id, *_args):
        if fw_id == "nist_csf":
            raise RuntimeError("nist exploded")
        return _result(absences=[{"requirement_id": "ISO.A5.1", "description": "I"}])

    monkeypatch.setattr(desk_review, "_call_framework_desk_review", partial)
    summary = desk_review.run_desk_review(assessment.id, db)
    nist_name = FrameworkRegistry.get("nist_csf").name
    assert summary.status == "completed"
    assert summary.error_message == desk_review.DESK_REVIEW_PARTIAL_MESSAGE.format(names=nist_name)
    assert failed_desk_review_frameworks(summary) == ["nist_csf"]
    rows = db.query(DeskReviewFinding).filter_by(assessment_id=assessment.id).all()
    assert {r.framework_id for r in rows} == {"dpdpa", "iso27001"}
    assert "data-desk-review-failed-frameworks" in http.get(f"/assessments/{assessment.id}/desk-review-status").text
    assert nist_name in http.get(f"/assessments/{assessment.id}/desk-review-status").text
    assert http.get(f"/api/assessments/{assessment.id}/desk-review").json()["failed_frameworks"] == ["nist_csf"]
    from app.routers import desk_review as desk_review_router

    monkeypatch.setattr(desk_review_router, "run_desk_review", lambda *_a, **_k: summary)
    triggered = desk_review_router.trigger_desk_review(assessment.id, db)
    assert triggered["failed_frameworks"] == ["nist_csf"]

    sentinel = []
    monkeypatch.setattr(desk_review, "_desk_review_call", lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("all down")))
    monkeypatch.setattr("app.services.auto_answer.persist_document_answers", lambda *_a: sentinel.append(True))
    summary = desk_review.run_desk_review(assessment.id, db)
    names = ", ".join(FrameworkRegistry.get(fw).name for fw in assessment.frameworks)
    assert summary.status == "error"
    assert summary.error_message == desk_review.DESK_REVIEW_ALL_FAILED_MESSAGE.format(names=names)
    assert db.query(DeskReviewFinding).filter_by(assessment_id=assessment.id).count() == 0
    assert sentinel == []

    one = _seed(db)
    _upload(db, texts, one)
    summary = desk_review.run_desk_review(one.id, db)
    assert summary.error_message == "all down"

    mixed = _seed(db, ("dpdpa", "iso27001"))
    _upload(db, texts, mixed)
    monkeypatch.setattr(desk_review, "_desk_review_call", lambda fw, **_k: _result() if fw == "dpdpa" else desk_review._parse_json_response("not json"))
    assert desk_review.run_desk_review(mixed.id, db).status == "completed"


def test_scenario_7_signal_type_is_not_inferred_from_content(db):
    """Scenario 7: explicit singular flag types drive industry deepening; legacy text does not."""
    from app.dpdpa.industry_questions import INDUSTRY_QUESTIONS
    from app.dpdpa.prompts import DESK_REVIEW_FLAG_TYPES
    from app.services import question_engine

    assert "content_lower" not in pyinspect.getsource(question_engine)
    assessment = _seed(db)
    db.add(DeskReviewSummary(assessment_id=assessment.id, status="completed", coverage_summary="{}"))
    db.add(DeskReviewFinding(
        assessment_id=assessment.id, framework_id="dpdpa", finding_type="signal",
        requirement_id="CH2.CONSENT.1", flag_type="scope_gap", content="Neutral wording", severity="high",
    ))
    db.commit()
    by_id = {q["id"]: q for q in _all_questions(question_engine.build_adaptive_questionnaire(assessment.id, db))}
    assert by_id["IND.SAAS.1"]["status"] == "deepened"

    db.query(DeskReviewFinding).delete()
    db.add(DeskReviewFinding(
        assessment_id=assessment.id, framework_id="dpdpa", finding_type="signal",
        requirement_id="CH2.CONSENT.1", flag_type="buried_consent", content="GDPR appears here", severity="high",
    ))
    db.commit()
    by_id = {q["id"]: q for q in _all_questions(question_engine.build_adaptive_questionnaire(assessment.id, db))}
    gdpr_only = [q for bank in INDUSTRY_QUESTIONS.values() for q in bank["questions"] if q.get("deepen_if", {}).get("signal_flags") == ["gdpr_copy_paste"]]
    assert all(by_id[q["id"]]["status"] != "deepened" for q in gdpr_only if q["id"] in by_id)

    db.query(DeskReviewFinding).delete()
    db.add(DeskReviewFinding(
        assessment_id=assessment.id, framework_id=None, finding_type="signal",
        requirement_id="CH2.CONSENT.1", flag_type=None, content="template scope GDPR gap", severity="high",
    ))
    db.commit()
    by_id = {q["id"]: q for q in _all_questions(question_engine.build_adaptive_questionnaire(assessment.id, db))}
    assert by_id["CH2.CONSENT.1"]["status"] == "deepened"
    assert all(q["status"] != "deepened" for q in by_id.values() if q["id"].startswith("IND."))

    values = {
        value
        for bank in INDUSTRY_QUESTIONS.values()
        for q in bank["questions"]
        for value in q.get("deepen_if", {}).get("signal_flags", [])
    }
    assert values <= set(DESK_REVIEW_FLAG_TYPES)


def test_scenario_8_multi_framework_evidence_extraction_is_per_framework(monkeypatch):
    """Scenario 8: desk evidence is reused per framework and missing evidence is extracted independently."""
    from app.services import claude_analyzer

    docs = [{"filename": "policy.pdf", "category": "policy", "text": "ISO grounded quote. NIST grounded quote."}]
    desk_data = {
        "findings": [{"type": "evidence", "requirement_id": "CH2.CONSENT.1", "source_quote": "DPDPA quote"}],
        "coverage_summary": {}, "signal_flags": [], "absence_findings": [],
    }
    calls = []

    def llm(**kwargs):
        calls.append(kwargs)
        if kwargs["tier"] == "extract":
            prompt = kwargs["messages"][0]["content"]
            if "ISO.A5.1" in prompt:
                return _response({"evidence": {"ISO.A5.1": ["ISO grounded quote", "invented"], "NIST.GV.OC.01": ["NIST grounded quote"]}})
            return _response({"evidence": {"NIST.GV.OC.01": ["NIST grounded quote"]}})
        if kwargs["tier"] == "judge":
            persona = kwargs["system"][0]["text"]
            fw_id = "dpdpa" if "DPDPA" in persona else "iso27001" if "ISO/IEC" in persona else "nist_csf"
            return _response(_analysis_payload(fw_id))
        return _response({"overall_posture": "ok", "common_themes": [], "cross_framework_priorities": []})

    monkeypatch.setattr(claude_analyzer, "_call_llm", llm)
    claude_analyzer.run_multi_framework_analysis(
        ["dpdpa", "iso27001", "nist_csf"], "Acme", "Technology", "medium", None, [], docs,
        desk_review_data=desk_data,
    )
    extracts = [item for item in calls if item["tier"] == "extract"]
    # P6-1c: framework-path extraction uses the configurable output ceiling.
    from app.config import settings as _settings

    assert len(extracts) == 2 and all(
        item["max_tokens"] == _settings.llm_max_output_tokens_framework for item in extracts
    )
    assert "ISO.A5.1" in extracts[0]["messages"][0]["content"]
    assert "DPDPA" not in extracts[0]["messages"][0]["content"]
    judges = [item["messages"][0]["content"] for item in calls if item["tier"] == "judge"]
    iso_prompt = next(p for p in judges if "ISO.A5.1" in p)
    assert "## Extracted Document Evidence" in iso_prompt and "ISO grounded quote" in iso_prompt
    assert "invented" not in iso_prompt and "NIST grounded quote" not in iso_prompt

    calls.clear()

    def failure_llm(**kwargs):
        prompt = kwargs["messages"][0]["content"]
        if kwargs["tier"] == "extract" and "ISO.A5.1" in prompt:
            raise RuntimeError("extract down")
        return llm(**kwargs)

    monkeypatch.setattr(claude_analyzer, "_call_llm", failure_llm)
    result = claude_analyzer.run_multi_framework_analysis(
        ["iso27001", "nist_csf"], "Acme", "Technology", "medium", None, [], docs,
    )
    assert "error" not in result["frameworks"]["iso27001"]
    judges = [item["messages"][0]["content"] for item in calls if item["tier"] == "judge"]
    assert len(judges) == 2
    assert sum("## Supporting Documents" in prompt for prompt in judges) == 1
    assert sum("## Extracted Document Evidence" in prompt for prompt in judges) == 1

    calls.clear()
    claude_analyzer.run_multi_framework_analysis(["iso27001"], "Acme", "Technology", "medium", None, [], [])
    assert not any(item["tier"] == "extract" for item in calls)


def test_scenario_9_screening_gate(db, http, monkeypatch):
    """Scenario 9: screening refuses ISO-only and mixed assessments before calls or writes."""
    from app.dpdpa.framework import get_all_requirements
    from app.services import screening

    for frameworks in (("iso27001",), ("dpdpa", "iso27001")):
        assessment = _seed(db, frameworks)
        assessment.screening_status = "untouched"
        assessment.screening_results = '{"old": true}'
        db.commit()
        called = []
        monkeypatch.setattr(screening, "_call_llm", lambda **_kw: called.append(True))
        with pytest.raises(screening.ScreeningNotApplicable) as exc:
            screening.run_screening_pass(assessment.id, {}, db)
        assert str(exc.value) == screening.SCREENING_NOT_APPLICABLE_MESSAGE
        db.refresh(assessment)
        assert called == []
        assert assessment.screening_status == "untouched" and assessment.screening_results == '{"old": true}'
        assert db.query(QuestionnaireResponse).filter_by(assessment_id=assessment.id).count() == 0
        response = http.post(f"/assessments/{assessment.id}/screening/submit", data={})
        assert response.status_code == 200
        assert screening.SCREENING_NOT_APPLICABLE_MESSAGE in response.text

    dpdpa = _seed(db)
    req_id = get_all_requirements()[0]["id"]
    monkeypatch.setattr(
        screening,
        "_call_llm",
        lambda **_kw: _response({"inferences": {req_id: {"compliance_status": "compliant", "confidence": "high", "reasoning": "yes"}}}),
    )
    screening.run_screening_pass(dpdpa.id, {}, db)
    row = db.query(QuestionnaireResponse).filter_by(assessment_id=dpdpa.id, question_id=req_id).one()
    assert row.answer_source == "inferred"


def test_scenario_10_prefill_gate_and_duplicate_prevention(db):
    """Scenario 10: DPDPA-keyed document pre-fill is DPDPA-only and never duplicates a response."""
    from app.services.auto_answer import persist_document_answers

    for frameworks in (("dpdpa", "iso27001"), ("iso27001",)):
        assessment = _seed(db, frameworks)
        db.add(DeskReviewSummary(assessment_id=assessment.id, status="completed", coverage_summary=json.dumps({"CH2.CONSENT.1": "adequate"})))
        db.commit()
        assert persist_document_answers(assessment.id, db) == 0
        assert db.query(QuestionnaireResponse).filter_by(assessment_id=assessment.id).count() == 0

    assessment = _seed(db)
    ids = ["CH2.CONSENT.1", "CH2.NOTICE.1", "CH2.MINIMIZE.1", "CH2.SECURITY.1"]
    db.add(DeskReviewSummary(assessment_id=assessment.id, status="completed", coverage_summary=json.dumps({key: "adequate" for key in ids})))
    rows = [
        QuestionnaireResponse(assessment_id=assessment.id, question_id=ids[0], answer="planned"),
        QuestionnaireResponse(assessment_id=assessment.id, question_id=ids[1], answer="planned", answer_source="inferred"),
        QuestionnaireResponse(assessment_id=assessment.id, question_id=ids[2], answer="planned", answer_source="document"),
    ]
    db.add_all(rows)
    db.commit()
    db.execute(update(QuestionnaireResponse).where(QuestionnaireResponse.id == rows[0].id).values(answer_source=None))
    db.commit()
    assert persist_document_answers(assessment.id, db) == 1
    db.commit()
    for req_id in ids:
        assert db.query(QuestionnaireResponse).filter_by(assessment_id=assessment.id, question_id=req_id).count() == 1
    db.refresh(rows[2])
    assert rows[2].answer_source == "document" and rows[2].answer == "fully_implemented"


def test_scenario_11_legacy_findings_are_quarantined(db, http, monkeypatch):
    """Scenario 11: DPDPA findings on ISO-only assessments are invisible to every reader."""
    from app.frameworks.prompts import build_framework_user_prompt
    from app.routers import analysis
    from app.services.desk_review_findings import load_desk_review_data, scoped_findings

    assessment = _seed(db, ("iso27001",))
    db.add(DeskReviewSummary(
        assessment_id=assessment.id, status="completed",
        coverage_summary=json.dumps({"CH2.CONSENT.1": "adequate"}),
    ))
    db.add_all([
        DeskReviewFinding(assessment_id=assessment.id, framework_id=None, finding_type="signal", requirement_id="CH2.CONSENT.1", content="legacy", severity="high"),
        DeskReviewFinding(assessment_id=assessment.id, framework_id="dpdpa", finding_type="evidence", requirement_id="CH2.CONSENT.1", content="legacy", severity="info"),
    ])
    db.commit()
    assert scoped_findings(db, assessment) == []
    assert load_desk_review_data(db, assessment) is None
    body = http.get(f"/assessments/{assessment.id}/desk-review-status").text
    assert "Red Flags" not in body and "0 findings" in body
    api = http.get(f"/api/assessments/{assessment.id}/desk-review").json()["findings"]
    assert api == {"evidence": [], "absences": [], "signals": []}

    seen = []
    monkeypatch.setattr("app.frameworks.questionnaire_builder.build_multi_questionnaire", lambda *_a, **_k: [])
    monkeypatch.setattr(analysis, "generate_multi_framework_initiatives", lambda *_a, **_k: [])
    monkeypatch.setattr(
        analysis,
        "run_multi_framework_analysis",
        lambda **kwargs: seen.append(kwargs.get("desk_review_data")) or {
            "frameworks": {"iso27001": {"parsed": {"executive_summary": "ok", "assessments": []}, "raw": "{}"}},
            "synthesis": None, "total_usage": {},
        },
    )
    assessment.description = "documentless input"
    db.add(QuestionnaireResponse(assessment_id=assessment.id, question_id="irrelevant", answer="fully_implemented"))
    db.commit()
    analysis.trigger_analysis(assessment.id, db)
    assert seen == [None]

    mixed = _seed(db, ("dpdpa", "iso27001"))
    mixed_data = {
        "coverage_summary": {},
        "signal_flags": [{"content": "cross", "severity": "high", "requirement_id": None, "requirement_ids": [], "framework_id": "dpdpa", "flag_type": None}],
    }
    iso = build_framework_user_prompt("iso27001", "Acme", "Technology", "medium", None, [], [], desk_review_summary=mixed_data)
    dpdpa = build_framework_user_prompt("dpdpa", "Acme", "Technology", "medium", None, [], [], desk_review_summary=mixed_data)
    assert "### Red Flags" not in iso
    assert "### Red Flags" in dpdpa


def test_scenario_12_standing_guards_and_public_signatures():
    """Scenario 12: existing seams, protected framework definitions, and model constraints stay intact."""
    from app.models.desk_review import DeskReviewFinding
    from app.services import desk_review, desk_review_findings

    assert list(pyinspect.signature(desk_review._call_claude_desk_review).parameters) == ["documents", "company_name", "industry"]
    assert list(pyinspect.signature(desk_review.run_desk_review).parameters) == ["assessment_id", "db"]
    assert "req_ids[0]" not in pyinspect.getsource(desk_review)
    models = subprocess.run(
        ["grep", "-rnE", r"relationship\(", "app/models"], cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    assert models.returncode == 1, models.stdout
    protected = subprocess.run(
        ["git", "diff", "--stat", "main", "--", "app/frameworks/definitions",
         ":!app/frameworks/definitions/dpdpa.py"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    )
    assert protected.stdout == ""
    # P6-0e edits one red-flag description in dpdpa.py; identifiers and weights stay frozen.
    dpdpa_diff = subprocess.run(
        ["git", "diff", "-U0", "main", "--", "app/frameworks/definitions/dpdpa.py"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout
    changed_lines = [
        line for line in dpdpa_diff.splitlines()
        if line[:1] in "+-" and not line.startswith(("+++", "---"))
    ]
    assert not any(
        token in line for line in changed_lines for token in ("pattern=", "id=", "Control(", "weight")
    ), changed_lines
    # schema.py may grow (P6-2a added TestCriterion / Control.test_criteria) but
    # must stay additive: no existing line removed or changed.
    schema_diff = subprocess.run(
        ["git", "diff", "-U0", "main", "--", "app/frameworks/schema.py"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    )
    removed = [l for l in schema_diff.stdout.splitlines() if l.startswith("-") and not l.startswith("---")]
    assert removed == [], removed
    source = pyinspect.getsource(desk_review_findings)
    assert "llm_client" not in source and "app.services.desk_review" not in source
    assert DeskReviewFinding.__table__.c.framework_id.default is None
