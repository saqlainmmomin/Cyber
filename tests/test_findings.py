"""Contract suite for P3-1 Findings and append-only Action history."""

from __future__ import annotations

import copy
import inspect
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import unquote

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, insert, text
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
from app.models.finding import Finding
from app.models.questionnaire import QuestionnaireResponse
from app.models.report import GapItem, GapReport
from app.services import findings, workpaper
from scripts import migrate_legacy
from scripts.migrate_legacy import run_migration

REPO_ROOT = Path(__file__).resolve().parents[1]
ALL_REQS = [row["id"] for row in get_all_requirements()]
REQS = ALL_REQS[:3]


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
    path = tmp_path / "findings.sqlite3"
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


@pytest.fixture()
def gate(monkeypatch):
    from app.frameworks import questionnaire_builder
    from app.routers import analysis

    monkeypatch.setattr(analysis, "build_questionnaire", lambda **_kwargs: [{"id": "Q1"}])
    monkeypatch.setattr(analysis, "generate_initiatives", lambda *_args: [])
    monkeypatch.setattr(analysis, "generate_multi_framework_initiatives", lambda *_args: [])
    monkeypatch.setattr(questionnaire_builder, "build_multi_questionnaire", lambda *_a, **_k: [])
    return analysis


def _seed(db, *, applicable=None, client_name="Acme Corp"):
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


def _revisions(db, conclusion_id):
    db.expire_all()
    return (
        db.query(ConclusionRevision)
        .filter_by(conclusion_id=conclusion_id)
        .order_by(ConclusionRevision.created_at, text("conclusion_revisions.rowid"))
        .all()
    )


def _url(assessment, conclusion, route):
    return f"/api/assessments/{assessment.id}/conclusions/{conclusion.id}/{route}"


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
    for key, value in overrides.items():
        if value is None:
            payload.pop(key, None)
        else:
            payload[key] = value
    return http.post(f"/api/assessments/{assessment.id}/findings", data=payload)


def _history(db, action_id):
    db.expire_all()
    return json.loads(db.get(Action, action_id).history_json)


def _run_one(db, gate, monkeypatch, *, item=None, client_name="Acme Corp"):
    assessment = _seed(db, client_name=client_name)
    _stub_single(monkeypatch, [item or _item(REQS[0])])
    gate.trigger_analysis(assessment.id, db)
    conclusion = db.query(Conclusion).filter_by(assessment_id=assessment.id).one()
    return assessment, conclusion


def _decide(http, assessment, conclusion, route, **overrides):
    payload = {
        "expected_version": conclusion.version,
        "reviewer_name": "Priya",
    }
    if route == "edit":
        payload.update(
            {
                "outcome": "non_compliant",
                "rationale": "Consultant rationale",
                "gaps_identified": "Consultant gap",
                "risk_level": "high",
                "recommended_action": "Consultant action",
            }
        )
    payload.update(overrides)
    response = http.post(_url(assessment, conclusion, route), data=payload)
    return response


def _approve(http, db, assessment, conclusion):
    response = _decide(http, assessment, conclusion, "approve")
    assert response.status_code == 200
    db.refresh(conclusion)
    return response


def _human_revision(db, conclusion, action, *, actor="consultant:Priya"):
    conclusion.version += 1
    if action == "edited":
        conclusion.ai_proposed = False
    revision = ConclusionRevision(
        conclusion_id=conclusion.id,
        actor=actor,
        action=action,
        previous_outcome=conclusion.outcome,
        previous_rationale=conclusion.rationale,
        citations_json=None,
        created_at=datetime.now(timezone.utc),
    )
    db.add(revision)
    db.commit()
    return revision


def _counts(db):
    return {
        table: db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one()
        for table in ("findings", "actions", "audit_events", "conclusion_revisions")
    }


def _action_snapshot(db):
    return db.execute(
        text(
            "SELECT id, status, title, owner, target_date, history_json, updated_at "
            "FROM actions ORDER BY id"
        )
    ).all()


def _conclusion_snapshot(db):
    return db.execute(
        text("SELECT id, version, updated_at FROM conclusions ORDER BY id")
    ).all()


def _nothing_snapshot(db):
    return _counts(db), _action_snapshot(db), _conclusion_snapshot(db)


