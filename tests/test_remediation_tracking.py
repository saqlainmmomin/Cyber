"""Contract suite for P3-4 remediation tracking and engagement rollups."""

from __future__ import annotations

import copy
import inspect
import json
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from fpdf import FPDF
from sqlalchemy import create_engine, event, insert, select, text
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.config import settings
from app.database import get_db
from app.dpdpa.framework import get_all_requirements
from app.main import app
from app.models.action import Action
from app.models.assessment import Assessment
from app.models.audit_event import AuditEvent
from app.models.client import Client
from app.models.conclusion import Conclusion, ConclusionRevision
from app.models.engagement import Engagement
from app.models.evidence import Evidence, EvidenceUse, EvidenceVersion
from app.models.finding import Finding
from app.models.questionnaire import QuestionnaireResponse
from app.models.report import GapItem, GapReport
from app.routers import web
from app.services import evidence as evidence_service
from app.services import findings, remediation_rollup, workpaper
from scripts.migrate_legacy import run_migration

REPO_ROOT = Path(__file__).resolve().parents[1]
REQS = [row["id"] for row in get_all_requirements()][:3]


@pytest.fixture(scope="module", autouse=True)
def _register_frameworks():
    from app.main import _register_frameworks as register

    register()


def _alembic_config(db_path: Path) -> Config:
    config = Config(str(REPO_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return config


@pytest.fixture()
def db_path(tmp_path):
    path = tmp_path / "remediation.sqlite3"
    command.upgrade(_alembic_config(path), "head")
    return path


@pytest.fixture()
def engine(db_path):
    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _record):  # pragma: no cover
        cursor = dbapi_connection.cursor()
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
    from app.routers.web import templates
    from app.template_config import configure_templates

    configure_templates(templates)
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{db_path}")

    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def upload_root(tmp_path, monkeypatch) -> Path:
    root = tmp_path / "uploads"
    root.mkdir()
    monkeypatch.setattr(settings, "upload_dir", str(root))
    return root


@pytest.fixture()
def gate(monkeypatch):
    from app.frameworks import questionnaire_builder
    from app.routers import analysis

    monkeypatch.setattr(analysis, "build_questionnaire", lambda **_kwargs: [{"id": "Q1"}])
    monkeypatch.setattr(analysis, "generate_initiatives", lambda *_args: [])
    monkeypatch.setattr(analysis, "generate_multi_framework_initiatives", lambda *_args: [])
    monkeypatch.setattr(questionnaire_builder, "build_multi_questionnaire", lambda *_a, **_k: [])
    return analysis


def _seed(db, *, applicable=None, client_name="Acme Corp", engagement=None):
    if engagement is None:
        client = Client(name=client_name, industry="Technology", size="medium")
        db.add(client)
        db.flush()
        engagement = Engagement(client_id=client.id, name=f"{client_name} gap", status="active")
        db.add(engagement)
        db.flush()
    assessment = Assessment(
        company_name=client_name,
        industry="Technology",
        company_size="medium",
        selected_frameworks=json.dumps(["dpdpa"]),
        engagement_id=engagement.id,
        applicable_requirements=json.dumps(applicable or [REQS[0]]),
    )
    db.add(assessment)
    db.flush()
    db.add(
        QuestionnaireResponse(
            assessment_id=assessment.id,
            question_id="Q1",
            answer="fully_implemented",
        )
    )
    db.commit()
    return assessment


def _item(
    requirement_id,
    status="partially_compliant",
    *,
    current="Current state",
    gap="Gap exists",
    risk="medium",
    action="Fix the gap",
    quote="",
):
    return {
        "requirement_id": requirement_id,
        "compliance_status": status,
        "current_state": current,
        "gap_description": gap,
        "risk_level": risk,
        "remediation_action": action,
        "remediation_priority": 2,
        "remediation_effort": "medium",
        "timeline_weeks": 6,
        "maturity_level": 2,
        "root_cause_category": "process",
        "evidence_quote": quote,
        "needs_review": False,
    }


def _stub_single(monkeypatch, items):
    from app.routers import analysis

    monkeypatch.setattr(
        analysis,
        "run_gap_analysis",
        lambda **_kwargs: {
            "parsed": {
                "executive_summary": "Synthetic summary",
                "assessments": copy.deepcopy(items),
            },
            "raw": "{}",
        },
    )


def _run_one(db, gate, monkeypatch, *, item=None, client_name="Acme Corp", engagement=None):
    assessment = _seed(db, client_name=client_name, engagement=engagement)
    _stub_single(monkeypatch, [item or _item(REQS[0], "non_compliant")])
    gate.trigger_analysis(assessment.id, db)
    conclusion = db.query(Conclusion).filter_by(assessment_id=assessment.id).one()
    return assessment, conclusion


def _approve(http, db, assessment, conclusion):
    response = http.post(
        f"/api/assessments/{assessment.id}/conclusions/{conclusion.id}/approve",
        data={"expected_version": conclusion.version, "reviewer_name": "Priya"},
    )
    assert response.status_code == 200
    db.refresh(conclusion)


def _create(http, assessment, conclusion, **overrides):
    payload = {
        "conclusion_id": conclusion.id,
        "conclusion_version": conclusion.version,
        "title": "Finding title",
        "description": "Finding description",
        "severity": "high",
        "priority": 1,
        "action_title": "First action",
        "reviewer_name": "Priya",
    }
    payload.update(overrides)
    return http.post(f"/api/assessments/{assessment.id}/findings", data=payload)


def _created_finding(db, http, gate, monkeypatch, *, client_name="Acme Corp", engagement=None, item=None):
    assessment, conclusion = _run_one(
        db,
        gate,
        monkeypatch,
        item=item or _item(REQS[0], "non_compliant"),
        client_name=client_name,
        engagement=engagement,
    )
    _approve(http, db, assessment, conclusion)
    response = _create(http, assessment, conclusion)
    assert response.status_code == 200
    finding = db.get(Finding, response.json()["finding_id"])
    action = db.query(Action).filter_by(finding_id=finding.id).one()
    return assessment, conclusion, finding, action


def _history(db, action_id):
    db.expire_all()
    return json.loads(db.get(Action, action_id).history_json)


def _nothing_snapshot(db):
    counts = {
        table: db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one()
        for table in ("findings", "actions", "audit_events", "conclusion_revisions")
    }
    actions = db.execute(
        text(
            "SELECT id, status, title, owner, target_date, history_json, updated_at "
            "FROM actions ORDER BY id"
        )
    ).all()
    conclusions = db.execute(
        text("SELECT id, version, updated_at FROM conclusions ORDER BY id")
    ).all()
    finding_statuses = db.execute(
        text("SELECT id, status FROM findings ORDER BY id")
    ).all()
    return counts, actions, conclusions, finding_statuses


def _closure_pdf(text_value: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(0, 10, text_value)
    return bytes(pdf.output())


def _closure_evidence(db, assessment, *, name="closure.pdf", text_value="Signed closure memo"):
    if not name.endswith((".pdf", ".docx", ".png", ".jpg", ".jpeg", ".webp")):
        name = f"{name.rsplit('.', 1)[0]}.pdf"
    result = evidence_service.ingest_upload(
        db,
        assessment_id=assessment.id,
        filename=name,
        content=_closure_pdf(text_value),
        category=None,
    )
    return result.evidence, result.version


def _post(http, db, assessment, finding, action, step, **data):
    data.setdefault("reviewer_name", "Priya")
    if "expected_history_length" not in data:
        data["expected_history_length"] = len(_history(db, action.id))
    return http.post(
        f"/api/assessments/{assessment.id}/findings/{finding.id}/actions/{action.id}/{step}",
        data=data,
    )


def _gap_item_kwargs(**overrides):
    defaults = {
        "requirement_id": REQS[0],
        "framework_id": "dpdpa",
        "cluster_id": None,
        "control_reference": "S.5(1)",
        "chapter": "Chapter II",
        "requirement_title": "Legacy requirement",
        "compliance_status": "non_compliant",
        "current_state": "Legacy state",
        "gap_description": "Legacy gap",
        "risk_level": "high",
        "remediation_action": "Legacy action",
        "remediation_priority": 1,
        "remediation_effort": "medium",
        "timeline_weeks": 6,
        "maturity_level": 2,
        "root_cause_category": "policy",
        "evidence_quote": "Legacy evidence",
        "evidence_confidence": "moderate",
        "remediation_status": "open",
        "remediation_owner": None,
        "remediation_target_date": None,
        "remediation_notes": None,
        "remediation_closed_at": None,
        "review_status": "draft",
        "needs_review": False,
        "ai_compliance_status": "non_compliant",
        "ai_gap_description": "AI legacy gap",
        "ai_risk_level": "high",
        "reviewer_notes": None,
        "reviewed_by": None,
        "reviewed_at": None,
    }
    defaults.update(overrides)
    return defaults


def _seed_legacy_assessment(db, *, company_name, gap_items):
    assessment = Assessment(
        company_name=company_name,
        industry="Technology",
        company_size="medium",
        status="completed",
        selected_frameworks=json.dumps(["dpdpa"]),
    )
    db.add(assessment)
    db.flush()
    report = GapReport(
        assessment_id=assessment.id,
        overall_score=50.0,
        chapter_scores=json.dumps({}),
        executive_summary="Legacy summary",
        raw_ai_response=json.dumps({}),
        framework_scores=json.dumps({"dpdpa": {"score": 50.0}}),
        legacy_history=json.dumps([]),
    )
    db.add(report)
    db.flush()
    for values in gap_items:
        db.execute(insert(GapItem).values(report_id=report.id, **values))
    db.commit()
    return assessment


def _close_and_verify(db, http, assessment, finding, action, *, text_value):
    evidence, version = _closure_evidence(
        db,
        assessment,
        name=f"{action.id}.txt",
        text_value=text_value,
    )
    assert _post(
        http,
        db,
        assessment,
        finding,
        action,
        "close",
        evidence_version_id=version.id,
    ).status_code == 200
    assert _post(http, db, assessment, finding, action, "verify").status_code == 200
    return evidence, version


def test_scenario_1_full_lifecycle_and_closure_history(db, http, gate, monkeypatch):
    """Scenario 1: finding → action → update → close → verify records closure evidence."""
    assessment, _conclusion, finding, action = _created_finding(db, http, gate, monkeypatch)
    before = _history(db, action.id)
    assert _post(http, db, assessment, finding, action, "status", status="in_progress").status_code == 200
    assert db.get(Finding, finding.id).status == "in_progress"
    assert _post(
        http,
        db,
        assessment,
        finding,
        action,
        "update",
        title=action.title,
        owner="Asha",
        target_date="2026-12-31",
    ).status_code == 200
    evidence, version = _closure_evidence(db, assessment)
    history_before_close = _history(db, action.id)
    response = _post(
        http,
        db,
        assessment,
        finding,
        action,
        "close",
        evidence_version_id=version.id,
        notes="Client sent memo",
    )
    assert response.status_code == 200
    assert 'data-action-status="closed"' in response.text
    assert "Closed, awaiting verification" in response.text
    assert 'data-verify-control' in response.text
    assert _history(db, action.id)[:-1] == history_before_close
    assert db.get(Finding, finding.id).status == "in_progress"

    history_before_verify = _history(db, action.id)
    response = _post(http, db, assessment, finding, action, "verify")
    assert response.status_code == 200
    assert 'data-action-status="verified"' in response.text
    assert _history(db, action.id)[:-1] == history_before_verify
    assert db.get(Finding, finding.id).status == "resolved"

    history = _history(db, action.id)
    assert [entry["action"] for entry in history] == [
        "created", "status_changed", "updated", "closed", "verified"
    ]
    assert all(set(entry) == set(findings.CLOSURE_HISTORY_KEYS) for entry in history[-2:])
    assert all(set(entry) == set(findings.HISTORY_KEYS) for entry in history[:-2])
    expected_evidence = {
        "evidence_id": evidence.id,
        "evidence_version_id": version.id,
        "version_number": 1,
        "sha256": version.file_hash_sha256,
        "filename": "closure.pdf",
    }
    assert history[-2]["changes"] == {"status": {"from": "in_progress", "to": "closed"}}
    assert history[-2]["notes"] == "Client sent memo"
    assert history[-2]["evidence"] == expected_evidence
    assert history[-1]["changes"] == {"status": {"from": "closed", "to": "verified"}}
    assert history[-1]["evidence"] == expected_evidence
    assert history[-2]["actor"] == history[-1]["actor"] == "consultant:Priya"
    assert all(datetime.fromisoformat(entry["timestamp"]).tzinfo for entry in history)
    page = http.get(f"/assessments/{assessment.id}/findings")
    assert "Closure verified" in page.text
    assert "Closed with evidence" in page.text
    assert f'href="/evidence/{evidence.id}"' in page.text
    assert "consultant:Priya" not in page.text


def test_scenario_2_state_machine_and_generic_status_route(db, http, gate, monkeypatch):
    """Scenario 2: closure routes enforce the four-state Action machine and generic targets remain narrow."""
    assert findings.ACTION_TRANSITIONS == {
        "open": ("in_progress", "closed"),
        "in_progress": ("open", "closed"),
        "closed": ("verified", "in_progress"),
        "verified": ("in_progress",),
    }
    assert findings.GENERIC_STATUS_TARGETS == ("open", "in_progress")
    assert findings.CLOSURE_STATUSES == ("closed", "verified")
    assert findings.ACTION_STATUS_LABELS == {
        "open": "Open",
        "in_progress": "In progress",
        "closed": "Closed, awaiting verification",
        "verified": "Closed and verified",
    }
    assert findings.CLOSURE_HISTORY_KEYS == findings.HISTORY_KEYS + ("evidence",)
    assert findings.EVIDENCE_KEYS == (
        "evidence_id", "evidence_version_id", "version_number", "sha256", "filename"
    )
    assert findings.HISTORY_ACTIONS == (
        "created", "status_changed", "updated", "closed", "verified", "reopened"
    )
    assessment, _conclusion, finding, action = _created_finding(db, http, gate, monkeypatch)
    response = _post(http, db, assessment, finding, action, "close")
    assert (response.status_code, response.json()["detail"]) == (400, findings.CLOSURE_EVIDENCE_REQUIRED)
    assert _post(
        http, db, assessment, finding, action, "status", status="closed"
    ).json()["detail"] == findings.CLOSURE_RESERVED
    assert _post(
        http, db, assessment, finding, action, "status", status="verified"
    ).json()["detail"] == findings.CLOSURE_RESERVED
    action.status = "closed"
    db.commit()
    response = _post(http, db, assessment, finding, action, "verify")
    assert response.json()["detail"] == findings.LEGACY_CLOSURE
    response = _post(http, db, assessment, finding, action, "reopen", notes="Revisit")
    assert response.status_code == 200
    assert db.get(Action, action.id).status == "in_progress"
    assessment2, _c2, finding2, action2 = _created_finding(
        db, http, gate, monkeypatch, client_name="Direct close"
    )
    evidence, version = _closure_evidence(db, assessment2, name="direct.txt", text_value="direct")
    response = _post(
        http, db, assessment2, finding2, action2, "close", evidence_version_id=version.id
    )
    assert response.status_code == 200
    assert db.get(Action, action2.id).status == "closed"
    assert evidence.status == "active"


def test_scenario_3_closure_evidence_scope_integrity_and_mapping(db, http, gate, monkeypatch):
    """Scenario 3: close accepts only active, intact evidence in assessment scope."""
    assessment, _c, finding, action = _created_finding(db, http, gate, monkeypatch)
    invalid_cases = []
    invalid_cases.append((None, None))
    other, _oc, _of, _oa = _created_finding(db, http, gate, monkeypatch, client_name="Other engagement")
    _oe, other_version = _closure_evidence(db, other, name="other.txt", text_value="other")
    invalid_cases.append((other_version.id, findings.CLOSURE_EVIDENCE_INVALID))
    own_evidence, own_version = _closure_evidence(db, assessment, name="own.txt", text_value="own")
    new_version = evidence_service.ingest_new_version(
        db,
        evidence_id=own_evidence.id,
        filename="own-v2.pdf",
        content=_closure_pdf("own v2"),
        change_reason="Updated memo",
    ).version
    assert new_version.status == "active"
    invalid_cases.append((own_version.id, findings.CLOSURE_EVIDENCE_INVALID))
    intact_evidence, intact_version = _closure_evidence(db, assessment, name="tampered.txt", text_value="tampered")
    evidence_service.blob_path(intact_version.storage_path).write_bytes(b"tampered bytes")
    invalid_cases.append((intact_version.id, findings.CLOSURE_EVIDENCE_INVALID))
    inactive_evidence, inactive_version = _closure_evidence(db, assessment, name="inactive.txt", text_value="inactive")
    inactive_evidence.status = "invalidated"
    db.commit()
    invalid_cases.append((inactive_version.id, findings.CLOSURE_EVIDENCE_INVALID))
    for version_id, expected in invalid_cases:
        before = _nothing_snapshot(db)
        response = _post(
            http,
            db,
            assessment,
            finding,
            action,
            "close",
            evidence_version_id=version_id or "",
        )
        assert response.status_code == 400
        assert response.json()["detail"] == (
            findings.CLOSURE_EVIDENCE_REQUIRED if version_id is None else expected
        )
        assert _nothing_snapshot(db) == before

    shared_engagement = db.get(Engagement, assessment.engagement_id)
    mapped_assessment = _seed(
        db,
        client_name="Mapped source",
        engagement=shared_engagement,
    )
    mapped_evidence, mapped_version = _closure_evidence(
        db, mapped_assessment, name="mapped.txt", text_value="mapped evidence"
    )
    evidence_service.map_evidence(
        db,
        evidence_id=mapped_evidence.id,
        assessment_id=assessment.id,
        framework_id="dpdpa",
        requirement_id=REQS[0],
        relevance="supporting",
        actor="consultant:Priya",
    )
    db.commit()
    use_count = db.query(EvidenceUse).count()
    response = _post(
        http, db, assessment, finding, action, "close", evidence_version_id=mapped_version.id
    )
    assert response.status_code == 200
    assert db.query(EvidenceUse).count() == use_count


def test_scenario_4_verification_rechecks_recorded_evidence(db, http, gate, monkeypatch):
    """Scenario 4: verification rechecks bytes and Evidence status while accepting superseded versions."""
    assessment, _c, finding, action = _created_finding(db, http, gate, monkeypatch)
    evidence, version = _closure_evidence(db, assessment, name="verify-tamper.txt", text_value="verify tamper")
    assert _post(http, db, assessment, finding, action, "close", evidence_version_id=version.id).status_code == 200
    evidence_service.blob_path(version.storage_path).write_bytes(b"changed")
    before = _nothing_snapshot(db)
    response = _post(http, db, assessment, finding, action, "verify")
    assert (response.status_code, response.json()["detail"]) == (400, findings.CLOSURE_EVIDENCE_CHANGED)
    assert _nothing_snapshot(db) == before

    assessment2, _c2, finding2, action2 = _created_finding(db, http, gate, monkeypatch, client_name="Archived evidence")
    archived, archived_version = _closure_evidence(db, assessment2, name="archived.txt", text_value="archived")
    assert _post(http, db, assessment2, finding2, action2, "close", evidence_version_id=archived_version.id).status_code == 200
    archived.status = "archived"
    db.commit()
    before = _nothing_snapshot(db)
    response = _post(http, db, assessment2, finding2, action2, "verify")
    assert (response.status_code, response.json()["detail"]) == (400, findings.CLOSURE_EVIDENCE_CHANGED)
    assert _nothing_snapshot(db) == before

    assessment3, _c3, finding3, action3 = _created_finding(db, http, gate, monkeypatch, client_name="Superseded evidence")
    original, original_version = _closure_evidence(db, assessment3, name="original.txt", text_value="original")
    assert _post(http, db, assessment3, finding3, action3, "close", evidence_version_id=original_version.id).status_code == 200
    replacement = evidence_service.ingest_new_version(
        db,
        evidence_id=original.id,
        filename="replacement.pdf",
        content=_closure_pdf("replacement"),
        change_reason="New version",
    ).version
    assert original_version.status == "superseded"
    response = _post(http, db, assessment3, finding3, action3, "verify")
    assert response.status_code == 200
    verified = _history(db, action3.id)[-1]
    assert verified["evidence"]["evidence_version_id"] == original_version.id
    assert verified["evidence"]["sha256"] != replacement.file_hash_sha256


def test_scenario_5_reopen_requires_reason_and_preserves_closures(db, http, gate, monkeypatch):
    """Scenario 5: reopening is a new append and forces a new evidence-backed closure."""
    assessment, _c, finding, action = _created_finding(db, http, gate, monkeypatch)
    _close_and_verify(db, http, assessment, finding, action, text_value="first closure")
    earlier = _history(db, action.id)[:]
    before = _nothing_snapshot(db)
    response = _post(http, db, assessment, finding, action, "reopen", notes=" ")
    assert (response.status_code, response.json()["detail"]) == (400, findings.REOPEN_REASON_REQUIRED)
    assert _nothing_snapshot(db) == before
    response = _post(http, db, assessment, finding, action, "reopen", notes="Regression found")
    assert response.status_code == 200
    assert db.get(Action, action.id).status == "in_progress"
    assert db.get(Finding, finding.id).status == "in_progress"
    history = _history(db, action.id)
    assert [entry["action"] for entry in history[-3:]] == ["closed", "verified", "reopened"]
    assert history[: len(earlier)] == earlier
    before = _nothing_snapshot(db)
    response = _post(http, db, assessment, finding, action, "reopen", notes=" ")
    assert (response.status_code, response.json()["detail"]) == (400, findings.NOT_REOPENABLE)
    assert _nothing_snapshot(db) == before
    before = _nothing_snapshot(db)
    response = _post(http, db, assessment, finding, action, "verify")
    assert (response.status_code, response.json()["detail"]) == (400, findings.NOT_VERIFIABLE)
    assert _nothing_snapshot(db) == before
    _close_and_verify(db, http, assessment, finding, action, text_value="second closure")
    history = _history(db, action.id)
    assert [entry["action"] for entry in history] == [
        "created", "closed", "verified", "reopened", "closed", "verified"
    ]
    assert findings.closure_on_record(history)["filename"] == f"{action.id}.pdf"


def test_scenario_6_finding_status_derivation_and_accepted_risk(db, http, gate, monkeypatch):
    """Scenario 6: Finding status follows Action statuses while accepted risk remains consultant-owned."""
    assessment, _c, finding, first = _created_finding(db, http, gate, monkeypatch)
    added = http.post(
        f"/api/assessments/{assessment.id}/findings/{finding.id}/actions",
        data={"title": "Second action", "reviewer_name": "Priya"},
    )
    assert added.status_code == 200
    second = db.query(Action).filter(Action.finding_id == finding.id, Action.id != first.id).one()
    _close_and_verify(db, http, assessment, finding, first, text_value="first")
    assert db.get(Finding, finding.id).status == "in_progress"
    _close_and_verify(db, http, assessment, finding, second, text_value="second")
    assert db.get(Finding, finding.id).status == "resolved"
    third_response = http.post(
        f"/api/assessments/{assessment.id}/findings/{finding.id}/actions",
        data={"title": "Third action", "reviewer_name": "Priya"},
    )
    assert third_response.status_code == 200
    assert db.get(Finding, finding.id).status == "in_progress"
    third = db.query(Action).filter(Action.finding_id == finding.id, Action.id.not_in([first.id, second.id])).one()
    before = db.get(Finding, finding.id).status
    assert _post(
        http,
        db,
        assessment,
        finding,
        third,
        "update",
        title=third.title,
        owner="Asha",
    ).status_code == 200
    assert db.get(Finding, finding.id).status == before

    finding.status = "accepted_risk"
    db.commit()
    assert _post(http, db, assessment, finding, third, "status", status="in_progress").status_code == 200
    evidence, version = _closure_evidence(db, assessment, name="risk.txt", text_value="risk")
    assert _post(http, db, assessment, finding, third, "close", evidence_version_id=version.id).status_code == 200
    assert _post(http, db, assessment, finding, third, "verify").status_code == 200
    assert db.get(Finding, finding.id).status == "accepted_risk"
    page_model = findings.findings_page(db, assessment.id)
    view = next(view for view in page_model.findings if view.finding.id == finding.id)
    assert view.status_label == "Accepted risk"
    assert view.closure_options is page_model.findings[0].closure_options
    page = http.get(f"/assessments/{assessment.id}/findings")
    assert "Status: Accepted risk" in page.text


def test_scenario_7_migrated_closed_actions_require_reverification(db, http):
    """Scenario 7: migrated closed Actions remain legacy until reopened, closed with evidence and verified."""
    assessment = _seed_legacy_assessment(
        db,
        company_name="Legacy",
        gap_items=[
            _gap_item_kwargs(
                remediation_status="closed",
                remediation_closed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            )
        ],
    )
    stats = run_migration(db)
    assert (stats.findings, stats.actions) == (1, 1)
    action = db.query(Action).one()
    finding = db.get(Finding, action.finding_id)
    page = http.get(f"/assessments/{assessment.id}/findings")
    action_html = page.text[page.text.index(f'id="action-{action.id}"'):]
    assert "Closed without closure evidence (legacy)" in action_html
    assert "data-reopen-control" in action_html
    assert "data-verify-control" not in action_html
    assert f"actions/{action.id}/status" not in action_html
    before = _nothing_snapshot(db)
    response = _post(http, db, assessment, finding, action, "verify")
    assert (response.status_code, response.json()["detail"]) == (400, findings.LEGACY_CLOSURE)
    assert _nothing_snapshot(db) == before
    imported = _history(db, action.id)[0].copy()
    db.refresh(assessment)
    assert assessment.engagement_id is not None
    assert _post(http, db, assessment, finding, action, "reopen", notes="No evidence on file").status_code == 200
    evidence, version = _closure_evidence(db, assessment, name="legacy.txt", text_value="legacy evidence")
    assert _post(http, db, assessment, finding, action, "close", evidence_version_id=version.id).status_code == 200
    assert _post(http, db, assessment, finding, action, "verify").status_code == 200
    assert [entry["action"] for entry in _history(db, action.id)] == [
        "imported", "reopened", "closed", "verified"
    ]
    assert _history(db, action.id)[0] == imported
    assert set(imported) == {"actor", "action", "timestamp", "notes"}
    stats = run_migration(db)
    assert (stats.findings, stats.actions) == (0, 0)


def test_scenario_8_append_concurrency_and_unreadable_history(db, http, gate, monkeypatch):
    """Scenario 8: stale close, verify and reopen tokens and CAS races never overwrite history."""
    assessment, _c, finding, action = _created_finding(db, http, gate, monkeypatch)
    evidence, version = _closure_evidence(db, assessment, name="stale.txt", text_value="stale")
    before = _nothing_snapshot(db)
    response = _post(
        http,
        db,
        assessment,
        finding,
        action,
        "close",
        evidence_version_id=version.id,
        expected_history_length=0,
    )
    assert (response.status_code, response.json()["detail"]) == (409, findings.STALE_ACTION)
    assert _nothing_snapshot(db) == before
    assert _post(http, db, assessment, finding, action, "close", evidence_version_id=version.id).status_code == 200
    before = _nothing_snapshot(db)
    response = _post(http, db, assessment, finding, action, "verify", expected_history_length=1)
    assert (response.status_code, response.json()["detail"]) == (409, findings.STALE_ACTION)
    assert _nothing_snapshot(db) == before
    assert _post(http, db, assessment, finding, action, "verify").status_code == 200
    before = _nothing_snapshot(db)
    response = _post(http, db, assessment, finding, action, "reopen", notes="Reopen", expected_history_length=1)
    assert (response.status_code, response.json()["detail"]) == (409, findings.STALE_ACTION)
    assert _nothing_snapshot(db) == before

    original_raw = db.get(Action, action.id).history_json
    real_load = findings.load_history
    raced = False

    def _race(raw):
        nonlocal raced
        parsed = real_load(raw)
        if not raced:
            raced = True
            db.execute(
                text("UPDATE actions SET history_json = :history WHERE id = :id"),
                {"history": json.dumps(parsed + [{"actor": "other", "action": "updated", "timestamp": "race", "notes": None, "changes": {}}]), "id": action.id},
            )
        return parsed

    monkeypatch.setattr(findings, "load_history", _race)
    before = _nothing_snapshot(db)
    response = _post(http, db, assessment, finding, action, "reopen", notes="Race")
    assert (response.status_code, response.json()["detail"]) == (409, findings.STALE_ACTION)
    db.expire_all()
    assert db.get(Action, action.id).history_json == original_raw
    assert _nothing_snapshot(db) == before
    monkeypatch.setattr(findings, "load_history", real_load)
    action.history_json = "not json"
    db.commit()
    response = _post(
        http,
        db,
        assessment,
        finding,
        action,
        "close",
        evidence_version_id=version.id,
        expected_history_length=4,
    )
    assert (response.status_code, response.json()["detail"]) == (400, findings.UNREADABLE_HISTORY)
    page = http.get(f"/assessments/{assessment.id}/findings")
    action_html = page.text[page.text.index(f'id="action-{action.id}"'):]
    assert "History could not be read." in action_html
    assert "data-close-control" not in action_html
    assert "data-verify-control" not in action_html
    assert "data-reopen-control" not in action_html


def test_scenario_9_gap_item_path_retired_and_report_uses_actions(db, http, gate, monkeypatch):
    """Scenario 9: legacy GapItem remediation is read-only and report progress comes from Actions."""
    assessment, _c, finding, action = _created_finding(db, http, gate, monkeypatch)
    report = db.query(GapReport).filter_by(assessment_id=assessment.id).one()
    item = db.query(GapItem).filter_by(report_id=report.id).first()
    item.remediation_owner = "owner@example.com"
    item.remediation_notes = "Legacy note"
    db.commit()
    before = (item.remediation_status, item.remediation_owner, item.remediation_notes, item.remediation_closed_at)
    assert not (REPO_ROOT / "app/routers/remediation.py").exists()
    assert not (REPO_ROOT / "app/schemas/remediation.py").exists()
    route_paths = {route.path for route in app.routes}
    assert not any("/gap-items/" in path or "remediation-summary" in path for path in route_paths)
    response = http.patch(f"/api/assessments/{assessment.id}/gap-items/{item.id}/remediation", data={})
    assert response.status_code in (404, 405)
    panel = (REPO_ROOT / "app/templates/partials/remediation_panel.html").read_text()
    assert not re.search(r"<form|<button|<select|hx-", panel, re.IGNORECASE)
    summary = http.get(f"/assessments/{assessment.id}/report-summary")
    assert summary.status_code == 200
    assert "data-legacy-remediation" in summary.text
    assert "Legacy remediation record (read-only)" in summary.text
    assert "owner@example.com" in summary.text
    assert "Legacy note" in summary.text
    assert before == (item.remediation_status, item.remediation_owner, item.remediation_notes, item.remediation_closed_at)

    _close_and_verify(db, http, assessment, finding, action, text_value="report closure")
    second = http.post(
        f"/api/assessments/{assessment.id}/findings/{finding.id}/actions",
        data={"title": "Open report action", "reviewer_name": "Priya"},
    )
    assert second.status_code == 200
    summary = http.get(f"/assessments/{assessment.id}/report-summary")
    assert "Remediation Progress" in summary.text
    assert "1 of 2 actions closed and verified" in summary.text
    assert f'href="/assessments/{assessment.id}/findings"' in summary.text
    empty, _ec, = _run_one(db, gate, monkeypatch, client_name="No action report")
    _approve(http, db, empty, _ec)
    empty_summary = http.get(f"/assessments/{empty.id}/report-summary")
    assert "No remediation actions yet." in empty_summary.text


def _make_assessment_with_findings(db, http, gate, monkeypatch, engagement, *, name, items):
    assessment = _seed(
        db,
        applicable=[item["requirement_id"] for item in items],
        client_name=name,
        engagement=engagement,
    )
    _stub_single(monkeypatch, items)
    gate.trigger_analysis(assessment.id, db)
    conclusions = db.query(Conclusion).filter_by(assessment_id=assessment.id).order_by(Conclusion.requirement_id).all()
    findings_rows = []
    for conclusion in conclusions:
        _approve(http, db, assessment, conclusion)
        response = _create(http, assessment, conclusion)
        assert response.status_code == 200
        finding = db.get(Finding, response.json()["finding_id"])
        action = db.query(Action).filter_by(finding_id=finding.id).one()
        findings_rows.append((finding, action))
    return assessment, findings_rows


def test_scenario_10_engagement_rollup_and_tracker_page(db, http, gate, monkeypatch):
    """Scenario 10: engagement rollup counts and lists preserve assessment/framework/requirement provenance."""
    client = Client(name="Rollup client", industry="Technology", size="medium")
    db.add(client)
    db.flush()
    engagement = Engagement(client_id=client.id, name="Rollup engagement", status="active")
    db.add(engagement)
    db.flush()
    a, a_rows = _make_assessment_with_findings(
        db,
        http,
        gate,
        monkeypatch,
        engagement,
        name="Assessment A",
        items=[
            _item(REQS[0], "non_compliant", risk="critical", action="A open"),
            _item(REQS[1], "partially_compliant", risk="high", action="A closed"),
        ],
    )
    b, b_rows = _make_assessment_with_findings(
        db,
        http,
        gate,
        monkeypatch,
        engagement,
        name="Assessment B",
        items=[_item(REQS[2], "insufficient_evidence", risk="medium", action="B open")],
    )
    archived, _ac, _af, _aa = _created_finding(
        db,
        http,
        gate,
        monkeypatch,
        client_name="Archived",
        engagement=engagement,
        item=_item(REQS[0], "non_compliant"),
    )
    archived.status = "archived"
    db.commit()
    _other, _oc, _of, _oa = _created_finding(
        db, http, gate, monkeypatch, client_name="Outside engagement"
    )

    a_open = a_rows[0][1]
    a_closed = a_rows[1][1]
    today = datetime.now(timezone.utc).date()
    a_open.owner = "Asha"
    a_open.target_date = datetime.combine(today - timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
    db.commit()
    a_extra_response = http.post(
        f"/api/assessments/{a.id}/findings/{a_rows[0][0].id}/actions",
        data={"title": "A in progress", "reviewer_name": "Priya"},
    )
    assert a_extra_response.status_code == 200
    a_in_progress = db.query(Action).filter(Action.finding_id == a_rows[0][0].id, Action.id != a_open.id).one()
    assert _post(http, db, a, a_rows[0][0], a_in_progress, "status", status="in_progress").status_code == 200
    a_closed_evidence, a_closed_version = _closure_evidence(db, a, name="rollup-closed.txt", text_value="closed")
    assert _post(http, db, a, a_rows[1][0], a_closed, "close", evidence_version_id=a_closed_version.id).status_code == 200
    a_verified = db.query(Action).filter(Action.finding_id == a_rows[1][0].id).one()
    b_open = b_rows[0][1]
    b_open.owner = "Asha"
    b_open.target_date = datetime.combine(today + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
    db.commit()
    b_extra_response = http.post(
        f"/api/assessments/{b.id}/findings/{b_rows[0][0].id}/actions",
        data={"title": "B verified", "reviewer_name": "Priya"},
    )
    assert b_extra_response.status_code == 200
    b_verified = db.query(Action).filter(Action.finding_id == b_rows[0][0].id, Action.id != b_open.id).one()
    _close_and_verify(db, http, b, b_rows[0][0], b_verified, text_value="verified")
    b_verified.owner = "Asha"
    db.commit()

    rollup = remediation_rollup.engagement_rollup(db, engagement, today=today)
    assert rollup.counts == {
        "open": 2,
        "in_progress": 1,
        "awaiting_verification": 1,
        "verified": 1,
        "overdue": 1,
        "unassigned": 1,
        "total": 5,
    }
    assert [row["severity"] for row in rollup.by_severity[:4]] == list(findings.RISK_LEVELS)
    assert rollup.by_owner == [
        {"owner": "Asha", "active": 2, "overdue": 1},
        {"owner": "Unassigned", "active": 1, "overdue": 0},
    ]
    assert [row.assessment_id for row in rollup.assessments] == [a.id, b.id]
    assert rollup.assessments[0].counts == {
        "open": 1, "in_progress": 1, "awaiting_verification": 1,
        "verified": 0, "overdue": 1, "unassigned": 1, "total": 3,
    }
    assert rollup.assessments[1].counts == {
        "open": 1, "in_progress": 0, "awaiting_verification": 0,
        "verified": 1, "overdue": 0, "unassigned": 0, "total": 2,
    }
    assert len(rollup.overdue) == 1
    assert rollup.overdue[0].framework_id == "dpdpa"
    assert rollup.overdue[0].requirement_id == REQS[0]
    assert rollup.overdue[0].href == f"/assessments/{a.id}/findings#finding-{a_rows[0][0].id}"
    assert rollup.awaiting_verification[0].action_id == a_closed.id
    assert remediation_rollup.assessment_action_counts(db, a.id, today=today) == rollup.assessments[0].counts
    a_closed.owner = "<script>x</script>"
    db.commit()
    page = http.get(f"/engagements/{engagement.id}/remediation")
    assert page.status_code == 200
    assert page.text.count("data-rollup-count=") == len(remediation_rollup.ROLLUP_KEYS)
    assert page.text.count("data-severity-row=") == 4
    assert page.text.count("data-owner-row") == 2
    assert page.text.count("data-assessment-row") == 2
    assert page.text.count("data-overdue-action") == 1
    assert page.text.count("data-awaiting-action") == 1
    assert f"/assessments/{a.id}/findings#finding-{a_rows[0][0].id}" in page.text
    assert "not compliance scores" in page.text
    assert "consultant:" not in page.text
    assert "&lt;script&gt;x&lt;/script&gt;" in page.text
    assert http.get(f"/engagements/{engagement.id}").text.count(
        f'href="/engagements/{engagement.id}/remediation"'
    ) == 1
    assert f'href="/engagements/{engagement.id}/remediation"' in http.get(
        f"/assessments/{a.id}/findings"
    ).text
    empty_client = Client(name="Empty rollup", industry="Technology", size="medium")
    db.add(empty_client)
    db.flush()
    empty_engagement = Engagement(client_id=empty_client.id, name="Empty", status="active")
    db.add(empty_engagement)
    db.commit()
    assert "No actions in this engagement yet." in http.get(
        f"/engagements/{empty_engagement.id}/remediation"
    ).text
    assert http.get("/engagements/unknown/remediation").status_code == 404


def test_scenario_11_structural_guards_and_read_models():
    """Scenario 11: route, source, template and field contracts remain stable."""
    expected_findings = {
        ("GET", "/assessments/{assessment_id}/findings"),
        ("POST", "/api/assessments/{assessment_id}/findings"),
        ("POST", "/api/assessments/{assessment_id}/findings/{finding_id}/actions"),
        ("POST", "/api/assessments/{assessment_id}/findings/{finding_id}/actions/{action_id}/status"),
        ("POST", "/api/assessments/{assessment_id}/findings/{finding_id}/actions/{action_id}/update"),
        ("POST", "/api/assessments/{assessment_id}/findings/{finding_id}/actions/{action_id}/close"),
        ("POST", "/api/assessments/{assessment_id}/findings/{finding_id}/actions/{action_id}/verify"),
        ("POST", "/api/assessments/{assessment_id}/findings/{finding_id}/actions/{action_id}/reopen"),
    }
    actual_findings = {
        (method, route.path)
        for route in app.routes
        if "/findings" in route.path
        for method in route.methods
        if method in {"GET", "POST", "PATCH", "PUT", "DELETE"}
    }
    assert actual_findings == expected_findings
    assert {
        (method, route.path)
        for route in app.routes
        if "/remediation" in route.path
        for method in route.methods
        if method in {"GET", "POST", "PATCH", "PUT", "DELETE"}
    } == {("GET", "/engagements/{engagement_id}/remediation")}
    sources = [
        (REPO_ROOT / "app/services/findings.py").read_text(),
        (REPO_ROOT / "app/routers/findings.py").read_text(),
        (REPO_ROOT / "app/services/remediation_rollup.py").read_text(),
    ]
    assert all("delete" not in source.lower() for source in sources)
    rollup_source = sources[-1]
    assert all(token not in rollup_source for token in ("db.add(", ".flush(", ".commit("))
    assert ".commit(" not in inspect.getsource(web.remediation_tracker_page)
    for filename in ("remediation_tracker.html", "../partials/remediation_panel.html"):
        source = (REPO_ROOT / "app/templates/pages" / filename).resolve().read_text()
        assert not re.search(r"<form|hx-post|hx-put|hx-patch|hx-delete|\|\s*safe\b|overall_score|CyberAssess", source, re.IGNORECASE)
    guard_source = "\n".join(
        (
            REPO_ROOT / path
        ).read_text()
        for path in (
            "app/services/findings.py",
            "app/routers/findings.py",
            "app/schemas/findings.py",
            "app/templates/pages/findings.html",
            "app/templates/components/finding_card.html",
        )
    )
    assert re.search(r'select all|create all|all conclusions|type="checkbox"|\bmultiple\b|\|\s*safe\b', guard_source, re.IGNORECASE) is None
    assert "CLOSURE_RESERVED" in guard_source
    assert "LEGACY_CLOSURE" in guard_source
    assert "Closed without closure evidence (legacy)" in guard_source
    signature = inspect.signature(findings.close_action)
    assert "evidence_version_id" in signature.parameters
    assert all("list" not in str(parameter.annotation) for parameter in signature.parameters.values())


def test_scenario_12_existing_surfaces_and_schema_head_remain_unchanged():
    """Scenario 12: the task leaves the existing workpaper, migration and schema surfaces intact."""
    for path in (
        "app/services/evidence.py",
        "app/services/conclusion_review.py",
        "app/services/workpaper.py",
        "scripts/migrate_legacy.py",
        "app/utils/pdf_export.py",
        "app/routers/reports.py",
    ):
        assert (REPO_ROOT / path).exists()
    assert not list((REPO_ROOT / "alembic/versions").glob("*p3_4*"))
    assert "relationship(" not in "\n".join(
        path.read_text() for path in (REPO_ROOT / "app/models").glob("*.py")
    )
