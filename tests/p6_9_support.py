"""Shared fixtures and seed helpers for the P6-9 contract tests (SoA, roadmap, prior period).

Kept at tests/ root (like report_period_helper.py) so the tests/support and tests/fixtures
guards stay untouched. Test modules import the fixtures by name. No network, no LLM.
"""

from __future__ import annotations

import copy
import importlib
import json
from datetime import date, datetime, timezone
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.config import settings
from app.database import get_db
from app.frameworks.registry import FrameworkRegistry
from app.main import app
from app.models.assessment import Assessment
from app.models.client import Client
from app.models.conclusion import Conclusion, ConclusionRevision
from app.models.engagement import Engagement
from app.models.questionnaire import QuestionnaireResponse
from app.services import approved_report, report_basis

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXED_GENERATED_AT = datetime(2026, 9, 28, 10, 0, tzinfo=timezone.utc)
PERIOD_1 = {"period_start": date(2026, 1, 1), "period_end": date(2026, 3, 31), "evidence_cutoff": date(2026, 4, 15)}
PERIOD_2 = {"period_start": date(2026, 4, 1), "period_end": date(2026, 6, 30), "evidence_cutoff": date(2026, 7, 15)}
FAKE_PDF = b"%PDF-1.7\n% P6-9 stub render\n"


def module(name: str):
    """Import a P6-9 module lazily so each test fails on its own before implementation."""
    return importlib.import_module(name)


@pytest.fixture(scope="module", autouse=True)
def _register_frameworks():
    from app.main import _register_frameworks as register

    register()