def _created_finding(db, http, gate, monkeypatch, *, client_name="Acme Corp"):
    assessment, conclusion = _run_one(
        db,
        gate,
        monkeypatch,
        item=_item(REQS[0], "non_compliant"),
        client_name=client_name,
    )
    _approve(http, db, assessment, conclusion)
    response = _create(http, assessment, conclusion)
    assert response.status_code == 200
    finding = db.get(Finding, response.json()["finding_id"])
    action = db.query(Action).filter_by(finding_id=finding.id).one()
    return assessment, conclusion, finding, action


def test_scenario_1_create_add_status_and_history(db, http, gate, monkeypatch):
    """Scenario 1: create, status update and add preserve complete append-only history."""
    assessment = _seed(db, applicable=[REQS[0]])
    _stub_single(monkeypatch, [_item(REQS[0], "non_compliant")])
    gate.trigger_analysis(assessment.id, db)
    conclusion = db.query(Conclusion).filter_by(assessment_id=assessment.id).one()
    approved = http.post(
        _url(assessment, conclusion, "approve"),
        data={"expected_version": conclusion.version, "reviewer_name": "Priya"},
    )
    assert approved.status_code == 200
    db.refresh(conclusion)

    response = _create(http, assessment, conclusion)
    assert response.status_code == 200
    finding_id = response.json()["finding_id"]
    assert response.headers["HX-Redirect"] == (
        f"/assessments/{assessment.id}/findings#finding-{finding_id}"
    )
    finding = db.get(Finding, finding_id)
    assert (
        finding.status,
        finding.title,
        finding.description,
        finding.severity,
        finding.priority,
        finding.conclusion_id,
        finding.assessment_id,
    ) == (
        "open",
        "Finding title",
        "Finding description",
        "high",
        1,
        conclusion.id,
        assessment.id,
    )
    first = db.query(Action).filter_by(finding_id=finding_id).one()
    assert (first.status, first.owner, first.target_date) == ("open", None, None)
    created = _history(db, first.id)
    assert len(created) == 1
    assert set(created[0]) == set(findings.HISTORY_KEYS)
    assert created[0] == {
        "actor": "consultant:Priya",
        "action": "created",
        "timestamp": created[0]["timestamp"],
        "notes": None,
        "changes": {
            "title": {"from": None, "to": "First action"},
            "owner": {"from": None, "to": None},
            "target_date": {"from": None, "to": None},
            "status": {"from": None, "to": "open"},
        },
    }
    assert datetime.fromisoformat(created[0]["timestamp"]).tzinfo is not None

    event_row = db.query(AuditEvent).filter_by(entity_id=finding_id).one()
    metadata = json.loads(event_row.metadata_json)
    assert (event_row.action, event_row.entity_type) == ("finding_created", "finding")
    assert set(metadata) == {
        "assessment_id",
        "conclusion_id",
        "conclusion_version",
        "conclusion_revision_id",
        "framework_id",
        "requirement_id",
        "first_action_id",
    }
    assert metadata["conclusion_version"] == 2
    assert metadata["conclusion_revision_id"] == next(
        row.id for row in _revisions(db, conclusion.id) if row.action == "approved"
    )

    response = http.post(
        f"/api/assessments/{assessment.id}/findings/{finding_id}/actions/{first.id}/status",
        data={
            "status": "in_progress",
            "expected_history_length": 1,
            "notes": "Kickoff",
            "reviewer_name": "Priya",
        },
    )
    assert response.status_code == 200
    assert f'id="finding-{finding_id}"' in response.text
    assert 'data-action-status="in_progress"' in response.text
    history = _history(db, first.id)
    assert [entry["action"] for entry in history] == ["created", "status_changed"]
    assert history[1]["changes"] == {
        "status": {"from": "open", "to": "in_progress"}
    }
    assert history[1]["notes"] == "Kickoff"
    assert datetime.fromisoformat(history[1]["timestamp"]).tzinfo is not None

    response = http.post(
        f"/api/assessments/{assessment.id}/findings/{finding_id}/actions",
        data={
            "title": "Second action",
            "owner": "Asha",
            "target_date": "2026-12-31",
            "reviewer_name": "Priya",
        },
    )
    assert response.status_code == 200
    second = (
        db.query(Action)
        .filter(Action.finding_id == finding_id, Action.id != first.id)
        .one()
    )
    second_history = _history(db, second.id)
    assert second_history[0]["changes"]["owner"]["to"] == "Asha"
    assert second_history[0]["changes"]["target_date"]["to"] == "2026-12-31"
    assert second.target_date.date().isoformat() == "2026-12-31"
    assert datetime.fromisoformat(second_history[0]["timestamp"]).tzinfo is not None


