"""Contract tests for P5-4 adaptive UCC questionnaire behavior."""

from __future__ import annotations

import inspect as pyinspect
import json
import subprocess
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
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
_UNSET = object()


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
    path = tmp_path / "p5_4.sqlite3"
    command.upgrade(_cfg(path), REVISION)
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


def _seed(db, frameworks=("dpdpa",), *, context_profile=None):
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
        industry="it_services",
        company_size="medium",
        selected_frameworks=None if frameworks is None else json.dumps(list(frameworks)),
        context_profile=json.dumps(context_profile) if context_profile else None,
        engagement_id=engagement.id,
    )
    db.add(assessment)
    db.commit()
    return assessment


def _upload(db, texts, assessment, *, body="Grounded exact quote.", filename="policy.pdf"):
    from app.services.evidence import ingest_upload

    payload = b"%PDF-1.4\n% p5-4 deterministic\n%%EOF\n"
    texts[payload] = body
    return ingest_upload(
        db,
        assessment_id=assessment.id,
        filename=filename,
        content=payload,
        category="privacy_policy",
    )


def _all_questions(questionnaire):
    return [q for section in questionnaire["sections"] for q in section.get("questions", [])]


def _question(questionnaire, question_id):
    return next(q for q in _all_questions(questionnaire) if q["id"] == question_id)


def _grounded_citations():
    return json.dumps([{
        "evidence_version_id": "v1",
        "location_type": "text_span",
        "location_ref": "chars:0-5",
        "excerpt": "quote",
    }])


def _add_finding(
    db,
    assessment,
    *,
    finding_type="evidence",
    requirement_id,
    framework_id="dpdpa",
    content="Document finding",
    quote="quote",
    citations=_UNSET,
    signal_group_id=None,
    flag_type=None,
):
    finding = DeskReviewFinding(
        assessment_id=assessment.id,
        finding_type=finding_type,
        requirement_id=requirement_id,
        framework_id=framework_id,
        content=content,
        severity="high" if finding_type != "evidence" else "info",
        source_quote=quote,
        source_location="Page 1",
        citations_json=(
            _grounded_citations() if citations is _UNSET and quote else
            None if citations is _UNSET else citations
        ),
        signal_group_id=signal_group_id,
        flag_type=flag_type,
    )
    db.add(finding)
    return finding


def _set_review(db, assessment, *, coverage=None, findings=(), raw_ai_response=None, status="completed"):
    with db.no_autoflush:
        db.query(DeskReviewFinding).filter_by(assessment_id=assessment.id).delete(
            synchronize_session=False,
        )
        summary = db.query(DeskReviewSummary).filter_by(assessment_id=assessment.id).first()
        if summary is None:
            summary = DeskReviewSummary(assessment_id=assessment.id)
            db.add(summary)
        summary.status = status
        summary.coverage_summary = json.dumps(coverage or {})
        summary.raw_ai_response = raw_ai_response
        db.add_all(findings)
    db.commit()
    return summary


def _result(*, coverage=None, evidence=None, signals=None, absences=None, catalog=None):
    return {
        "document_catalog": catalog or [],
        "evidence_map": evidence or {},
        "absence_findings": absences or [],
        "signal_flags": signals or [],
        "coverage_summary": coverage or {},
    }


def test_scenario_1_routing_and_no_desk_review_baseline(db):
    """Scenario 1: routing, no-review defaults, UCC members, and tier stats are correct."""
    from app.services.question_engine import build_adaptive_questionnaire, is_dpdpa_only
    from app.services.tier_engine import compute_tier_stats

    legacy = _seed(db, None)
    dpdpa = _seed(db, ("dpdpa",))
    iso = _seed(db, ("iso27001",))
    mixed = _seed(db, ("dpdpa", "iso27001"))
    assert is_dpdpa_only(legacy) and is_dpdpa_only(dpdpa)
    assert not is_dpdpa_only(iso) and not is_dpdpa_only(mixed)

    for assessment in (iso, mixed):
        questionnaire = build_adaptive_questionnaire(assessment.id, db)
        questions = _all_questions(questionnaire)
        assert all(q["status"] == "active" for q in questions)
        assert all(q[key] is None for q in questions for key in (
            "pre_fill_answer", "pre_fill_confidence", "pre_fill_source", "pre_fill_evidence_summary",
        ))
        assert all(q["desk_review_evidence"] is None for q in questions)
        assert all(q["desk_review_note"] == q["context_note"] for q in questions)
        assert questionnaire["stats"]["pre_filled_questions"] == 0
        assert questionnaire["stats"]["deepened_questions"] == 0
        assert questionnaire["stats"]["tier_counts"] == compute_tier_stats(questions)
        assert set(questionnaire["stats"]["tier_counts"]) == {"deep", "standard", "light", "skip"}
        assert sum(questionnaire["stats"]["tier_counts"].values()) == questionnaire["stats"]["total_questions"]
        assert all(
            [member["control_id"] for member in q["member_controls"]] == q["maps_to"]
            for q in questions
        )

    iso.context_profile = json.dumps({"risk_tier": "HIGH"})
    db.commit()
    assert _question(build_adaptive_questionnaire(iso.id, db), "SINGLE.ISO.A5.1")["tier"] == "deep"
    iso.context_profile = json.dumps({"risk_tier": "MEDIUM"})
    db.commit()
    assert _question(build_adaptive_questionnaire(iso.id, db), "SINGLE.ISO.A5.1")["tier"] == "standard"

    _set_review(db, iso, status="analyzing")
    assert all(
        q["status"] == "active"
        for q in _all_questions(build_adaptive_questionnaire(iso.id, db))
    )