@pytest.fixture()
def db_path(tmp_path):
    path = tmp_path / "p6-9.sqlite3"
    config = Config(str(REPO_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{path}")
    command.upgrade(config, "head")
    return path


@pytest.fixture()
def db(db_path):
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _record):  # pragma: no cover
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


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
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _no_llm(monkeypatch):
    from app.services import llm_client

    def _refuse(*_args, **_kwargs):
        raise AssertionError("P6-9 tests must never call an LLM")

    monkeypatch.setattr(llm_client, "call_llm", _refuse)


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


@pytest.fixture()
def stub_render(monkeypatch):
    """Board report versions without WeasyPrint: the comparison reads sidecars, never the PDF."""
    board = module("app.services.board_report")
    monkeypatch.setattr(board, "render_pdf", lambda _document: FAKE_PDF)
    return board


def control_ids(framework_id: str) -> list[str]:
    return [control.id for control in FrameworkRegistry.get_all_controls(framework_id)]


def new_engagement(db, company="Acme Analytics Pvt Ltd"):
    client = db.query(Client).filter_by(name=company).first()
    if client is None:
        client = Client(name=company, industry="Technology", size="medium")
        db.add(client)
        db.flush()
    engagement = Engagement(client_id=client.id, name="Annual security review", status="active")
    db.add(engagement)
    db.flush()
    return engagement


def seed(db, engagement, *, frameworks, applicable, period=PERIOD_2, company="Acme Analytics Pvt Ltd"):
    assessment = Assessment(
        company_name=company,
        industry="Technology",
        company_size="medium",
        selected_frameworks=json.dumps(frameworks),
        engagement_id=engagement.id if engagement is not None else None,
        applicable_requirements=json.dumps(applicable),
    )
    db.add(assessment)
    db.flush()
    report_basis.update_report_basis(
        db, assessment, **period,
        prepared_by="Priya Sharma", reviewed_by="Ravi Menon", actor="consultant:Seed",
    )
    db.add(QuestionnaireResponse(assessment_id=assessment.id, question_id="Q1", answer="fully_implemented"))
    db.commit()
    return assessment


def item(requirement_id, status="partially_compliant", risk="medium"):
    return {
        "requirement_id": requirement_id,
        "compliance_status": status,
        "current_state": f"Rationale for {requirement_id}",
        "gap_description": "Gap exists" if status != "compliant" else "",
        "risk_level": risk,
        "remediation_action": "Fix the gap" if status != "compliant" else "",
        "remediation_priority": 2,
        "remediation_effort": "medium",
        "timeline_weeks": 6,
        "maturity_level": 2,
        "root_cause_category": "process",
        "evidence_quote": "",
        "needs_review": False,
    }


def analyse(monkeypatch, gate, db, assessment, per_framework):
    """Run the real analysis route with both analyzer seams faked (never a network call)."""
    from app.routers import analysis

    def _single(**_kwargs):
        (items,) = per_framework.values()
        return {"parsed": {"executive_summary": "Synthetic", "assessments": copy.deepcopy(items)}, "raw": "{}"}

    def _multi(**_kwargs):
        return {
            "frameworks": {
                framework_id: {
                    "parsed": {"executive_summary": "Synthetic", "assessments": copy.deepcopy(items)},
                    "raw": "{}",
                }
                for framework_id, items in per_framework.items()
            },
            "synthesis": None,
            "total_usage": {},
        }

    monkeypatch.setattr(analysis, "run_gap_analysis", _single)
    monkeypatch.setattr(analysis, "run_multi_framework_analysis", _multi)
    gate.trigger_analysis(assessment.id, db)
    db.expire_all()
    return {
        (row.framework_id, row.requirement_id): row
        for row in db.query(Conclusion).filter_by(assessment_id=assessment.id).all()
    }


def decide(db, conclusion, action="approved", **edits):
    """Consultant decision written directly (fixture data, not the gate under test)."""
    previous = conclusion.outcome
    for field, value in edits.items():
        setattr(conclusion, field, value)
    conclusion.version += 1
    db.add(
        ConclusionRevision(
            conclusion_id=conclusion.id,
            actor="consultant:Priya",
            action=action,
            previous_outcome=previous,
            previous_rationale=conclusion.rationale,
            citations_json=None,
            created_at=datetime.now(timezone.utc),
        )
    )


def approve_all(db, conclusions, *, skip=()):
    for key, conclusion in conclusions.items():
        if key not in skip:
            decide(db, conclusion)
    db.commit()


def finding(http, assessment, conclusion, *, title, severity="high", priority=1, action="Fix it", owner="Anita Rao", target="2026-11-30"):
    response = http.post(
        f"/api/assessments/{assessment.id}/findings",
        data={
            "conclusion_id": conclusion.id,
            "conclusion_version": conclusion.version,
            "title": title,
            "description": f"Description of {title}",
            "severity": severity,
            "priority": priority,
            "action_title": action,
            "action_owner": owner,
            "action_target_date": target,
            "reviewer_name": "Priya",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["finding_id"]


def release(db, assessment):
    approved_report.record_release(db, assessment, actor="consultant:Priya")
    db.commit()
    db.expire_all()


def released_assessment(db, http, gate, monkeypatch, engagement, *, frameworks, outcomes, period=PERIOD_2, company="Acme Analytics Pvt Ltd"):
    """Seed, analyse, approve every conclusion and release. `outcomes` maps (framework, id) -> (status, risk)."""
    per_framework: dict[str, list] = {}
    for (framework_id, requirement_id), (status, risk) in outcomes.items():
        per_framework.setdefault(framework_id, []).append(item(requirement_id, status, risk))
    applicable = [requirement_id for (_framework, requirement_id) in outcomes]
    assessment = seed(db, engagement, frameworks=list(frameworks), applicable=applicable, period=period, company=company)
    conclusions = analyse(monkeypatch, gate, db, assessment, per_framework)
    approve_all(db, conclusions)
    return assessment, conclusions


def build(db, assessment, *, snapshot_id="00000000-0000-4000-8000-000000000009", version_label="v1"):
    return module("app.services.board_report").build_document(
        db, assessment, snapshot_id=snapshot_id, version_label=version_label, generated_at=FIXED_GENERATED_AT,
    )


def generate_board(http, assessment):
    response = http.post(
        f"/api/assessments/{assessment.id}/snapshots",
        data={"type": "board_report", "reviewer_name": "Priya"},
    )
    assert response.status_code == 200, response.text
    return response.json()["snapshot_id"]


def issue(http, assessment, snapshot_id):
    response = http.post(
        f"/api/assessments/{assessment.id}/snapshots/{snapshot_id}/issue",
        data={"reviewer_name": "Priya"},
    )
    assert response.status_code == 200, response.text


def latest_rowid_event(db, action):
    return db.execute(
        text("SELECT metadata_json FROM audit_events WHERE action = :a ORDER BY rowid DESC LIMIT 1"),
        {"a": action},
    ).scalar_one_or_none()