def test_scenario_2_eligibility_and_page_membership(db, http, gate, monkeypatch):
    """Scenario 2: only current individual gap decisions are eligible."""
    pending_a, pending = _run_one(
        db, gate, monkeypatch, client_name="Pending", item=_item(REQS[0], "non_compliant")
    )
    before = _nothing_snapshot(db)
    response = _create(http, pending_a, pending)
    assert (response.status_code, response.json()["detail"]) == (400, findings.NOT_APPROVED)
    assert _nothing_snapshot(db) == before

    rejected_a, rejected = _run_one(
        db, gate, monkeypatch, client_name="Rejected", item=_item(REQS[0], "non_compliant")
    )
    assert _decide(http, rejected_a, rejected, "reject").status_code == 200
    db.refresh(rejected)
    before = _nothing_snapshot(db)
    response = _create(http, rejected_a, rejected)
    assert (response.status_code, response.json()["detail"]) == (400, findings.NOT_APPROVED)
    assert _nothing_snapshot(db) == before

    reopened_a, reopened = _run_one(
        db, gate, monkeypatch, client_name="Reopened", item=_item(REQS[0], "non_compliant")
    )
    _approve(http, db, reopened_a, reopened)
    assert _decide(http, reopened_a, reopened, "reopen").status_code == 200
    db.refresh(reopened)
    before = _nothing_snapshot(db)
    response = _create(http, reopened_a, reopened)
    assert (response.status_code, response.json()["detail"]) == (400, findings.NOT_APPROVED)
    assert _nothing_snapshot(db) == before

    compliant_a, compliant = _run_one(
        db,
        gate,
        monkeypatch,
        client_name="Compliant",
        item=_item(REQS[0], "compliant", gap="", action=""),
    )
    _approve(http, db, compliant_a, compliant)
    before = _nothing_snapshot(db)
    response = _create(http, compliant_a, compliant)
    assert (response.status_code, response.json()["detail"]) == (400, findings.NO_GAP)
    assert _nothing_snapshot(db) == before

    bulk_a, bulk = _run_one(
        db, gate, monkeypatch, client_name="Bulk", item=_item(REQS[0], "non_compliant")
    )
    _human_revision(db, bulk, "approved", actor="Manager Review")
    db.refresh(bulk)
    before = _nothing_snapshot(db)
    response = _create(http, bulk_a, bulk)
    assert (response.status_code, response.json()["detail"]) == (400, findings.LEGACY_BULK)
    assert _nothing_snapshot(db) == before

    other_a, other = _run_one(
        db, gate, monkeypatch, client_name="Other", item=_item(REQS[0], "non_compliant")
    )
    _approve(http, db, other_a, other)
    before = _nothing_snapshot(db)
    response = _create(http, pending_a, other)
    assert response.status_code == 404
    assert _nothing_snapshot(db) == before
    response = _create(http, pending_a, pending, conclusion_id="unknown")
    assert response.status_code == 404
    response = _create(http, pending_a, pending, conclusion_id="")
    assert response.status_code == 404
    assert _nothing_snapshot(db) == before

    before = _nothing_snapshot(db)
    response = _create(
        http,
        other_a,
        other,
        conclusion_version=other.version - 1,
    )
    assert (response.status_code, response.json()["detail"]) == (409, findings.STALE_CONCLUSION)
    assert unquote(response.headers["X-Toast-Message"]) == findings.STALE_CONCLUSION
    assert _nothing_snapshot(db) == before

    edited_a, edited = _run_one(
        db, gate, monkeypatch, client_name="Edited", item=_item(REQS[0], "partially_compliant")
    )
    assert _decide(http, edited_a, edited, "edit").status_code == 200
    db.refresh(edited)
    read_model = findings.findings_page(db, edited_a.id)
    assert [row.card.conclusion.id for row in read_model.eligible] == [edited.id]
    assert _create(http, edited_a, edited).status_code == 200
    assert findings.findings_page(db, edited_a.id).eligible == []