def test_scenario_2_grounded_citation_helper(db):
    """Scenario 2: only a non-blank quote with a text_span citation is grounded."""
    from app.services.desk_review_findings import (
        GROUNDED_CITATION_LOCATION_TYPE,
        finding_has_grounded_citation,
    )

    assessment = _seed(db, ("iso27001",))
    cases = [
        ("evidence", "x", _grounded_citations(), True),
        ("evidence", "x", json.dumps([{ "location_type": "whole_item" }]), False),
        ("evidence", "", _grounded_citations(), False),
        ("evidence", "x", "[]", False),
        ("evidence", "x", None, False),
        ("evidence", "x", "not json", False),
        ("evidence", "x", '{"a": 1}', False),
        ("signal", "x", _grounded_citations(), False),
    ]
    for finding_type, quote, citations, expected in cases:
        finding = _add_finding(
            db, assessment, finding_type=finding_type, requirement_id="ISO.A5.1",
            quote=quote, citations=citations,
        )
        assert finding_has_grounded_citation(finding) is expected
    assert GROUNDED_CITATION_LOCATION_TYPE == "text_span"


def test_scenario_3_cluster_deepen(db):
    """Scenario 3: any member absence, absent coverage, or signal deepens a cluster."""
    from app.services.question_engine import (
        CLUSTER_ABSENT_COVERAGE_ITEM,
        CLUSTER_ABSENCE_ITEM,
        CLUSTER_NOTE_OVERFLOW,
        build_adaptive_questionnaire,
    )

    assessment = _seed(db, ("dpdpa", "iso27001", "nist_csf"))
    assert _question(build_adaptive_questionnaire(assessment.id, db), "CLUSTER_002")["maps_to"] == [
        "CH4.SDF.1", "ISO.A5.2", "NIST.GV.RR.02", "NIST.GV.RR.03",
    ]

    _set_review(db, assessment, findings=[_add_finding(
        db, assessment, finding_type="absence", requirement_id="ISO.A5.2",
        framework_id="iso27001", content="No owner", quote="",
        citations="[]",
    )])
    question = _question(build_adaptive_questionnaire(assessment.id, db), "CLUSTER_002")
    assert question["status"] == "deepened" and question["follow_up_enabled"]
    assert question["tier"] == "deep"
    assert question["desk_review_note"] == CLUSTER_ABSENCE_ITEM.format(
        control_id="ISO.A5.2", content="No owner"
    )

    signals = [
        _add_finding(db, assessment, finding_type="signal", requirement_id=control_id,
                     framework_id="nist_csf", content="No role owner", quote="",
                     citations="[]", signal_group_id="signal-1", flag_type="unclassified")
        for control_id in ("NIST.GV.RR.02", "NIST.GV.RR.03")
    ]
    _set_review(db, assessment, findings=signals)
    question = _question(build_adaptive_questionnaire(assessment.id, db), "CLUSTER_002")
    assert question["desk_review_note"].count("Signal detected (NIST.GV.RR.02, NIST.GV.RR.03): ") == 1

    _set_review(db, assessment, findings=[_add_finding(
        db, assessment, finding_type="signal", requirement_id="CH4.SDF.1",
        framework_id=None, content="Legacy signal", quote="", citations="[]",
    )])
    assert _question(build_adaptive_questionnaire(assessment.id, db), "CLUSTER_002")["status"] == "deepened"

    _set_review(db, assessment, coverage={"CH4.SDF.1": "absent"})
    question = _question(build_adaptive_questionnaire(assessment.id, db), "CLUSTER_002")
    assert CLUSTER_ABSENT_COVERAGE_ITEM.format(control_id="CH4.SDF.1") in question["desk_review_note"]

    findings = [
        _add_finding(db, assessment, finding_type="absence", requirement_id=control_id,
                     framework_id=framework_id, content=f"Finding {index}", quote="", citations="[]")
        for index, (control_id, framework_id) in enumerate([
            ("CH4.SDF.1", "dpdpa"), ("ISO.A5.2", "iso27001"),
            ("NIST.GV.RR.02", "nist_csf"), ("NIST.GV.RR.03", "nist_csf"),
        ], start=1)
    ]
    findings.append(_add_finding(
        db, assessment, finding_type="absence", requirement_id="CH4.SDF.1",
        framework_id="dpdpa", content="Finding 5", quote="", citations="[]",
    ))
    _set_review(db, assessment, findings=findings)
    note = _question(build_adaptive_questionnaire(assessment.id, db), "CLUSTER_002")["desk_review_note"]
    assert note.startswith("CH4.SDF.1: No evidence found in documents: Finding 1")
    assert note.endswith(CLUSTER_NOTE_OVERFLOW.format(n=2))

    _set_review(db, assessment, findings=[_add_finding(
        db, assessment, finding_type="signal", requirement_id=None,
        framework_id="nist_csf", content="Cross-cutting", quote="", citations="[]",
    )])
    assert _question(build_adaptive_questionnaire(assessment.id, db), "CLUSTER_002")["status"] == "active"

    findings = [
        _add_finding(db, assessment, finding_type="signal", requirement_id="ISO.A5.2",
                     framework_id="iso27001", content="Signal", quote="", citations="[]"),
        _add_finding(db, assessment, requirement_id="NIST.GV.RR.02", framework_id="nist_csf"),
    ]
    _set_review(db, assessment, findings=findings)
    question = _question(build_adaptive_questionnaire(assessment.id, db), "CLUSTER_002")
    assert question["status"] == "deepened"
    assert any(e["control_id"] == "NIST.GV.RR.02" for e in question["desk_review_evidence"])
    assert all(question[key] is None for key in (
        "pre_fill_answer", "pre_fill_confidence", "pre_fill_source", "pre_fill_evidence_summary",
    ))


