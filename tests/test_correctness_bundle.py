"""Contract tests for the P5-1 correctness bundle."""

from __future__ import annotations

import copy
import inspect
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pdfplumber
import pytest
from alembic import command
from alembic.config import Config
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.config import settings
from app.database import get_db
from app.dpdpa.questionnaire import build_questionnaire
from app.frameworks.registry import FrameworkRegistry
from app.main import app
from app.models.analysis_run import AnalysisRun
from app.models.assessment import Assessment
from app.models.audit_event import AuditEvent
from app.models.client import Client
from app.models.engagement import Engagement
from app.models.questionnaire import QuestionnaireResponse
from app.models.report import GapItem, GapReport
from app.models.rfi import RFIDocument
from app.models.report_snapshot import ReportSnapshot
from app.routers import analysis, web
from app.schemas.report import FrameworkScoreOut
from app.services import evidence as evidence_service, report_content
from app.services.scoring import (
    compute_framework_scores,
    failed_framework_scores,
    is_failed_framework_score,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_SCOPE_IDS = {
    "CB.TRANSFER.1",
    "CB.TRANSFER.2",
    "CB.TRANSFER.3",
    "CH2.CONSENT.5",
    "CH4.CHILD.1",
    "CH4.CHILD.2",
    "CH4.CHILD.3",
    "CH4.SDF.1",
    "CH4.SDF.2",
    "CH4.SDF.3",
    "CH4.SDF.4",
}


@pytest.fixture(scope="module", autouse=True)
def _register_frameworks():
    from app.main import _register_frameworks as register

    register()


@pytest.fixture(autouse=True)
def upload_root(tmp_path, monkeypatch):
    root = tmp_path / "uploads"
    root.mkdir()
    monkeypatch.setattr(settings, "upload_dir", str(root))
    return root


def _alembic_config(db_path: Path) -> Config:
    config = Config(str(REPO_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return config


@pytest.fixture()
def db_path(tmp_path):
    path = tmp_path / "correctness-bundle.sqlite3"
    command.upgrade(_alembic_config(path), "head")
    return path


@pytest.fixture()
def engine(db_path):
    eng = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})

    @event.listens_for(eng, "connect")
    def _enable_foreign_keys(dbapi_connection, _record):  # pragma: no cover
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    yield eng
    eng.dispose()


@pytest.fixture()
def db(engine):
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def http(db, db_path, monkeypatch):
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{db_path}")

    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


def _core_ids() -> list[str]:
    return [
        question["id"]
        for question in build_questionnaire()
        if not question["id"].startswith(("IND.", "FU."))
    ]


def _seed(db, *, frameworks=("dpdpa",), applicable=None, client_name="Acme Corp"):
    client = Client(name=client_name, industry="Technology", size="medium")
    db.add(client)
    db.flush()
    engagement = Engagement(client_id=client.id, name=f"{client_name} engagement", status="active")
    db.add(engagement)
    db.flush()
    assessment = Assessment(
        company_name=client_name,
        industry="Technology",
        company_size="medium",
        selected_frameworks=json.dumps(list(frameworks)),
        engagement_id=engagement.id,
        applicable_requirements=json.dumps(applicable) if applicable is not None else None,
    )
    db.add(assessment)
    db.commit()
    return assessment


def _add_response(db, assessment, question_id, *, source="human", answer="fully_implemented"):
    row = QuestionnaireResponse(
        assessment_id=assessment.id,
        question_id=question_id,
        answer=answer,
        answer_source=source,
    )
    db.add(row)
    db.flush()
    if source is None:
        row.answer_source = None
    return row


def _answer_ids(db, assessment, question_ids, *, source="human"):
    for question_id in question_ids:
        _add_response(db, assessment, question_id, source=source)
    db.commit()


def _item(requirement_id, status="compliant"):
    return {
        "requirement_id": requirement_id,
        "compliance_status": status,
        "current_state": f"State of {requirement_id}",
        "gap_description": f"Gap in {requirement_id}",
        "risk_level": "high" if status != "compliant" else "low",
        "remediation_action": f"Fix {requirement_id}",
        "remediation_priority": 2,
        "remediation_effort": "medium",
        "timeline_weeks": 6,
        "maturity_level": 2,
        "root_cause_category": "process",
        "evidence_quote": "Synthetic evidence",
        "needs_review": False,
    }


def _stub_single(monkeypatch, *, captured=None, requirement_id=None, status="compliant"):
    requirement_id = requirement_id or _core_ids()[0]

    def _fake(**kwargs):
        if captured is not None:
            captured.append(kwargs)
        return {
            "parsed": {
                "executive_summary": "Synthetic summary",
                "assessments": [_item(requirement_id, status)],
            },
            "raw": "{}",
        }

    monkeypatch.setattr(analysis, "run_gap_analysis", _fake)
    monkeypatch.setattr(analysis, "generate_initiatives", lambda *_args: [])


def _stub_multi(monkeypatch, *, failed=(), captured=None, status="compliant"):
    failed = set(failed)

    def _fake(**kwargs):
        if captured is not None:
            captured.append(kwargs)
        frameworks = {}
        for framework_id in kwargs["framework_ids"]:
            if framework_id in failed:
                frameworks[framework_id] = {
                    "parsed": {"executive_summary": "failed", "assessments": []},
                    "raw": "boom",
                    "error": "boom",
                }
                continue
            control_id = FrameworkRegistry.get(framework_id).all_controls()[0].id
            frameworks[framework_id] = {
                "parsed": {
                    "executive_summary": f"{framework_id} summary",
                    "assessments": [_item(control_id, status)],
                },
                "raw": "{}",
            }
        return {"frameworks": frameworks, "synthesis": None, "total_usage": {}}

    monkeypatch.setattr(analysis, "run_multi_framework_analysis", _fake)
    monkeypatch.setattr(analysis, "generate_multi_framework_initiatives", lambda *_args: [])


def _add_document(db, assessment, monkeypatch):
    monkeypatch.setattr(evidence_service, "extract_text", lambda *_args: "A synthetic policy document.")
    return evidence_service.ingest_upload(
        db,
        assessment_id=assessment.id,
        filename="policy.pdf",
        content=b"%PDF-1.4 synthetic policy",
        category="privacy_policy",
    )


def _multi_cluster_id():
    from app.frameworks.questionnaire_builder import build_multi_questionnaire

    return build_multi_questionnaire(["dpdpa", "iso27001"])[0]["cluster_id"]


def _make_report(db, assessment, scores):
    report = GapReport(
        assessment_id=assessment.id,
        overall_score=0.0,
        chapter_scores=json.dumps({}),
        framework_scores=json.dumps(scores),
        executive_summary="Synthetic report",
        raw_ai_response="{}",
    )
    db.add(report)
    db.commit()
    return report


def test_scope_aware_gate_and_invalid_scope_inputs(db, monkeypatch, caplog):
    """Scenario 1: the DPDPA gate counts only in-scope core questions."""
    from app.routers.analysis import CompletionGateRefused

    all_ids = _core_ids()
    assert len(all_ids) == 41
    applicable = [question_id for question_id in all_ids if question_id not in EXCLUDED_SCOPE_IDS]
    assert len(applicable) == 30

    assessment = _seed(db, applicable=applicable)
    _answer_ids(db, assessment, applicable[:24])
    _stub_single(monkeypatch)
    result = analysis.trigger_analysis(assessment.id, db=db)
    assert result["status"] == "completed"
    assert not db.query(AuditEvent).filter(AuditEvent.action == "analysis.completion_override").count()

    refused = _seed(db, applicable=applicable, client_name="Scope Refused")
    _answer_ids(db, refused, applicable[:23])
    with pytest.raises(CompletionGateRefused) as exc:
        analysis.trigger_analysis(refused.id, db=db)
    assert exc.value.status_code == 400
    assert exc.value.detail == analysis.COMPLETION_GATE_MESSAGE.format(answered=23, expected=30, pct=77)
    assert db.query(AnalysisRun).filter(AnalysisRun.assessment_id == refused.id).count() == 0
    assert db.get(Assessment, refused.id).status == "created"

    out_of_scope = _seed(db, applicable=applicable, client_name="Out of Scope")
    _answer_ids(db, out_of_scope, applicable[:23] + list(EXCLUDED_SCOPE_IDS)[:5])
    with pytest.raises(CompletionGateRefused) as exc:
        analysis.trigger_analysis(out_of_scope.id, db=db)
    assert "23 of 30" in exc.value.detail

    for raw, name in ((None, "No Scope"), ("not-json", "Bad Scope")):
        scoped = _seed(db, client_name=name)
        _answer_ids(db, scoped, all_ids[:32])
        if raw is not None:
            scoped.applicable_requirements = raw
            db.commit()
        with pytest.raises(CompletionGateRefused) as exc:
            analysis.trigger_analysis(scoped.id, db=db)
        assert "32 of 41" in exc.value.detail
    assert "Invalid applicable_requirements for assessment gate" in caplog.text

    empty_scope = _seed(db, applicable=[], client_name="Empty Scope")
    with pytest.raises(HTTPException) as exc:
        analysis.trigger_analysis(empty_scope.id, db=db)
    assert exc.value.detail == "Submit questionnaire responses or upload documents before running analysis."


def test_explicit_completion_override_replaces_document_bypass(db, monkeypatch, http):
    """Scenario 2: incomplete analysis requires a coded, attributed audit override."""
    assessment = _seed(db, client_name="Documents")
    _add_document(db, assessment, monkeypatch)
    _stub_single(monkeypatch)

    with pytest.raises(analysis.CompletionGateRefused):
        analysis.trigger_analysis(assessment.id, db=db)
    assert db.get(Assessment, assessment.id).status == "documents_uploaded"

    result = analysis.trigger_analysis(
        assessment.id,
        db=db,
        override=analysis.CompletionOverride(reason="document_led", reviewer_name="Priya"),
    )
    assert result["status"] == "completed"
    event = (
        db.query(AuditEvent)
        .filter(AuditEvent.action == analysis.COMPLETION_OVERRIDE_EVENT)
        .one()
    )
    assert event.actor == "consultant:Priya"
    assert event.entity_type == "assessment"
    assert event.entity_id == assessment.id
    assert json.loads(event.metadata_json) == {
        "answered": 0,
        "completion_pct": 0,
        "expected": 41,
        "framework_ids": ["dpdpa"],
        "reason": "document_led",
        "schema_version": 1,
        "threshold_pct": 80,
    }

    invalid = _seed(db, client_name="Invalid Override")
    _add_document(db, invalid, monkeypatch)
    with pytest.raises(HTTPException) as exc:
        analysis.trigger_analysis(
            invalid.id,
            db=db,
            override=analysis.CompletionOverride(reason="unknown", reviewer_name="Priya"),
        )
    assert exc.value.detail == "Choose a valid override reason."
    assert not db.query(AuditEvent).filter(AuditEvent.entity_id == invalid.id).count()

    no_inputs = _seed(db, client_name="No Inputs")
    with pytest.raises(HTTPException) as exc:
        analysis.trigger_analysis(
            no_inputs.id,
            db=db,
            override=analysis.CompletionOverride(reason="document_led", reviewer_name="Priya"),
        )
    assert exc.value.detail == "Submit questionnaire responses or upload documents before running analysis."
    assert not db.query(AuditEvent).filter(AuditEvent.entity_id == no_inputs.id).count()

    complete = _seed(db, client_name="Complete")
    _answer_ids(db, complete, _core_ids()[:33])
    result = analysis.trigger_analysis(
        complete.id,
        db=db,
        override=analysis.CompletionOverride(reason="document_led", reviewer_name="Ignored"),
    )
    assert result["status"] == "completed"
    assert not db.query(AuditEvent).filter(AuditEvent.entity_id == complete.id).count()

    api_assessment = _seed(db, client_name="API Override")
    _add_document(db, api_assessment, monkeypatch)
    response = http.post(
        f"/api/assessments/{api_assessment.id}/analyze",
        json={"reason": "document_led"},
    )
    assert response.status_code == 200
    api_event = (
        db.query(AuditEvent)
        .filter(
            AuditEvent.entity_id == api_assessment.id,
            AuditEvent.action == analysis.COMPLETION_OVERRIDE_EVENT,
        )
        .one()
    )
    assert api_event.actor == "consultant:Manager Review"

    no_body = _seed(db, client_name="API No Body")
    response = http.post(f"/api/assessments/{no_body.id}/analyze")
    assert response.status_code == 400


def test_unconfirmed_answers_are_excluded_from_gates_analyzers_and_envelopes(db, monkeypatch):
    """Scenario 3: document and inferred answers are never silent analysis inputs."""
    from app.services.analysis_pipeline import _envelope
    from app.services.auto_answer import UNCONFIRMED_ANSWER_SOURCES, confirmed_response_clause

    assert UNCONFIRMED_ANSWER_SOURCES == ("document", "inferred")
    assert str(confirmed_response_clause())

    document_only = _seed(db, client_name="Document Only")
    _answer_ids(db, document_only, _core_ids()[:33], source="document")
    with pytest.raises(analysis.CompletionGateRefused) as exc:
        analysis.trigger_analysis(document_only.id, db=db)
    assert "0 of 41" in exc.value.detail

    mixed = _seed(db, client_name="Mixed Sources")
    _answer_ids(db, mixed, _core_ids()[:30])
    _answer_ids(db, mixed, _core_ids()[30:33], source="document")
    with pytest.raises(analysis.CompletionGateRefused) as exc:
        analysis.trigger_analysis(mixed.id, db=db)
    assert "30 of 41" in exc.value.detail

    for row in db.query(QuestionnaireResponse).filter(QuestionnaireResponse.assessment_id == mixed.id).all():
        if row.answer_source == "document":
            row.answer_source = "document_confirmed"
    db.commit()
    _stub_single(monkeypatch)
    assert analysis.trigger_analysis(mixed.id, db=db)["status"] == "completed"

    inferred = _seed(db, client_name="Inferred")
    _answer_ids(db, inferred, _core_ids()[:33], source="inferred")
    with pytest.raises(analysis.CompletionGateRefused) as exc:
        analysis.trigger_analysis(inferred.id, db=db)
    assert "0 of 41" in exc.value.detail

    legacy_null = _seed(db, client_name="Legacy Null")
    _answer_ids(db, legacy_null, _core_ids()[:33], source=None)
    _stub_single(monkeypatch)
    assert analysis.trigger_analysis(legacy_null.id, db=db)["status"] == "completed"

    captured_single = []
    captured_assessment = _seed(db, client_name="Captured Single")
    _answer_ids(db, captured_assessment, _core_ids()[:33])
    _add_response(db, captured_assessment, "UNCONFIRMED.TEST", source="document")
    db.commit()
    _stub_single(monkeypatch, captured=captured_single)
    analysis.trigger_analysis(captured_assessment.id, db=db)
    assert all(row["question_id"] != "UNCONFIRMED.TEST" for row in captured_single[0]["responses"])

    captured_multi = _seed(
        db,
        frameworks=("dpdpa", "iso27001"),
        client_name="Captured Multi",
    )
    cluster_id = _multi_cluster_id()
    _add_response(db, captured_multi, cluster_id, source="human")
    _add_response(db, captured_multi, "CH4.SDF.4", source="document")
    db.commit()
    captured_multi_kwargs = []
    _stub_multi(monkeypatch, captured=captured_multi_kwargs)
    analysis.trigger_analysis(
        captured_multi.id,
        db=db,
        override=analysis.CompletionOverride(reason="client_answers_pending", reviewer_name="Priya"),
    )
    assert all(row["question_id"] != "CH4.SDF.4" for row in captured_multi_kwargs[0]["responses"])

    runs = db.query(AnalysisRun).filter(AnalysisRun.assessment_id == captured_multi.id).all()
    assert all(json.loads(run.claims_json)["inputs"]["questionnaire_response_count"] == 1 for run in runs)
    assessment = db.get(Assessment, captured_multi.id)
    assert _envelope(
        trigger_id="test",
        framework_id="dpdpa",
        assessment_id=assessment.id,
        db=db,
        sources=(),
    )["inputs"]["questionnaire_response_count"] == 1


def test_web_gate_panel_override_and_no_input_state(db, engine, monkeypatch, http):
    """Scenario 4: the web route renders the gate and audited override form."""
    import app.database as database

    monkeypatch.setattr(database, "SessionLocal", sessionmaker(bind=engine))
    blocked = _seed(db, client_name="Web Blocked")
    response = http.post(f"/assessments/{blocked.id}/run-analysis")
    assert response.status_code == 200
    assert "data-completion-gate-blocked" in response.text
    assert analysis.COMPLETION_GATE_MESSAGE.format(answered=0, expected=41, pct=0) in response.text
    assert "data-completion-override-form" in response.text
    assert [
        f'value="{code}"' for code in analysis.COMPLETION_OVERRIDE_REASONS
    ] == [
        f'value="{code}"' for code in analysis.COMPLETION_OVERRIDE_REASONS if f'value="{code}"' in response.text
    ]
    assert response.headers["X-Toast-Type"] == "error"
    assert db.get(Assessment, blocked.id).status == "created"

    overridden = _seed(db, client_name="Web Override")
    _add_document(db, overridden, monkeypatch)
    _stub_single(monkeypatch)
    response = http.post(
        f"/assessments/{overridden.id}/run-analysis",
        data={"override_reason": "document_led", "reviewer_name": "Priya"},
    )
    assert response.status_code == 200
    assert db.query(AuditEvent).filter(
        AuditEvent.entity_id == overridden.id,
        AuditEvent.action == analysis.COMPLETION_OVERRIDE_EVENT,
    ).count() == 1

    no_input = _seed(db, applicable=[], client_name="Web No Input")
    response = http.post(f"/assessments/{no_input.id}/run-analysis")
    assert response.status_code == 200
    assert "data-completion-gate-blocked" in response.text
    assert "data-completion-override-form" not in response.text
    assert db.get(Assessment, no_input.id).status == "created"


def test_partial_framework_failure_is_stored_and_rendered_fail_closed(db, monkeypatch, http):
    """Scenario 5: a failed framework has no score and keeps the assessment incomplete."""
    assessment = _seed(db, frameworks=("dpdpa", "iso27001"), client_name="Partial Failure")
    _add_response(db, assessment, _multi_cluster_id())
    db.commit()
    _stub_multi(monkeypatch, failed=("iso27001",))
    result = analysis.trigger_analysis(
        assessment.id,
        db=db,
        override=analysis.CompletionOverride(reason="client_answers_pending", reviewer_name="Priya"),
    )
    assert result["status"] == "incomplete"
    assert result["failed_frameworks"] == ["iso27001"]
    assert result["per_framework_scores"]["iso27001"] is None
    assert "ISO" in result["message"]

    db.expire_all()
    report = db.query(GapReport).filter(GapReport.assessment_id == assessment.id).one()
    scores = json.loads(report.framework_scores)
    assert scores["iso27001"] == failed_framework_scores()
    assert "status" not in scores["dpdpa"]
    assert isinstance(scores["dpdpa"]["overall_score"], (int, float))
    assert not any(key.startswith("iso27001:") for key in json.loads(report.chapter_scores))
    assert db.get(Assessment, assessment.id).status == "error"

    summary = http.get(f"/assessments/{assessment.id}/report-summary")
    assert summary.status_code == 200
    assert "data-analysis-incomplete-banner" in summary.text
    assert 'data-framework-failed="iso27001"' in summary.text
    card = summary.text.split('data-framework-failed="iso27001"', 1)[1].split("</div>", 1)[0]
    assert "0%" not in card

    status = http.get(f"/assessments/{assessment.id}/analysis-status")
    assert status.status_code == 200
    assert "data-analysis-failed-frameworks" in status.text
    assert FrameworkRegistry.get("iso27001").name in status.text


def test_all_framework_failure_preserves_previous_report_and_marks_runs_failed(db, monkeypatch):
    """Scenario 6: all failed frameworks persist no replacement report."""
    assessment = _seed(db, frameworks=("dpdpa", "iso27001"), client_name="All Failed")
    _add_response(db, assessment, _multi_cluster_id())
    db.commit()
    _stub_multi(monkeypatch)
    analysis.trigger_analysis(
        assessment.id,
        db=db,
        override=analysis.CompletionOverride(reason="client_answers_pending", reviewer_name="Priya"),
    )
    db.expire_all()
    old_report = db.query(GapReport).filter(GapReport.assessment_id == assessment.id).one()
    old_report_id = old_report.id
    old_scores = old_report.framework_scores
    old_items = [(item.requirement_id, item.compliance_status) for item in db.query(GapItem).filter(GapItem.report_id == old_report.id)]

    _stub_multi(monkeypatch, failed=("dpdpa", "iso27001"))
    with pytest.raises(HTTPException) as exc:
        analysis.trigger_analysis(
            assessment.id,
            db=db,
            override=analysis.CompletionOverride(reason="client_answers_pending", reviewer_name="Priya"),
        )
    assert exc.value.status_code == 500
    assert exc.value.detail == "Analysis failed for every selected framework. Run analysis again."
    db.expire_all()
    current = db.query(GapReport).filter(GapReport.assessment_id == assessment.id).one()
    assert (current.id, current.framework_scores) == (old_report_id, old_scores)
    assert [(item.requirement_id, item.compliance_status) for item in db.query(GapItem).filter(GapItem.report_id == current.id)] == old_items
    assert db.get(Assessment, assessment.id).status == "error"
    assert all(
        run.status == "failed"
        for run in db.query(AnalysisRun).filter(AnalysisRun.assessment_id == assessment.id).order_by(AnalysisRun.started_at).all()[-2:]
    )


def test_failed_framework_blocks_release_but_draft_pdf_and_integrated_report_explain_it(
    db, monkeypatch, http, upload_root
):
    """Scenario 7: every release path refuses a failed framework while draft PDF output remains explicit."""
    assessment = _seed(db, frameworks=("dpdpa", "iso27001"), client_name="Release Blocked")
    _add_response(db, assessment, _multi_cluster_id())
    db.commit()
    _stub_multi(monkeypatch, failed=("iso27001",))
    analysis.trigger_analysis(
        assessment.id,
        db=db,
        override=analysis.CompletionOverride(reason="client_answers_pending", reviewer_name="Priya"),
    )
    db.expire_all()
    assessment = db.get(Assessment, assessment.id)
    assessment.review_status = "approved"
    db.add(
        RFIDocument(
            assessment_id=assessment.id,
            title="Synthetic RFI",
            introduction="Please respond.",
            evidence_items="[]",
            response_instructions="Respond.",
            appendix="",
            total_items=0,
            critical_items=0,
        )
    )
    db.commit()

    release_detail = (
        f"Analysis failed for {FrameworkRegistry.get('iso27001').name}. "
        "Run analysis again before releasing this report."
    )
    for path in (
        f"/api/assessments/{assessment.id}/report",
        f"/api/assessments/{assessment.id}/report/summary",
        f"/api/assessments/{assessment.id}/report/full",
        f"/api/assessments/{assessment.id}/report/pdf",
        f"/assessments/{assessment.id}/rfi/pdf",
    ):
        response = http.get(path)
        assert response.status_code == 409
        assert response.json()["detail"] == release_detail

    draft = http.post(
        f"/api/assessments/{assessment.id}/snapshots",
        data={"type": "gap_report", "reviewer_name": "Priya"},
    )
    assert draft.status_code == 200
    snapshot_id = draft.json()["snapshot_id"]
    issued = http.post(
        f"/api/assessments/{assessment.id}/snapshots/{snapshot_id}/issue",
        data={"reviewer_name": "Priya"},
    )
    assert issued.status_code == 409
    assert issued.json()["detail"] == release_detail
    snapshot_path = upload_root / db.get(ReportSnapshot, snapshot_id).storage_path
    with pdfplumber.open(snapshot_path) as pdf:
        pdf_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    assert "analysis failed" in pdf_text.lower()
    assert "Incomplete:" in pdf_text

    integrated = report_content.integrated_report(db, db.get(Engagement, assessment.engagement_id))
    assert any(item.reason == report_content.ANALYSIS_INCOMPLETE for item in integrated.excluded)

    failed_schema = FrameworkScoreOut(**failed_framework_scores())
    assert failed_schema.status == "failed"
    normal_schema = FrameworkScoreOut(
        overall_score=80.0,
        overall_rating="Compliant",
        domain_scores={},
    )
    assert normal_schema.status == "scored"

    _stub_multi(monkeypatch)
    analysis.trigger_analysis(
        assessment.id,
        db=db,
        override=analysis.CompletionOverride(reason="client_answers_pending", reviewer_name="Priya"),
    )
    db.expire_all()
    assert http.get(f"/api/assessments/{assessment.id}/report/summary").status_code == 200


def test_requirement_counts_are_registry_driven(db, http):
    """Scenario 8: report summary counts the selected frameworks' controls."""
    expected = {
        "iso27001": 93,
        "nist_csf": 94,
        "dpdpa": 41,
        "dpdpa_iso": 134,
    }
    cases = [
        (("iso27001",), expected["iso27001"]),
        (("nist_csf",), expected["nist_csf"]),
        (("dpdpa",), expected["dpdpa"]),
        (("dpdpa", "iso27001"), expected["dpdpa_iso"]),
    ]
    for index, (frameworks, total) in enumerate(cases):
        assessment = _seed(db, frameworks=frameworks, client_name=f"Counts {index}")
        scores = {
            framework_id: {
                "overall_score": 80.0,
                "overall_rating": "Compliant",
                "domain_scores": {},
            }
            for framework_id in frameworks
        }
        _make_report(db, assessment, scores)
        assessment.review_status = "approved"
        db.commit()
        response = http.get(f"/api/assessments/{assessment.id}/report/summary")
        assert response.status_code == 200
        payload = response.json()
        assert payload["requirement_counts"] == {
            framework_id: FrameworkRegistry.get(framework_id).control_count()
            for framework_id in frameworks
        }
        assert payload["total_requirements"] == total
    source = (REPO_ROOT / "app/routers/reports.py").read_text()
    assert "ROOT_CAUSE_CLUSTERS" not in source
    assert "app.dpdpa" not in source


def test_penalty_exposure_is_dpdpa_only_and_claim_is_removed(db, http):
    """Scenario 9: non-DPDPA gaps never acquire DPDPA rupee exposure."""
    from app.routers.web import _compute_business_impact

    iso_gap = SimpleNamespace(
        framework_id="iso27001", requirement_id="A.5.1", compliance_status="non_compliant", risk_level="high"
    )
    dpdpa_gap = SimpleNamespace(
        framework_id="dpdpa", requirement_id="CH2.SECURITY.1", compliance_status="non_compliant", risk_level="high"
    )
    unknown_dpdpa_gap = SimpleNamespace(
        framework_id="dpdpa", requirement_id="OTHER.1", compliance_status="non_compliant", risk_level="medium"
    )
    legacy_gap = SimpleNamespace(
        framework_id=None, requirement_id="CH2.SECURITY.1", compliance_status="non_compliant", risk_level="medium"
    )
    clean = SimpleNamespace(
        framework_id="dpdpa", requirement_id="CH2.SECURITY.1", compliance_status="compliant", risk_level="low"
    )

    assert _compute_business_impact([iso_gap]) == {
        "max_penalty_cr": 0,
        "affected_domains": [],
        "critical_high_count": 1,
        "has_gaps": True,
        "has_dpdpa_exposure": False,
    }
    assert _compute_business_impact([dpdpa_gap])["max_penalty_cr"] == 250
    assert _compute_business_impact([dpdpa_gap])["has_dpdpa_exposure"] is True
    assert _compute_business_impact([unknown_dpdpa_gap])["max_penalty_cr"] == 50
    assert _compute_business_impact([legacy_gap])["max_penalty_cr"] == 250
    assert _compute_business_impact([clean])["has_gaps"] is False

    for index, item in enumerate((iso_gap, dpdpa_gap)):
        assessment = _seed(
            db,
            frameworks=("dpdpa", "iso27001"),
            client_name=f"Penalty {index}",
        )
        scores = {
            framework_id: {
                "overall_score": 80.0,
                "overall_rating": "Compliant",
                "domain_scores": {},
            }
            for framework_id in assessment.frameworks
        }
        report = _make_report(db, assessment, scores)
        db.add(
            GapItem(
                report_id=report.id,
                requirement_id=item.requirement_id,
                framework_id=item.framework_id,
                chapter="Test",
                requirement_title=item.requirement_id,
                compliance_status=item.compliance_status,
                current_state="state",
                gap_description="gap",
                risk_level=item.risk_level,
                remediation_action="fix",
                remediation_priority=2,
                remediation_effort="medium",
                timeline_weeks=4,
            )
        )
        db.commit()
        rendered = http.get(f"/assessments/{assessment.id}/report-summary")
        assert rendered.status_code == 200
        if index == 0:
            assert "₹" not in rendered.text
        else:
            assert "₹250" in rendered.text

    template_source = (REPO_ROOT / "app/templates/partials/report_summary.html").read_text()
    assert "₹500" not in template_source
    assert "Repeat violations" not in template_source


def test_p5_1_structural_guards_and_signatures():
    """Scenario 10: the fixed contract preserves all standing source guards."""
    analysis_source = (REPO_ROOT / "app/routers/analysis.py").read_text()
    assert analysis_source.count("overall_score=0.0") == 2
    for line in analysis_source.splitlines():
        if "overall_score" in line:
            assert "overall_score=0.0" in line or 'per_fw_scores.items()' in line

    for relative in (
        "app/services/scoring.py",
        "app/routers/reports.py",
        "app/utils/pdf_export.py",
        "app/routers/review.py",
    ):
        source = (REPO_ROOT / relative).read_text()
        assert not any(token in source for token in ("Conclusion", "AnalysisRun", "analysis_pipeline"))
    pipeline_source = (REPO_ROOT / "app/services/analysis_pipeline.py").read_text()
    assert "delete" not in pipeline_source
    content_source = (REPO_ROOT / "app/services/report_content.py").read_text()
    assert not any(token in content_source for token in ("db.add(", "db.add_all(", "db.merge(", ".flush(", ".commit(", "delete"))

    for template in (REPO_ROOT / "app/templates").rglob("*.html"):
        source = template.read_text()
        assert "overall_score" not in source
        assert "CyberAssess" not in source
        assert "|safe" not in source
    report_summary = (REPO_ROOT / "app/templates/partials/report_summary.html").read_text()
    assert '/snapshots"' in report_summary
    assert "Live PDF" in report_summary
    assert "Download PDF" not in report_summary
    assert "PDF Report" not in report_summary

    gate_partial = (REPO_ROOT / "app/templates/partials/analysis_gate_blocked.html").read_text()
    assert "data-completion-gate-blocked" in gate_partial
    assert "data-completion-override-form" in gate_partial
    assert "'" not in gate_partial

    assert subprocess.run(
        ["alembic", "heads"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip() == "8b2d5f7e1c34 (head)"
    parameter_names = list(inspect.signature(analysis._run_multi_framework_analysis).parameters)
    assert parameter_names == [
        "assessment",
        "assessment_id",
        "responses",
        "documents",
        "context_profile",
        "desk_review_data",
        "applicable_requirements",
        "selected_frameworks",
        "has_documents",
        "db",
    ]