def test_scenario_3_one_finding_per_conclusion(db, http, gate, monkeypatch):
    """Scenario 3: duplicate and migrated collisions preserve one Finding per Conclusion."""
    assessment, conclusion, finding, _action = _created_finding(db, http, gate, monkeypatch)
    before = _nothing_snapshot(db)
    response = _create(http, assessment, conclusion)
    assert (response.status_code, response.json()["detail"]) == (400, findings.DUPLICATE)
    assert _nothing_snapshot(db) == before

    second_a, second = _run_one(
        db, gate, monkeypatch, client_name="Migrated", item=_item(REQS[0], "non_compliant")
    )
    _approve(http, db, second_a, second)
    migrated = Finding(
        assessment_id=second_a.id,
        conclusion_id=second.id,
        title="Migrated finding",
        description="Legacy description",
        severity="high",
        priority=1,
        status="open",
    )
    db.add(migrated)
    db.flush()
    db.add(
        Action(
            finding_id=migrated.id,
            title="Imported action",
            owner=None,
            target_date=None,
            status="open",
            history_json=json.dumps(
                [{"actor": "system:migration", "action": "imported", "timestamp": datetime.now(timezone.utc).isoformat(), "notes": "Migrated from legacy GapItem remediation fields"}]
            ),
        )
    )
    db.commit()
    before = _nothing_snapshot(db)
    response = _create(http, second_a, second)
    assert (response.status_code, response.json()["detail"]) == (400, findings.DUPLICATE)
    assert _nothing_snapshot(db) == before
    page = http.get(f"/assessments/{second_a.id}/findings")
    assert page.status_code == 200
    assert 'data-finding-origin="migrated"' in page.text

    response = http.post(
        f"/api/assessments/{assessment.id}/findings",
        json={
            "conclusion_id": [conclusion.id],
            "conclusion_version": conclusion.version,
            "title": "Another",
            "description": "Another",
            "severity": "high",
            "priority": 1,
            "action_title": "Action",
        },
    )
    assert response.status_code == 422
    assert db.query(Finding).filter_by(conclusion_id=conclusion.id).count() == 1
    assert db.get(Finding, finding.id) is not None


@pytest.mark.parametrize(
    ("current", "target", "expected_status", "message"),
    [
        ("open", "open", 400, "An action cannot move from open to open."),
        ("open", "in_progress", 200, None),
        ("open", "closed", 400, findings.CLOSURE_RESERVED),
        ("open", "verified", 400, findings.CLOSURE_RESERVED),
        ("in_progress", "open", 200, None),
        ("in_progress", "in_progress", 400, "An action cannot move from in_progress to in_progress."),
        ("in_progress", "closed", 400, findings.CLOSURE_RESERVED),
        ("in_progress", "verified", 400, findings.CLOSURE_RESERVED),
    ],
)
def test_scenario_4_action_state_machine(
    db, http, gate, monkeypatch, current, target, expected_status, message
):
    """Scenario 4: the P3-1 state machine permits only open and in-progress reversal."""
    assert findings.ACTION_TRANSITIONS == {
        "open": ("in_progress",),
        "in_progress": ("open",),
        "closed": (),
        "verified": (),
    }
    assert findings.CLOSURE_STATUSES == ("closed", "verified")
    assert set(findings.ACTION_STATUSES) == set(migrate_legacy.ACTION_STATUSES)
    assert set(findings.FINDING_STATUSES) == set(migrate_legacy.FINDING_STATUSES)
    assessment, _conclusion, finding, action = _created_finding(
        db, http, gate, monkeypatch, client_name=f"{current}-{target}"
    )
    action.status = current
    db.commit()
    before_history = _history(db, action.id)
    before = _nothing_snapshot(db)
    response = http.post(
        f"/api/assessments/{assessment.id}/findings/{finding.id}/actions/{action.id}/status",
        data={
            "status": target,
            "expected_history_length": len(before_history),
            "reviewer_name": "Priya",
        },
    )
    assert response.status_code == expected_status
    if expected_status == 200:
        after = _history(db, action.id)
        assert after[:-1] == before_history
        assert after[-1]["action"] == "status_changed"
        assert db.get(Action, action.id).status == target
    else:
        assert response.json()["detail"] == message
        assert _nothing_snapshot(db) == before