def test_scenario_4_cluster_prefill(db):
    """Scenario 4: each member needs grounded coverage before a cluster is pre-filled."""
    from app.services.question_engine import (
        CLUSTER_EVIDENCE_NOTE,
        CLUSTER_PREFILL_NOTE,
        build_adaptive_questionnaire,
    )

    assessment = _seed(db, ("iso27001",))
    def evidence(control_id="ISO.A5.37", framework_id="iso27001", quote="quote"):
        return _add_finding(db, assessment, requirement_id=control_id, framework_id=framework_id, quote=quote)

    _set_review(db, assessment, coverage={"ISO.A5.37": "adequate"}, findings=[evidence()])
    question = _question(build_adaptive_questionnaire(assessment.id, db), "SINGLE.ISO.A5.37")
    assert question["status"] == "pre_filled"
    assert question["pre_fill_answer"] == "fully_implemented"
    assert question["pre_fill_confidence"] == "high"
    assert question["pre_fill_source"] == "document"
    assert question["tier"] == "light" and question["desk_review_note"] == CLUSTER_PREFILL_NOTE
    assert "quote" in question["pre_fill_evidence_summary"]

    _set_review(db, assessment, coverage={"ISO.A5.1": "adequate"}, findings=[evidence("ISO.A5.1")])
    assert _question(build_adaptive_questionnaire(assessment.id, db), "SINGLE.ISO.A5.1")["tier"] == "standard"
    _set_review(db, assessment, coverage={"ISO.A5.37": "partial"}, findings=[evidence()])
    question = _question(build_adaptive_questionnaire(assessment.id, db), "SINGLE.ISO.A5.37")
    assert (question["pre_fill_answer"], question["pre_fill_confidence"]) == ("partially_implemented", "medium")

    for citations in (json.dumps([{ "location_type": "whole_item" }]), "[]"):
        _set_review(db, assessment, coverage={"ISO.A5.37": "adequate"}, findings=[
            _add_finding(
                db,
                assessment,
                requirement_id="ISO.A5.37",
                framework_id="iso27001",
                citations=citations,
            ),
        ])
        question = _question(build_adaptive_questionnaire(assessment.id, db), "SINGLE.ISO.A5.37")
        assert question["status"] == "active"
        assert question["desk_review_note"] == CLUSTER_EVIDENCE_NOTE
        assert question["desk_review_evidence"]

    _set_review(db, assessment, coverage={}, findings=[evidence()])
    assert _question(build_adaptive_questionnaire(assessment.id, db), "SINGLE.ISO.A5.37")["status"] == "active"

    mixed = _seed(db, ("dpdpa", "iso27001"))
    members = ["CH2.NOTICE.3", "CH3.GRIEVANCE.1", "CH3.GRIEVANCE.2"]
    findings = [
        _add_finding(db, mixed, requirement_id=member, framework_id="dpdpa")
        for member in members
    ]
    _set_review(db, mixed, coverage={members[0]: "adequate", members[1]: "adequate", members[2]: "partial"}, findings=findings)
    question = _question(build_adaptive_questionnaire(mixed.id, db), "CLUSTER_022")
    assert (question["pre_fill_answer"], question["pre_fill_confidence"]) == ("partially_implemented", "medium")
    findings[-1].citations_json = json.dumps([{ "location_type": "whole_item" }])
    db.commit()
    question = _question(build_adaptive_questionnaire(mixed.id, db), "CLUSTER_022")
    assert question["status"] == "active"
    questionnaire = build_adaptive_questionnaire(assessment.id, db)
    assert questionnaire["stats"]["pre_filled_questions"] == sum(
        q["status"] == "pre_filled" for q in _all_questions(questionnaire)
    )