def test_scenario_4_terminal_and_unknown_status(db, http, gate, monkeypatch):
    """Scenario 4: terminal rows are read-only and unknown status input is invalid."""
    assessment, _conclusion, finding, action = _created_finding(db, http, gate, monkeypatch)
    action.status = "closed"
    db.commit()
    for target in findings.ACTION_STATUSES:
        before = _nothing_snapshot(db)
        response = http.post(
            f"/api/assessments/{assessment.id}/findings/{finding.id}/actions/{action.id}/status",
            data={"status": target, "expected_history_length": 1},
        )
        assert (response.status_code, response.json()["detail"]) == (400, findings.TERMINAL)
        assert _nothing_snapshot(db) == before
    response = http.post(
        f"/api/assessments/{assessment.id}/findings/{finding.id}/actions/{action.id}/update",
        data={"title": action.title, "expected_history_length": 1},
    )
    assert (response.status_code, response.json()["detail"]) == (400, findings.TERMINAL)
    page = http.get(f"/assessments/{assessment.id}/findings")
    assert "Closed and verified actions cannot be changed here." in page.text
    action_html = page.text[page.text.index(f'id="action-{action.id}"') :]
    assert f"actions/{action.id}/status" not in action_html
    response = http.post(
        f"/api/assessments/{assessment.id}/findings/{finding.id}/actions/{action.id}/status",
        data={"status": "banana", "expected_history_length": 1},
    )
    assert response.status_code == 422


def test_scenario_5_append_concurrency_and_unreadable_history(
    db, http, gate, monkeypatch
):
    """Scenario 5: stale tokens, CAS races and malformed history never overwrite prior entries."""
    assessment, _conclusion, finding, action = _created_finding(db, http, gate, monkeypatch)
    status_url = f"/api/assessments/{assessment.id}/findings/{finding.id}/actions/{action.id}/status"
    update_url = f"/api/assessments/{assessment.id}/findings/{finding.id}/actions/{action.id}/update"
    for url, payload in (
        (status_url, {"status": "in_progress", "expected_history_length": 0}),
        (update_url, {"title": "Changed", "expected_history_length": 0}),
    ):
        before = _nothing_snapshot(db)
        response = http.post(url, data=payload)
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
            fabricated = parsed + [{"actor": "other", "action": "updated", "timestamp": "race", "notes": None, "changes": {"title": {"from": "a", "to": "b"}}}]
            db.execute(
                text("UPDATE actions SET history_json = :history WHERE id = :id"),
                {"history": json.dumps(fabricated), "id": action.id},
            )
        return parsed

    monkeypatch.setattr(findings, "load_history", _race)
    response = http.post(
        status_url,
        data={"status": "in_progress", "expected_history_length": 1},
    )
    assert (response.status_code, response.json()["detail"]) == (409, findings.STALE_ACTION)
    db.expire_all()
    assert db.get(Action, action.id).history_json == original_raw
    monkeypatch.setattr(findings, "load_history", real_load)

    action.history_json = "not json"
    db.commit()
    before = _nothing_snapshot(db)
    response = http.post(
        status_url,
        data={"status": "in_progress", "expected_history_length": 1},
    )
    assert (response.status_code, response.json()["detail"]) == (400, findings.UNREADABLE_HISTORY)
    assert _nothing_snapshot(db) == before
    page = http.get(f"/assessments/{assessment.id}/findings")
    assert page.status_code == 200
    assert "History could not be read." in page.text


def test_scenario_6_details_update_and_validation(db, http, gate, monkeypatch):
    """Scenario 6: detail edits append exact changes and validation writes nothing."""
    assessment, _conclusion, finding, action = _created_finding(db, http, gate, monkeypatch)
    update_url = f"/api/assessments/{assessment.id}/findings/{finding.id}/actions/{action.id}/update"
    before_history = _history(db, action.id)
    response = http.post(
        update_url,
        data={
            "title": action.title,
            "owner": "Asha",
            "target_date": "2026-11-30",
            "expected_history_length": 1,
            "reviewer_name": "Priya",
        },
    )
    assert response.status_code == 200
    history = _history(db, action.id)
    assert history[:-1] == before_history
    assert history[-1]["action"] == "updated"
    assert history[-1]["changes"] == {
        "owner": {"from": None, "to": "Asha"},
        "target_date": {"from": None, "to": "2026-11-30"},
    }
    response = http.post(
        update_url,
        data={
            "title": action.title,
            "owner": "",
            "target_date": "2026-11-30",
            "expected_history_length": 2,
        },
    )
    assert response.status_code == 200
    history2 = _history(db, action.id)
    assert history2[:-1] == history
    assert history2[-1]["changes"] == {"owner": {"from": "Asha", "to": None}}
    assert db.get(Action, action.id).owner is None
    before = _nothing_snapshot(db)
    response = http.post(
        update_url,
        data={
            "title": action.title,
            "owner": "",
            "target_date": "2026-11-30",
            "expected_history_length": 3,
        },
    )
    assert (response.status_code, response.json()["detail"]) == (400, findings.NO_CHANGES)
    assert _nothing_snapshot(db) == before

    create_cases = [
        ({"title": ""}, 400, None),
        ({"description": ""}, 400, None),
        ({"action_title": ""}, 400, "An action needs a title."),
        ({"title": "x" * 256}, 400, findings.TITLE_TOO_LONG),
        ({"action_owner": "x" * 256}, 400, None),
        ({"notes": "x" * 2001}, 400, None),
        ({"priority": 5}, 400, "Priority must be between 1 and 4."),
        ({"severity": "severe"}, 422, None),
        ({"action_target_date": "2026-13-40"}, 422, None),
    ]
    second_a, second = _run_one(
        db, gate, monkeypatch, client_name="Validation", item=_item(REQS[0], "non_compliant")
    )
    _approve(http, db, second_a, second)
    for overrides, status_code, detail in create_cases:
        before = _nothing_snapshot(db)
        response = _create(http, second_a, second, **overrides)
        assert response.status_code == status_code
        if detail:
            assert response.json()["detail"] == detail
        assert _nothing_snapshot(db) == before
    response = http.post(update_url, data={"title": action.title})
    assert response.status_code == 422

    third_a, third = _run_one(
        db, gate, monkeypatch, client_name="Blank actor", item=_item(REQS[0], "non_compliant")
    )
    _approve(http, db, third_a, third)
    response = _create(http, third_a, third, notes="  ", reviewer_name="")
    assert response.status_code == 200
    created_action = db.query(Action).filter_by(finding_id=response.json()["finding_id"]).one()
    entry = _history(db, created_action.id)[0]
    assert entry["notes"] is None
    assert entry["actor"] == "consultant:Manager Review"


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
        "remediation_owner": "owner@example.com",
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


def test_scenario_7_page_render_reopen_escaping_and_single_card_read(
    db, http, gate, monkeypatch
):
    """Scenario 7: the page renders eligibility, provenance, history, escaping and reopen warnings."""
    assessment, conclusion = _run_one(
        db,
        gate,
        monkeypatch,
        item=_item(REQS[0], "non_compliant", action="Prefilled action"),
    )
    _approve(http, db, assessment, conclusion)
    calls = 0
    real_cards = findings.conclusion_review.conclusion_cards

    def _spy(*args, **kwargs):
        nonlocal calls
        calls += 1
        return real_cards(*args, **kwargs)

    monkeypatch.setattr(findings.conclusion_review, "conclusion_cards", _spy)
    page = http.get(f"/assessments/{assessment.id}/findings")
    assert page.status_code == 200
    assert calls == 1
    assert page.text.count("data-eligible-conclusion") == 1
    assert "Prefilled action" in page.text
    assert f'name="conclusion_version" value="{conclusion.version}"' in page.text
    workpaper_href = f"/assessments/{assessment.id}/workpaper#wp-dpdpa-{REQS[0]}"
    assert f'href="{workpaper_href}"' in page.text

    response = _create(
        http,
        assessment,
        conclusion,
        action_owner="<script>alert(1)</script>",
        notes="<script>alert(1)</script>",
    )
    assert response.status_code == 200
    finding_id = response.json()["finding_id"]
    page = http.get(f"/assessments/{assessment.id}/findings")
    assert page.text.count("data-finding-card") == 1
    assert "Created by Priya" in page.text
    assert "Workpaper trace →" in page.text
    assert page.text.count("data-action-row") == 1
    assert 'data-history-action="created"' in page.text
    assert "consultant:Priya" not in page.text
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in page.text
    assert "<script>alert(1)</script>" not in page.text

    assert _decide(http, assessment, conclusion, "reopen").status_code == 200
    page = http.get(f"/assessments/{assessment.id}/findings")
    assert 'data-source-approved="false"' in page.text
    assert "Source conclusion is no longer approved (now pending)" in page.text
    assert f'id="finding-{finding_id}"' in page.text

    empty = _seed(db, client_name="Empty")
    empty_page = http.get(f"/assessments/{empty.id}/findings")
    assert "No approved conclusions are waiting for a finding." in empty_page.text
    assert "No findings yet." in empty_page.text
    assert http.get("/assessments/unknown/findings").status_code == 404