def test_scenario_5_framework_quarantine_and_dp5c(db):
    """Scenario 5: DPDPA-keyed findings cannot pre-fill another framework control."""
    from app.services.question_engine import (
        CLUSTER_EVIDENCE_NOTE,
        _load_cluster_desk_data,
        build_adaptive_questionnaire,
    )

    assessment = _seed(db, ("dpdpa", "iso27001", "nist_csf"))
    findings = [_add_finding(db, assessment, requirement_id="CH4.SDF.1", framework_id="dpdpa")]
    _set_review(db, assessment, coverage={"CH4.SDF.1": "adequate"}, findings=findings)
    question = _question(build_adaptive_questionnaire(assessment.id, db), "CLUSTER_002")
    assert question["status"] == "active" and question["desk_review_note"] == CLUSTER_EVIDENCE_NOTE

    findings = [
        _add_finding(db, assessment, requirement_id=control_id, framework_id=framework_id)
        for control_id, framework_id in (
            ("CH4.SDF.1", "dpdpa"), ("ISO.A5.2", "iso27001"),
            ("NIST.GV.RR.02", "nist_csf"), ("NIST.GV.RR.03", "nist_csf"),
        )
    ]
    _set_review(db, assessment, coverage={f.requirement_id: "adequate" for f in findings}, findings=findings)
    assert _question(build_adaptive_questionnaire(assessment.id, db), "CLUSTER_002")["status"] == "pre_filled"

    miskeyed = _add_finding(
        db, assessment, requirement_id="ISO.A5.2", framework_id="dpdpa",
        content="mis-keyed evidence",
    )
    _set_review(db, assessment, coverage={
        "CH4.SDF.1": "adequate", "ISO.A5.2": "adequate",
        "NIST.GV.RR.02": "adequate", "NIST.GV.RR.03": "adequate",
    }, findings=[
        _add_finding(db, assessment, requirement_id="CH4.SDF.1", framework_id="dpdpa"),
        _add_finding(db, assessment, requirement_id="NIST.GV.RR.02", framework_id="nist_csf"),
        _add_finding(db, assessment, requirement_id="NIST.GV.RR.03", framework_id="nist_csf"),
        miskeyed,
    ])
    desk = _load_cluster_desk_data(assessment, db)
    assert "ISO.A5.2" not in desk.evidence
    assert _question(build_adaptive_questionnaire(assessment.id, db), "CLUSTER_002")["status"] == "active"
    signal = _add_finding(
        db, assessment, finding_type="signal", requirement_id="ISO.A5.2", framework_id="dpdpa",
        content="mis-keyed signal", quote="", citations="[]",
    )
    _set_review(db, assessment, coverage={
        "CH4.SDF.1": "adequate", "ISO.A5.2": "adequate",
        "NIST.GV.RR.02": "adequate", "NIST.GV.RR.03": "adequate",
    }, findings=[
        _add_finding(db, assessment, requirement_id="CH4.SDF.1", framework_id="dpdpa"),
        _add_finding(db, assessment, requirement_id="NIST.GV.RR.02", framework_id="nist_csf"),
        _add_finding(db, assessment, requirement_id="NIST.GV.RR.03", framework_id="nist_csf"),
        miskeyed, signal,
    ])
    assert _question(build_adaptive_questionnaire(assessment.id, db), "CLUSTER_002")["status"] == "active"

    mixed = _seed(db, ("dpdpa", "iso27001"))
    _set_review(db, mixed, coverage={"CH2.NOTICE.2": "adequate"}, findings=[
        _add_finding(db, mixed, requirement_id="CH2.NOTICE.2", framework_id=None),
    ])
    assert _question(build_adaptive_questionnaire(mixed.id, db), "CLUSTER_021")["status"] == "pre_filled"

    iso = _seed(db, ("iso27001",))
    legacy = _add_finding(db, iso, requirement_id="CH2.CONSENT.1", framework_id=None)
    _set_review(db, iso, coverage={"CH2.CONSENT.1": "adequate"}, findings=[legacy])
    assert not _load_cluster_desk_data(iso, db).evidence
    assert all(q["status"] == "active" for q in _all_questions(build_adaptive_questionnaire(iso.id, db)))


def test_scenario_6_failed_framework(db):
    """Scenario 6: failed framework members remain active and explain why."""
    from app.frameworks.registry import FrameworkRegistry
    from app.services.question_engine import _load_cluster_desk_data, build_adaptive_questionnaire

    assessment = _seed(db, ("dpdpa", "iso27001", "nist_csf"))
    raw = json.dumps({
        "schema_version": 2,
        "frameworks": {
            "dpdpa": {"status": "completed"},
            "iso27001": {"status": "completed"},
            "nist_csf": {"status": "error", "error": "boom"},
        },
    })
    findings = [
        _add_finding(db, assessment, requirement_id="CH4.SDF.1", framework_id="dpdpa"),
        _add_finding(db, assessment, requirement_id="ISO.A5.2", framework_id="iso27001"),
        _add_finding(db, assessment, requirement_id="CH2.NOTICE.2", framework_id="dpdpa"),
    ]
    _set_review(db, assessment, coverage={
        "CH4.SDF.1": "adequate", "ISO.A5.2": "adequate", "CH2.NOTICE.2": "adequate",
    }, findings=findings, raw_ai_response=raw)
    questionnaire = build_adaptive_questionnaire(assessment.id, db)
    q002 = _question(questionnaire, "CLUSTER_002")
    assert q002["status"] == "active"
    assert q002["desk_review_note"].endswith(
        "Desk review did not complete for NIST CSF, so this question was not pre-filled from documents."
    )
    assert _question(questionnaire, "CLUSTER_021")["status"] == "pre_filled"
    assert _load_cluster_desk_data(assessment, db).failed_frameworks == frozenset({"nist_csf"})

    summary = db.query(DeskReviewSummary).filter_by(assessment_id=assessment.id).one()
    summary.raw_ai_response = json.dumps({"legacy": True})
    db.commit()
    assert _load_cluster_desk_data(assessment, db).failed_frameworks == frozenset()


def test_scenario_7_tiering_reuses_unchanged_engine(db):
    """Scenario 7: every cluster tier matches the unchanged tier engine."""
    from app.services.question_engine import build_adaptive_questionnaire
    from app.services.tier_engine import assign_tier

    assessment = _seed(db, ("iso27001",), context_profile={"risk_tier": "HIGH"})
    questionnaire = build_adaptive_questionnaire(assessment.id, db)
    assert all(q["tier"] == assign_tier(q, "HIGH") for q in _all_questions(questionnaire))
    result = subprocess.run(
        ["git", "diff", "--stat", "main", "--", "app/services/tier_engine.py"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    )
    assert result.stdout == ""
    assert pyinspect.getsource(assign_tier)


def test_scenario_8_cluster_prefill_persistence(db, engine, texts, monkeypatch):
    """Scenario 8: desk review writes and refreshes cluster-keyed document pre-fills."""
    monkeypatch.setattr(settings, "llm_batch_threshold_controls", 10_000)  # P6-1b: pins the unbatched call shape this test characterises (D-P6-1b-L)
    from app.services import desk_review
    from app.services.auto_answer import persist_document_answers
    from app.services import question_engine

    assessment = _seed(db, ("dpdpa", "iso27001"))
    _upload(
        db,
        texts,
        assessment,
        body="Board approved privacy officer. Named security owner.",
    )
    monkeypatch.setattr(
        desk_review,
        "_call_claude_desk_review",
        lambda **_kwargs: _result(
            coverage={"CH4.SDF.1": "adequate"},
            evidence={"CH4.SDF.1": [{
                "quote": "Board approved privacy officer",
                "document": "policy.pdf", "location": "Page 1",
            }]},
        ),
    )
    monkeypatch.setattr(
        desk_review,
        "_call_framework_desk_review",
        lambda _framework_id, *_args: _result(
            coverage={"ISO.A5.2": "adequate"},
            evidence={"ISO.A5.2": [{
                "quote": "Named security owner",
                "document": "policy.pdf", "location": "Page 1",
            }]},
        ),
    )
    desk_review.run_desk_review(assessment.id, db)
    row = db.query(QuestionnaireResponse).filter_by(assessment_id=assessment.id).one()
    assert (row.question_id, row.answer, row.answer_source, row.confidence) == (
        "CLUSTER_002", "fully_implemented", "document", "high",
    )
    assert "Board approved privacy officer" in row.notes
    assert "Named security owner" in row.notes
    assert not db.query(QuestionnaireResponse).filter(
        QuestionnaireResponse.assessment_id == assessment.id,
        QuestionnaireResponse.question_id.in_(["CH4.SDF.1", "ISO.A5.2"]),
    ).count()
    document_prefills = [
        q for q in _all_questions(question_engine.build_adaptive_questionnaire(assessment.id, db))
        if q["status"] == "pre_filled" and q["pre_fill_source"] == "document"
    ]
    assert db.query(QuestionnaireResponse).filter_by(
        assessment_id=assessment.id, answer_source="document",
    ).count() == len(document_prefills)

    second = sessionmaker(bind=engine)()
    try:
        monkeypatch.setattr(
            desk_review,
            "_call_claude_desk_review",
            lambda **_kwargs: _result(
                coverage={"CH4.SDF.1": "partial"},
                evidence={"CH4.SDF.1": [{
                    "quote": "Board approved privacy officer",
                    "document": "policy.pdf", "location": "Page 1",
                }]},
            ),
        )
        desk_review.run_desk_review(assessment.id, second)
        refreshed = second.query(QuestionnaireResponse).filter_by(
            assessment_id=assessment.id, question_id="CLUSTER_002",
        ).one()
        assert (refreshed.answer, refreshed.confidence) == ("partially_implemented", "medium")
    finally:
        second.close()

    original_builder = question_engine.build_adaptive_questionnaire
    fake_questions = [
        {"id": "CLUSTER_002", "status": "pre_filled", "pre_fill_source": "document",
         "pre_fill_answer": "fully_implemented", "pre_fill_confidence": "high",
         "pre_fill_evidence_summary": "quote", "desk_review_evidence": []},
        {"id": "CLUSTER_003", "status": "pre_filled", "pre_fill_source": "document",
         "pre_fill_answer": "fully_implemented", "pre_fill_confidence": "high",
         "pre_fill_evidence_summary": "quote", "desk_review_evidence": []},
        {"id": "CLUSTER_004", "status": "pre_filled", "pre_fill_source": "document",
         "pre_fill_answer": "fully_implemented", "pre_fill_confidence": "high",
         "pre_fill_evidence_summary": "quote", "desk_review_evidence": []},
    ]
    monkeypatch.setattr(
        question_engine,
        "build_adaptive_questionnaire",
        lambda *_args: {"sections": [{"questions": fake_questions}]},
    )
    existing = [
        QuestionnaireResponse(assessment_id=assessment.id, question_id="CLUSTER_002", answer="planned", answer_source="human"),
        QuestionnaireResponse(assessment_id=assessment.id, question_id="CLUSTER_003", answer="planned", answer_source=None),
        QuestionnaireResponse(assessment_id=assessment.id, question_id="CLUSTER_004", answer="planned", answer_source="inferred"),
    ]
    db.add_all(existing)
    db.commit()
    assert persist_document_answers(assessment.id, db) == 0
    assert db.query(QuestionnaireResponse).filter(
        QuestionnaireResponse.assessment_id == assessment.id,
        QuestionnaireResponse.question_id.in_([q["id"] for q in fake_questions]),
    ).count() == 4
    monkeypatch.setattr(question_engine, "build_adaptive_questionnaire", original_builder)

    dpdpa = _seed(db, ("dpdpa",))
    _set_review(db, dpdpa, coverage={"CH2.CONSENT.1": "adequate"})
    db.add(QuestionnaireResponse(
        assessment_id=dpdpa.id,
        question_id="CH2.CONSENT.1",
        answer="planned",
        answer_source="human",
    ))
    db.commit()
    assert persist_document_answers(dpdpa.id, db) == 0


def test_scenario_9_analysis_excludes_unconfirmed_cluster_prefill(db, texts, monkeypatch):
    """Scenario 9: analysis sees a cluster row only after section-save confirmation."""
    from app.routers import analysis
    from app.schemas.analysis import CompletionOverride
    from app.services import question_engine
    from app.frameworks.prompts import _expand_cluster_responses

    assessment = _seed(db, ("dpdpa", "iso27001"))
    _upload(db, texts, assessment)
    db.add(QuestionnaireResponse(
        assessment_id=assessment.id, question_id="CLUSTER_002",
        answer="fully_implemented", answer_source="document",
    ))
    db.commit()
    captured = []

    def fake_analysis(**kwargs):
        captured.append(kwargs["responses"])
        return {
            "frameworks": {
                framework_id: {"parsed": {"assessments": [], "executive_summary": "ok"}, "raw": "{}"}
                for framework_id in assessment.frameworks
            },
            "synthesis": None,
            "total_usage": {},
        }

    monkeypatch.setattr(analysis, "run_multi_framework_analysis", fake_analysis)
    monkeypatch.setattr(analysis, "generate_multi_framework_initiatives", lambda *_args, **_kwargs: [])
    override = CompletionOverride(reason="document_led")
    analysis.trigger_analysis(assessment.id, db, override=override)
    assert all(row["question_id"] != "CLUSTER_002" for row in captured[-1])

    db.query(QuestionnaireResponse).filter_by(
        assessment_id=assessment.id, question_id="CLUSTER_002",
    ).update({"answer_source": "document_confirmed"})
    db.commit()
    assessment.status = "questionnaire_done"
    db.commit()
    analysis.trigger_analysis(assessment.id, db, override=override)
    confirmed = next(row for row in captured[-1] if row["question_id"] == "CLUSTER_002")
    assert confirmed["answer_source"] if "answer_source" in confirmed else True
    assert _expand_cluster_responses(
        [{"question_id": "CLUSTER_002", "answer": "fully_implemented"}],
        "iso27001", {"ISO.A5.2"},
    )[0]["question_id"] == "ISO.A5.2"


def test_scenario_10_live_prefill_render_and_save_provenance(db, http):
    """Scenario 10: live document pre-fills render and save with durable provenance."""
    from app.services.question_engine import build_adaptive_questionnaire
    from sqlalchemy import update

    assessment = _seed(db, ("dpdpa", "iso27001"))
    members = [
        ("CH4.SDF.1", "dpdpa"), ("ISO.A5.2", "iso27001"),
    ]
    _set_review(db, assessment, coverage={control_id: "adequate" for control_id, _ in members}, findings=[
        _add_finding(db, assessment, requirement_id=control_id, framework_id=framework_id)
        for control_id, framework_id in members
    ])
    db.add(QuestionnaireResponse(
        assessment_id=assessment.id, question_id="CLUSTER_002",
        answer="fully_implemented", answer_source="document",
    ))
    db.commit()
    q = _question(build_adaptive_questionnaire(assessment.id, db), "CLUSTER_002")
    section_id = q["section"]
    response = http.get(f"/assessments/{assessment.id}/questionnaire/section/{section_id}")
    assert response.status_code == 200
    assert 'name="answer_CLUSTER_002" value="fully_implemented"' in response.text
    assert 'name="answer_CLUSTER_002" value="fully_implemented" class="sr-only" checked' in response.text

    _set_review(db, assessment, coverage={}, findings=[_add_finding(
        db, assessment, finding_type="absence", requirement_id="ISO.A5.2",
        framework_id="iso27001", content="No owner", quote="", citations="[]",
    )])
    response = http.get(f"/assessments/{assessment.id}/questionnaire/section/{section_id}")
    assert 'name="answer_CLUSTER_002" value="fully_implemented" class="sr-only" checked' not in response.text
    assert db.query(QuestionnaireResponse).filter_by(
        assessment_id=assessment.id, question_id="CLUSTER_002",
    ).one().answer_source == "document"

    def post_answer(answer):
        return http.post(
            f"/assessments/{assessment.id}/questionnaire/save",
            data={"section_id": section_id, "answer_CLUSTER_002": answer},
        )

    _set_review(db, assessment, coverage={control_id: "adequate" for control_id, _ in members}, findings=[
        _add_finding(db, assessment, requirement_id=control_id, framework_id=framework_id)
        for control_id, framework_id in members
    ])
    post_answer("fully_implemented")
    assert db.query(QuestionnaireResponse).filter_by(
        assessment_id=assessment.id, question_id="CLUSTER_002",
    ).one().answer_source == "document_confirmed"
    row = db.query(QuestionnaireResponse).filter_by(
        assessment_id=assessment.id, question_id="CLUSTER_002",
    ).one()
    row.answer_source = "document"
    db.commit()
    post_answer("partially_implemented")
    assert db.query(QuestionnaireResponse).filter_by(
        assessment_id=assessment.id, question_id="CLUSTER_002",
    ).one().answer_source == "human_override"

    db.query(QuestionnaireResponse).filter_by(
        assessment_id=assessment.id, question_id="CLUSTER_002",
    ).delete()
    db.commit()
    post_answer("fully_implemented")
    assert db.query(QuestionnaireResponse).filter_by(
        assessment_id=assessment.id, question_id="CLUSTER_002",
    ).one().answer_source == "document_confirmed"
    db.query(QuestionnaireResponse).filter_by(
        assessment_id=assessment.id, question_id="CLUSTER_002",
    ).delete()
    db.commit()
    post_answer("not_implemented")
    assert db.query(QuestionnaireResponse).filter_by(
        assessment_id=assessment.id, question_id="CLUSTER_002",
    ).one().answer_source == "human_override"

    # A stale document row is human input once the live state is deepened.
    _set_review(db, assessment, coverage={}, findings=[_add_finding(
        db, assessment, finding_type="absence", requirement_id="ISO.A5.2",
        framework_id="iso27001", content="No owner", quote="", citations="[]",
    )])
    db.query(QuestionnaireResponse).filter_by(
        assessment_id=assessment.id, question_id="CLUSTER_002",
    ).one().answer_source = "document"
    db.commit()
    post_answer("not_implemented")
    assert db.query(QuestionnaireResponse).filter_by(
        assessment_id=assessment.id, question_id="CLUSTER_002",
    ).one().answer_source == "human"

    # Existing human, inferred, and NULL sources follow the shared transition rule.
    for source, expected in (("human", "human"), ("inferred", "human"), (None, "human")):
        row = db.query(QuestionnaireResponse).filter_by(
            assessment_id=assessment.id, question_id="CLUSTER_002",
        ).one()
        row.answer_source = source or "human"
        db.commit()
        if source is None:
            db.execute(update(QuestionnaireResponse).where(
                QuestionnaireResponse.id == row.id,
            ).values(answer_source=None))
            db.commit()
        post_answer("fully_implemented")
        assert db.query(QuestionnaireResponse).filter_by(
            assessment_id=assessment.id, question_id="CLUSTER_002",
        ).one().answer_source == expected

    dpdpa = _seed(db, ("dpdpa",))
    _set_review(db, dpdpa, coverage={"CH2.CONSENT.1": "adequate"})
    db.add(QuestionnaireResponse(
        assessment_id=dpdpa.id, question_id="CH2.CONSENT.1",
        answer="fully_implemented", answer_source="document",
    ))
    db.commit()
    base_q = _question(build_adaptive_questionnaire(dpdpa.id, db), "CH2.CONSENT.1")
    assert base_q["status"] == "active"
    section = base_q["section"]
    html = http.get(f"/assessments/{dpdpa.id}/questionnaire/section/{section}").text
    assert 'name="answer_CH2.CONSENT.1" value="fully_implemented" class="sr-only" checked' not in html
    http.post(f"/assessments/{dpdpa.id}/questionnaire/save", data={
        "section_id": section, "answer_CH2.CONSENT.1": "fully_implemented",
    })
    assert db.query(QuestionnaireResponse).filter_by(
        assessment_id=dpdpa.id, question_id="CH2.CONSENT.1",
    ).one().answer_source == "human"


def test_scenario_11_progress_and_response_count(db, http, monkeypatch):
    """Scenario 11: progress counts confirmed rendered answers and live pending pre-fills."""
    from app.services.question_engine import build_adaptive_questionnaire, questionnaire_progress

    assessment = _seed(db, ("dpdpa", "iso27001"))
    members = [("CH4.SDF.1", "dpdpa"), ("ISO.A5.2", "iso27001")]
    _set_review(db, assessment, coverage={control_id: "adequate" for control_id, _ in members}, findings=[
        _add_finding(db, assessment, requirement_id=control_id, framework_id=framework_id)
        for control_id, framework_id in members
    ])
    questionnaire = build_adaptive_questionnaire(assessment.id, db)
    ids = [q["id"] for q in _all_questions(questionnaire) if q["id"] != "CLUSTER_002"]
    db.add_all([
        QuestionnaireResponse(assessment_id=assessment.id, question_id=ids[0], answer="planned", answer_source="human"),
        QuestionnaireResponse(assessment_id=assessment.id, question_id=ids[1], answer="planned", answer_source="human"),
        QuestionnaireResponse(assessment_id=assessment.id, question_id="CLUSTER_002", answer="fully_implemented", answer_source="document"),
        QuestionnaireResponse(assessment_id=assessment.id, question_id="CH2.CONSENT.1", answer="planned", answer_source="document"),
        QuestionnaireResponse(assessment_id=assessment.id, question_id="CH2.NOTICE.1", answer="planned", answer_source="document"),
        QuestionnaireResponse(assessment_id=assessment.id, question_id="CH2.MINIMIZE.1", answer="planned", answer_source="document"),
        QuestionnaireResponse(assessment_id=assessment.id, question_id="FU.CLUSTER_002.1", answer="planned", answer_source="human"),
    ])
    db.commit()
    assert questionnaire_progress(questionnaire, assessment.id, db) == {
        "answered_questions": 2, "awaiting_confirmation": 1,
    }
    page = http.get(f"/assessments/{assessment.id}?tab=questionnaire")
    assert page.status_code == 200
    assert "2 questions answered" in page.text
    sections = http.get(f"/assessments/{assessment.id}/questionnaire/sections")
    assert 'data-stat-answered' in sections.text and "2 answered" in sections.text
    assert 'data-stat-awaiting-confirmation' in sections.text
    assert "1 pre-filled answers awaiting confirmation" in sections.text

    dpdpa = _seed(db, ("dpdpa",))
    all_ids = [q["id"] for q in _all_questions(build_adaptive_questionnaire(dpdpa.id, db))]
    dpdpa.applicable_requirements = json.dumps(all_ids[:10])
    db.commit()
    out_scope = http.get(f"/assessments/{dpdpa.id}/questionnaire/sections")
    assert "out of scope" in out_scope.text and "covered by documents" not in out_scope.text

    monkeypatch.setattr("app.routers.web.build_adaptive_questionnaire", lambda *_args: (_ for _ in ()).throw(RuntimeError("builder down")))
    fallback = http.get(f"/assessments/{assessment.id}?tab=questionnaire")
    assert fallback.status_code == 200 and "2 questions answered" in fallback.text


def test_scenario_12_screening_visibility_and_copy(db, http, monkeypatch):
    """Scenario 12: screening is visible only on DPDPA-only assessments and copy is honest."""
    from app.services import screening

    for frameworks in (("iso27001",), ("dpdpa", "iso27001")):
        assessment = _seed(db, frameworks)
        assessment.context_answers = "[]"
        db.commit()
        page = http.get(f"/assessments/{assessment.id}?tab=questionnaire")
        assert 'id="screening-section"' not in page.text
        assert "Start screening" not in page.text
        assert 'data-screening-unavailable' in page.text
        assert screening.SCREENING_NOT_APPLICABLE_MESSAGE in page.text
        form = http.get(f"/assessments/{assessment.id}/screening")
        assert screening.SCREENING_NOT_APPLICABLE_MESSAGE in form.text and "<form" not in form.text
        called = []
        monkeypatch.setattr(screening, "_call_llm", lambda **_kwargs: called.append(True))
        submitted = http.post(f"/assessments/{assessment.id}/screening/submit", data={})
        assert submitted.status_code == 200
        assert screening.SCREENING_NOT_APPLICABLE_MESSAGE in submitted.text
        assert called == []

    dpdpa = _seed(db, ("dpdpa",))
    dpdpa.context_answers = "[]"
    db.commit()
    page = http.get(f"/assessments/{dpdpa.id}?tab=questionnaire")
    assert 'id="screening-section"' in page.text and "~30%" not in page.text
    form = http.get(f"/assessments/{dpdpa.id}/screening")
    assert "<form" in form.text and "30-40%" not in form.text
    assert "screening_applies(" in pyinspect.getsource(screening.run_screening_pass)
    assert '!= ["dpdpa"]' not in pyinspect.getsource(screening.run_screening_pass)


def test_scenario_13_structural_guards(db):
    """Scenario 13: protected surfaces, provenance vocabulary, and no retired keyword path remain."""
    from app.services import question_engine
    from app.services.auto_answer import UNCONFIRMED_ANSWER_SOURCES
    from app.services.desk_review_findings import GROUNDED_CITATION_LOCATION_TYPE

    protected = subprocess.run([
        "git", "diff", "--stat", "main", "--",
        "app/services/scoring.py", "app/routers/reports.py",
        "app/utils/pdf_export.py", "app/routers/review.py", "app/services/tier_engine.py",
        "app/frameworks", "app/dpdpa", "alembic", "app/models",
    ], cwd=REPO_ROOT, capture_output=True, text=True, check=True)
    assert protected.stdout == ""
    analysis_diff = subprocess.run([
        "git", "diff", "main", "--", "app/routers/analysis.py",
    ], cwd=REPO_ROOT, capture_output=True, text=True, check=True)
    assert analysis_diff.stdout.count('+            "answer_source": r.answer_source,') == 1
    assert '-            "answer_source": r.answer_source,' not in analysis_diff.stdout
    assert "content_lower" not in pyinspect.getsource(question_engine)
    assert "flag_type" not in pyinspect.getsource(question_engine._load_cluster_desk_data)
    assert "flag_type" not in pyinspect.getsource(question_engine._modulate_cluster_question)
    findings_source = pyinspect.getsource(__import__("app.services.desk_review_findings", fromlist=["x"]))
    assert "llm_client" not in findings_source and "app.services.desk_review" not in findings_source
    assert UNCONFIRMED_ANSWER_SOURCES == ("document", "inferred")
    assert GROUNDED_CITATION_LOCATION_TYPE == "text_span"
    assert subprocess.run([".venv/bin/alembic", "heads"], cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout.strip() == f"{REVISION} (head)"
    for template in (
        "app/templates/partials/questionnaire_tab.html",
        "app/templates/partials/screening_form.html",
        "app/templates/partials/questionnaire_sections.html",
    ):
        source = (REPO_ROOT / template).read_text()
        assert "|safe" not in source and "CyberAssess" not in source and "overall_score" not in source