def test_scenario_8_workpaper_linkage(db, http, gate, monkeypatch):
    """Scenario 8: Findings and workpaper entries link to one another without changing entry counts."""
    assessment, conclusion, finding, _action = _created_finding(db, http, gate, monkeypatch)
    wp = workpaper.build_workpaper(db, assessment)
    entries = [
        entry
        for section in wp.sections
        for entry in section.entries + section.excluded_entries
    ]
    linked = next(entry for entry in entries if entry.card.conclusion.id == conclusion.id)
    assert linked.findings == [
        {
            "finding_id": finding.id,
            "title": finding.title,
            "status": finding.status,
            "severity": finding.severity,
            "href": f"/assessments/{assessment.id}/findings#finding-{finding.id}",
        }
    ]
    assert all(entry.findings == [] for entry in entries if entry is not linked)

    workpaper_page = http.get(f"/assessments/{assessment.id}/workpaper")
    assert workpaper_page.status_code == 200
    assert "data-workpaper-finding" in workpaper_page.text
    assert f'href="/assessments/{assessment.id}/findings#finding-{finding.id}"' in workpaper_page.text
    assert workpaper_page.text.count("data-workpaper-entry") == len(entries)
    anchor = f"wp-dpdpa-{REQS[0]}"
    assert workpaper_page.text.count(f'id="{anchor}"') == 1
    findings_page = http.get(f"/assessments/{assessment.id}/findings")
    assert f'href="/assessments/{assessment.id}/workpaper#{anchor}"' in findings_page.text
    assert f'href="/assessments/{assessment.id}/findings"' in workpaper_page.text
    conclusions_page = http.get(f"/assessments/{assessment.id}/conclusions")
    assert f'href="/assessments/{assessment.id}/findings"' in conclusions_page.text


def test_scenario_9_legacy_coexistence_and_rerun(db, http):
    """Scenario 9: migrated histories remain intact and migration reruns skip consultant-operated rows."""
    assessment = _seed_legacy_assessment(
        db,
        company_name="Legacy",
        gap_items=[
            _gap_item_kwargs(requirement_id=REQS[0]),
            _gap_item_kwargs(
                requirement_id=REQS[1],
                requirement_title="Closed legacy requirement",
                remediation_status="closed",
                remediation_closed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            ),
        ],
    )
    stats = run_migration(db)
    assert (stats.findings, stats.actions) == (2, 2)
    page = http.get(f"/assessments/{assessment.id}/findings")
    assert page.text.count('data-finding-origin="migrated"') == 2
    assert page.text.count("Migrated from legacy remediation") >= 2
    assert page.text.count("Imported from legacy remediation") == 2

    open_action = db.query(Action).filter_by(status="open").one()
    closed_action = db.query(Action).filter_by(status="closed").one()
    open_finding = db.get(Finding, open_action.finding_id)
    closed_html = page.text[page.text.index(f'id="action-{closed_action.id}"') :]
    assert f"actions/{closed_action.id}/status" not in closed_html
    original_import = _history(db, open_action.id)[0].copy()
    response = http.post(
        f"/api/assessments/{assessment.id}/findings/{open_finding.id}/actions",
        data={"title": "Consultant action", "reviewer_name": "Priya"},
    )
    assert response.status_code == 200
    response = http.post(
        f"/api/assessments/{assessment.id}/findings/{open_finding.id}/actions/{open_action.id}/status",
        data={
            "status": "in_progress",
            "expected_history_length": 1,
            "reviewer_name": "Priya",
        },
    )
    assert response.status_code == 200
    history = _history(db, open_action.id)
    assert [entry["action"] for entry in history] == ["imported", "status_changed"]
    assert history[0] == original_import
    assert set(history[0]) == {"actor", "action", "timestamp", "notes"}
    before_count = db.query(Action).count()
    stats = run_migration(db)
    assert (stats.findings, stats.actions) == (0, 0)
    assert db.query(Action).count() == before_count


def test_scenario_10_provenance_and_no_conclusion_writes(db, http, gate, monkeypatch):
    """Scenario 10: Finding and Action mutations never alter Conclusions and audit only creation."""
    assessment, conclusion = _run_one(
        db, gate, monkeypatch, item=_item(REQS[0], "non_compliant")
    )
    _approve(http, db, assessment, conclusion)
    before = (
        conclusion.version,
        conclusion.updated_at,
        conclusion.outcome,
        conclusion.rationale,
        {row.id for row in _revisions(db, conclusion.id)},
    )
    created = _create(http, assessment, conclusion)
    assert created.status_code == 200
    finding = db.get(Finding, created.json()["finding_id"])
    first = db.query(Action).filter_by(finding_id=finding.id).one()
    assert http.post(
        f"/api/assessments/{assessment.id}/findings/{finding.id}/actions",
        data={"title": "Second", "reviewer_name": "Priya"},
    ).status_code == 200
    assert http.post(
        f"/api/assessments/{assessment.id}/findings/{finding.id}/actions/{first.id}/status",
        data={"status": "in_progress", "expected_history_length": 1},
    ).status_code == 200
    assert http.post(
        f"/api/assessments/{assessment.id}/findings/{finding.id}/actions/{first.id}/update",
        data={"title": first.title, "owner": "Asha", "expected_history_length": 2},
    ).status_code == 200
    db.refresh(conclusion)
    after = (
        conclusion.version,
        conclusion.updated_at,
        conclusion.outcome,
        conclusion.rationale,
        {row.id for row in _revisions(db, conclusion.id)},
    )
    assert after == before
    assert db.query(AuditEvent).filter_by(entity_type="finding").count() == 1


def test_scenario_11_structural_guards():
    """Scenario 11: route sets, signatures and source guards preserve individual operation boundaries."""
    expected = {
        ("GET", "/assessments/{assessment_id}/findings"),
        ("POST", "/api/assessments/{assessment_id}/findings"),
        ("POST", "/api/assessments/{assessment_id}/findings/{finding_id}/actions"),
        ("POST", "/api/assessments/{assessment_id}/findings/{finding_id}/actions/{action_id}/status"),
        ("POST", "/api/assessments/{assessment_id}/findings/{finding_id}/actions/{action_id}/update"),
    }
    actual = {
        (method, route.path)
        for route in app.routes
        if "/findings" in route.path
        for method in route.methods
        if method in {"GET", "POST", "PATCH", "PUT", "DELETE"}
    }
    assert actual == expected
    signature = inspect.signature(findings.create_finding)
    assert "conclusion_id" in signature.parameters
    assert all("list" not in str(parameter.annotation) for parameter in signature.parameters.values())

    paths = [
        REPO_ROOT / "app/services/findings.py",
        REPO_ROOT / "app/routers/findings.py",
        REPO_ROOT / "app/schemas/findings.py",
        REPO_ROOT / "app/templates/pages/findings.html",
        REPO_ROOT / "app/templates/components/finding_card.html",
    ]
    source = "\n".join(path.read_text() for path in paths)
    assert re.search(
        r'select all|create all|all conclusions|type="checkbox"|\bmultiple\b|\|\s*safe\b',
        source,
        re.IGNORECASE,
    ) is None
    service_source = (REPO_ROOT / "app/services/findings.py").read_text()
    router_source = (REPO_ROOT / "app/routers/findings.py").read_text()
    assert "LEGACY_BULK" in service_source
    assert "Legacy bulk approval, not individually reviewed" in (
        REPO_ROOT / "app/templates/components/finding_card.html"
    ).read_text()
    assert "delete" not in service_source.lower()
    assert "delete" not in router_source.lower()
    assert ".commit(" not in service_source
    assert "swap_conclusion" not in service_source
    assert "ConclusionRevision(" not in service_source
    from app.routers import web

    assert ".commit(" not in inspect.getsource(web.findings_page)


def test_scenario_12_existing_contract_surfaces_remain_registered():
    """Scenario 12: existing conclusion and workpaper route contracts remain unchanged."""
    conclusion_routes = {
        (method, route.path)
        for route in app.routes
        if "/conclusions" in route.path
        for method in route.methods
        if method in {"GET", "POST", "PATCH", "PUT", "DELETE"}
    }
    assert conclusion_routes == {
        ("GET", "/assessments/{assessment_id}/conclusions"),
        ("POST", "/api/assessments/{assessment_id}/conclusions/{conclusion_id}/approve"),
        ("POST", "/api/assessments/{assessment_id}/conclusions/{conclusion_id}/edit"),
        ("POST", "/api/assessments/{assessment_id}/conclusions/{conclusion_id}/reject"),
        ("POST", "/api/assessments/{assessment_id}/conclusions/{conclusion_id}/reopen"),
    }
    workpaper_routes = {
        (method, route.path)
        for route in app.routes
        if "/workpaper" in route.path
        for method in route.methods
        if method in {"GET", "POST", "PATCH", "PUT", "DELETE"}
    }
    assert workpaper_routes == {("GET", "/assessments/{assessment_id}/workpaper")}
