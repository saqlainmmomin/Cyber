"""Contract tests for P6-6 report foundations.

Handoff: tasks/handoffs/2026-09-28-p6-6-report-foundations.md. Plan:
docs/plans/2026-09-25-001-grounded-analysis-and-deliverables-plan.md, Part D (D0) and
decision D-P6-G. These tests were written before the implementation; they fail on
`main` only because the P6-6 code does not exist yet. No network.
"""

from __future__ import annotations

import copy
import hashlib
import importlib
import io
import json
import re
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import unquote

import pdfplumber
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
from app.models.audit_event import AuditEvent
from app.models.client import Client
from app.models.conclusion import Conclusion, ConclusionRevision
from app.models.engagement import Engagement
from app.models.questionnaire import QuestionnaireResponse
from app.models.report_snapshot import ReportSnapshot
from app.services import approved_report, conclusion_review, report_snapshots
from app.utils import pdf_export

REPO_ROOT = Path(__file__).resolve().parents[1]
ALEMBIC_HEAD = "b7d41c9e2a63"  # P6-6 added no migration (D-P6-6-A); P6-8 V3-A adds 5e9a2c7d4b18, Yozora backend b7d41c9e2a63
PERIOD = {
    "period_start": date(2026, 4, 1),
    "period_end": date(2026, 6, 30),
    "evidence_cutoff": date(2026, 7, 15),
}
PERIOD_FORM = {
    "period_start": "2026-04-01",
    "period_end": "2026-06-30",
    "evidence_cutoff": "2026-07-15",
}
PERIOD_TEXT = "Assessment period: 01 Apr 2026 to 30 Jun 2026"
CUTOFF_TEXT = "Evidence cut-off: 15 Jul 2026"
PERIOD_REQUIRED = (
    "Record the assessment period and evidence cut-off before approving conclusions."
)
PERIOD_LOCKED = (
    "The assessment period and evidence cut-off are locked while any conclusion is "
    "approved. Reopen the approved conclusions to change them."
)
# Copy that must never appear in a report whose frameworks are all standards
# (ISO 27001 / NIST CSF / PCI-DSS): DPDPA terms, legal-regime advice, maturity model.
NON_LEGAL_FORBIDDEN = (
    "dpdpa",
    "digital personal data protection",
    "data principal",
    "data fiduciary",
    "schedule to the",
    "legal counsel",
    "legal advice",
    "privacy practice",
    "privacy professional",
    "cmmi",
    "maturity model",
)
STALE_METHODOLOGY = (
    "grc response scale",
    "five-option scale",
    "questionnaire responses use",
    "maturity model",
    "cmmi",
    "m3 (defined)",
    "planned: control is not yet in place",
    "questionnaire-based",
    "structured assessment interview",
)


def _rb():
    """app.services.report_basis, imported lazily so each test fails on its own."""
    return importlib.import_module("app.services.report_basis")


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
    path = tmp_path / "p6-6.sqlite3"
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
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _no_llm(monkeypatch):
    from app.services import llm_client

    def _refuse(*_args, **_kwargs):
        raise AssertionError("P6-6 tests must never call an LLM")

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


def _ids(framework_id: str, count: int | None = None) -> list[str]:
    ids = [control.id for control in FrameworkRegistry.get_all_controls(framework_id)]
    return ids if count is None else ids[:count]


def _seed(
    db,
    *,
    frameworks,
    applicable,
    period: bool = True,
    company="Acme Corp",
    engagement=None,
    description=None,
    prepared_by=None,
    reviewed_by=None,
):
    if engagement is None:
        client = Client(name=company, industry="Technology", size="medium")
        db.add(client)
        db.flush()
        engagement = Engagement(client_id=client.id, name=f"{company} gap", status="active")
        db.add(engagement)
        db.flush()
    assessment = Assessment(
        company_name=company,
        industry="Technology",
        company_size="medium",
        description=description,
        selected_frameworks=json.dumps(frameworks),
        engagement_id=engagement.id,
        applicable_requirements=json.dumps(applicable),
    )
    db.add(assessment)
    db.flush()
    if period or prepared_by is not None or reviewed_by is not None:
        dates = PERIOD if period else dict.fromkeys(PERIOD)
        _rb().update_report_basis(
            db,
            assessment,
            **dates,
            prepared_by=prepared_by,
            reviewed_by=reviewed_by,
            actor="consultant:Seed",
        )
    db.add(
        QuestionnaireResponse(
            assessment_id=assessment.id, question_id="Q1", answer="fully_implemented"
        )
    )
    db.commit()
    return assessment


def _item(requirement_id, status="partially_compliant", risk="medium"):
    return {
        "requirement_id": requirement_id,
        "compliance_status": status,
        "current_state": "Current state",
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


def _analyse(monkeypatch, gate, db, assessment, per_framework: dict[str, list[dict]]):
    """Run the real analysis route with both analyzer seams faked (never a network call)."""
    from app.routers import analysis

    def _single(**_kwargs):
        (items,) = per_framework.values()
        return {
            "parsed": {"executive_summary": "Synthetic summary", "assessments": copy.deepcopy(items)},
            "raw": "{}",
        }

    def _multi(**_kwargs):
        return {
            "frameworks": {
                framework_id: {
                    "parsed": {
                        "executive_summary": f"{framework_id} summary",
                        "assessments": copy.deepcopy(items),
                    },
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
    return (
        db.query(Conclusion)
        .filter_by(assessment_id=assessment.id)
        .order_by(Conclusion.framework_id, Conclusion.requirement_id)
        .all()
    )


def _capture_citations(db, conclusion):
    proposal = (
        db.query(ConclusionRevision)
        .filter_by(conclusion_id=conclusion.id, action="proposed")
        .order_by(ConclusionRevision.created_at.desc(), text("conclusion_revisions.rowid DESC"))
        .first()
    )
    proposal.citations_json = "[]"
    db.commit()


def _post_decision(http, assessment, conclusion, route, **extra):
    payload = {"expected_version": conclusion.version, "reviewer_name": "Priya"}
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
    payload.update(extra)
    return http.post(
        f"/api/assessments/{assessment.id}/conclusions/{conclusion.id}/{route}",
        data=payload,
    )


def _approve_http(http, db, assessment, conclusion):
    _capture_citations(db, conclusion)
    db.refresh(conclusion)
    response = _post_decision(http, assessment, conclusion, "approve")
    assert response.status_code == 200, response.text
    db.refresh(conclusion)
    return response


def _approve_all_direct(db, assessment):
    """Bulk consultant approvals written directly (fixture data, not the gate under test)."""
    for conclusion in db.query(Conclusion).filter_by(assessment_id=assessment.id).all():
        conclusion.version += 1
        db.add(
            ConclusionRevision(
                conclusion_id=conclusion.id,
                actor="consultant:Priya",
                action="approved",
                previous_outcome=conclusion.outcome,
                previous_rationale=conclusion.rationale,
                citations_json=None,
                created_at=datetime.now(timezone.utc),
            )
        )
    db.commit()


def _release(db, assessment):
    approved_report.record_release(db, assessment, actor="consultant:Priya")
    db.commit()


def _finding_with_action(http, assessment, conclusion, *, title, owner, target, action):
    response = http.post(
        f"/api/assessments/{assessment.id}/findings",
        data={
            "conclusion_id": conclusion.id,
            "conclusion_version": conclusion.version,
            "title": title,
            "description": "Finding description",
            "severity": "high",
            "priority": 1,
            "action_title": action,
            "action_owner": owner,
            "action_target_date": target,
            "reviewer_name": "Priya",
        },
    )
    assert response.status_code == 200, response.text
    return response


def _pdf_pages(content: bytes) -> list[str]:
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        return [" ".join((page.extract_text() or "").split()) for page in pdf.pages]


def _pdf_text(content: bytes) -> str:
    return " ".join(_pdf_pages(content))


def _board_pdf(http, assessment) -> bytes:
    response = http.get(f"/api/assessments/{assessment.id}/report/pdf")
    assert response.status_code == 200, response.text
    return response.content


def _released_board_assessment(db, http, gate, monkeypatch, *, frameworks, per_framework, **seed):
    applicable = [item["requirement_id"] for items in per_framework.values() for item in items]
    assessment = _seed(db, frameworks=frameworks, applicable=applicable, **seed)
    _analyse(monkeypatch, gate, db, assessment, per_framework)
    _approve_all_direct(db, assessment)
    _release(db, assessment)
    return assessment


# ---------------------------------------------------------------------------
# 1. Model and migration
# ---------------------------------------------------------------------------


def test_scenario_1_basis_is_an_append_only_audit_trail(db):
    """Scenario 1 (D-P6-6-A): no schema change; the basis is the latest audit event's "after"."""
    rb = _rb()
    columns = {column.name for column in Assessment.__table__.columns}
    assert not {"period_start", "period_end", "evidence_cutoff"} & columns
    heads = subprocess.run(
        [sys.executable, "-m", "alembic", "heads"],
        cwd=REPO_ROOT, check=True, capture_output=True, text=True,
    ).stdout.strip()
    assert heads == f"{ALEMBIC_HEAD} (head)"

    assessment = _seed(db, frameworks=["dpdpa"], applicable=_ids("dpdpa", 1), period=False)
    assert rb.current_basis(db, assessment) == rb.EMPTY_BASIS
    assert rb.current_basis(None, assessment) == rb.EMPTY_BASIS
    assert rb.basis_for(None) == rb.EMPTY_BASIS
    for cutoff in (date(2026, 7, 15), date(2026, 7, 20)):
        rb.update_report_basis(
            db, assessment, **{**PERIOD, "evidence_cutoff": cutoff},
            prepared_by="Priya", reviewed_by=None, actor="consultant:Priya",
        )
        db.commit()
    events = (
        db.query(AuditEvent)
        .filter_by(action="assessment.report_basis_updated", entity_type="assessment", entity_id=assessment.id)
        .all()
    )
    assert len(events) == 2
    assert json.loads(events[0].metadata_json)["after"]["evidence_cutoff"] == "2026-07-15"
    assert json.loads(events[1].metadata_json)["before"]["evidence_cutoff"] == "2026-07-15"
    assert rb.current_basis(db, assessment).evidence_cutoff == date(2026, 7, 20)
    assert rb.basis_for(assessment).evidence_cutoff == date(2026, 7, 20)

    # A malformed latest event reads as "not recorded", never as a crash or a guess.
    events[1].metadata_json = "{not json"
    db.commit()
    assert rb.current_basis(db, assessment) == rb.EMPTY_BASIS


# ---------------------------------------------------------------------------
# 2-3. Report basis service and route
# ---------------------------------------------------------------------------


def test_scenario_2_report_basis_service_rules(db):
    """Scenario 2: validation, name cleaning, labels, audit event and no-op saves."""
    rb = _rb()
    assessment = _seed(db, frameworks=["dpdpa"], applicable=_ids("dpdpa", 1), period=False)

    empty = rb.current_basis(db, assessment)
    assert empty.period_recorded is False
    assert empty.period_label == "not recorded" and empty.cutoff_label == "not recorded"
    assert rb.approval_blocker(db, assessment) == PERIOD_REQUIRED
    assert rb.basis_for(None).period_label == "not recorded"

    def _update(**overrides):
        values = {
            **PERIOD,
            "prepared_by": None,
            "reviewed_by": None,
            "actor": "consultant:Priya",
            **overrides,
        }
        return rb.update_report_basis(db, assessment, **values)

    for overrides, message in (
        ({"evidence_cutoff": None}, rb.PERIOD_INCOMPLETE_MESSAGE),
        ({"period_end": date(2026, 3, 31)}, rb.PERIOD_ORDER_MESSAGE),
        ({"evidence_cutoff": date(2026, 3, 31)}, rb.CUTOFF_ORDER_MESSAGE),
    ):
        with pytest.raises(rb.ReportBasisError) as excinfo:
            _update(**overrides)
        assert excinfo.value.message == message
        assert excinfo.value.status_code == 400
    assert rb.PERIOD_INCOMPLETE_MESSAGE == (
        "Enter the period start, period end and evidence cut-off together, or leave all three blank."
    )
    assert rb.PERIOD_ORDER_MESSAGE == "The assessment period must end on or after its start date."
    assert rb.CUTOFF_ORDER_MESSAGE == (
        "The evidence cut-off must be on or after the start of the assessment period."
    )
    assert db.query(AuditEvent).filter_by(action=rb.AUDIT_ACTION).count() == 0

    basis = _update(prepared_by="  Priya\n  Sharma  ", reviewed_by="R" * 250)
    db.commit()
    stored = rb.current_basis(db, assessment)
    assert stored == basis
    assert stored.period_start == date(2026, 4, 1)
    assert stored.period_end == date(2026, 6, 30)
    assert stored.evidence_cutoff == date(2026, 7, 15)
    assert stored.prepared_by == "Priya Sharma"
    assert stored.reviewed_by == "R" * 200
    assert basis.period_recorded is True
    assert basis.period_label == "01 Apr 2026 to 30 Jun 2026"
    assert basis.cutoff_label == "15 Jul 2026"
    assert rb.approval_blocker(db, assessment) is None

    events = db.query(AuditEvent).filter_by(action="assessment.report_basis_updated").all()
    assert len(events) == 1
    assert events[0].entity_type == "assessment" and events[0].entity_id == assessment.id
    assert events[0].actor == "consultant:Priya"
    metadata = json.loads(events[0].metadata_json)
    assert metadata["before"]["period_start"] is None
    assert metadata["after"] == {
        "period_start": "2026-04-01",
        "period_end": "2026-06-30",
        "evidence_cutoff": "2026-07-15",
        "prepared_by": "Priya Sharma",
        "reviewed_by": "R" * 200,
    }

    # Saving the same values again writes nothing.
    _update(prepared_by="Priya Sharma", reviewed_by="R" * 200)
    db.commit()
    assert db.query(AuditEvent).filter_by(action=rb.AUDIT_ACTION).count() == 1

    # All three blank clears the period while nothing is approved.
    _update(period_start=None, period_end=None, evidence_cutoff=None)
    db.commit()
    cleared = rb.current_basis(db, assessment)
    assert cleared.period_start is None and cleared.evidence_cutoff is None
    assert cleared.period_recorded is False


def test_scenario_3_route_saves_and_rejects(db, http):
    """Scenario 3: POST /api/assessments/{id}/report-basis."""
    assessment = _seed(db, frameworks=["dpdpa"], applicable=_ids("dpdpa", 1), period=False)
    url = f"/api/assessments/{assessment.id}/report-basis"

    bad = http.post(url, data={**PERIOD_FORM, "period_end": "30/06/2026"})
    assert bad.status_code == 400
    assert bad.json()["detail"] == "Dates must be in YYYY-MM-DD format."
    assert bad.headers["X-Toast-Type"] == "error"

    missing = http.post("/api/assessments/does-not-exist/report-basis", data=PERIOD_FORM)
    assert missing.status_code == 404

    saved = http.post(
        url,
        data={**PERIOD_FORM, "prepared_by": "Priya Sharma", "reviewed_by": "", "reviewer_name": "Priya"},
    )
    assert saved.status_code == 200, saved.text
    assert saved.json() == {
        "status": "saved",
        "period_start": "2026-04-01",
        "period_end": "2026-06-30",
        "evidence_cutoff": "2026-07-15",
        "prepared_by": "Priya Sharma",
        "reviewed_by": None,
    }
    assert saved.headers["HX-Redirect"] == f"/assessments/{assessment.id}/conclusions"
    assert saved.headers["X-Toast-Type"] == "success"
    db.expire_all()
    assert _rb().current_basis(db, assessment).period_end == date(2026, 6, 30)
    event_row = db.query(AuditEvent).filter_by(action="assessment.report_basis_updated").one()
    assert event_row.actor == "consultant:Priya"


# ---------------------------------------------------------------------------
# 4-5. Approval gate (D-P6-G)
# ---------------------------------------------------------------------------


def test_scenario_4_approval_gate_blocks_approve_and_edit(db, http, gate, monkeypatch):
    """Scenario 4: approve and edit are refused until period and cut-off are recorded; reject is not."""
    ids = _ids("dpdpa", 3)
    assessment = _seed(db, frameworks=["dpdpa"], applicable=ids, period=False)
    conclusions = _analyse(
        monkeypatch, gate, db, assessment, {"dpdpa": [_item(rid, "non_compliant") for rid in ids]}
    )
    first, second, third = conclusions
    for conclusion in conclusions:
        _capture_citations(db, conclusion)
        db.refresh(conclusion)

    revisions_before = db.query(ConclusionRevision).count()
    for conclusion, route in ((first, "approve"), (second, "edit")):
        version = conclusion.version
        response = _post_decision(http, assessment, conclusion, route)
        assert response.status_code == 400
        assert response.json()["detail"] == PERIOD_REQUIRED
        db.refresh(conclusion)
        assert conclusion.version == version
    assert db.query(ConclusionRevision).count() == revisions_before

    with pytest.raises(conclusion_review.InvalidDecision) as excinfo:
        conclusion_review.decide(
            db,
            assessment_id=assessment.id,
            conclusion_id=first.id,
            action="approved",
            expected_version=first.version,
            actor="consultant:Priya",
        )
    assert excinfo.value.message == PERIOD_REQUIRED
    db.rollback()

    rejected = _post_decision(http, assessment, third, "reject")
    assert rejected.status_code == 200

    cards = {card.conclusion.id: card for card in conclusion_review.conclusion_cards(db, assessment.id)}
    assert cards[first.id].approval_blocker == PERIOD_REQUIRED

    page = http.get(f"/assessments/{assessment.id}/conclusions")
    assert page.status_code == 200
    assert "data-report-basis-panel" in page.text
    assert f'hx-post="/api/assessments/{assessment.id}/report-basis"' in page.text
    assert PERIOD_REQUIRED in page.text

    saved = http.post(f"/api/assessments/{assessment.id}/report-basis", data=PERIOD_FORM)
    assert saved.status_code == 200
    db.expire_all()
    first = db.get(Conclusion, first.id)
    approved = _post_decision(http, assessment, first, "approve")
    assert approved.status_code == 200, approved.text
    cards = {card.conclusion.id: card for card in conclusion_review.conclusion_cards(db, assessment.id)}
    assert cards[second.id].approval_blocker != PERIOD_REQUIRED


def test_scenario_5_period_locks_while_any_conclusion_is_approved(db, http, gate, monkeypatch):
    """Scenario 5: the period cannot change under an approved conclusion; sign-off can."""
    rb = _rb()
    ids = _ids("dpdpa", 1)
    assessment = _seed(db, frameworks=["dpdpa"], applicable=ids)
    (conclusion,) = _analyse(monkeypatch, gate, db, assessment, {"dpdpa": [_item(ids[0])]})
    assert rb.period_locked(db, assessment) is False
    _approve_http(http, db, assessment, conclusion)
    assert rb.period_locked(db, assessment) is True

    url = f"/api/assessments/{assessment.id}/report-basis"
    moved = http.post(url, data={**PERIOD_FORM, "evidence_cutoff": "2026-07-31"})
    assert moved.status_code == 400
    assert moved.json()["detail"] == PERIOD_LOCKED
    cleared = http.post(url, data={"period_start": "", "period_end": "", "evidence_cutoff": ""})
    assert cleared.status_code == 400 and cleared.json()["detail"] == PERIOD_LOCKED

    signed = http.post(url, data={**PERIOD_FORM, "prepared_by": "Priya", "reviewed_by": "Ravi"})
    assert signed.status_code == 200
    db.expire_all()
    assert rb.current_basis(db, assessment).reviewed_by == "Ravi"

    page = http.get(f"/assessments/{assessment.id}/conclusions")
    assert 'data-period-locked="yes"' in page.text

    conclusion = db.get(Conclusion, conclusion.id)
    reopened = _post_decision(http, assessment, conclusion, "reopen")
    assert reopened.status_code == 200
    moved = http.post(url, data={**PERIOD_FORM, "evidence_cutoff": "2026-07-31"})
    assert moved.status_code == 200
    db.expire_all()
    assert rb.current_basis(db, assessment).evidence_cutoff == date(2026, 7, 31)


# ---------------------------------------------------------------------------
# 6-10. Board PDF defects
# ---------------------------------------------------------------------------


def test_scenario_6_board_pdf_prints_period_cutoff_and_labelled_render_date(
    db, http, gate, monkeypatch
):
    """Scenario 6 (D0 #1, #2): cover and scope page carry period, cut-off and a labelled render date."""
    ids = _ids("dpdpa", 2)
    assessment = _released_board_assessment(
        db, http, gate, monkeypatch,
        frameworks=["dpdpa"],
        per_framework={"dpdpa": [_item(ids[0], "non_compliant", "high"), _item(ids[1], "compliant")]},
    )
    pages = _pdf_pages(_board_pdf(http, assessment))
    today = datetime.now(timezone.utc).strftime("%d %b %Y")
    assert PERIOD_TEXT in pages[0] and CUTOFF_TEXT in pages[0]
    assert f"Report generated: {today}" in pages[0]
    scope_page = next(page for page in pages if "Nature of Assessment" in page)
    assert PERIOD_TEXT in scope_page and CUTOFF_TEXT in scope_page
    assert f"Report generated: {today}" in scope_page
    full = " ".join(pages)
    assert "Assessment Date" not in full
    assert datetime.now(timezone.utc).strftime("%B %d, %Y") not in full

    # A PDF rendered without an assessment period says so instead of inventing a date.
    legacy = _released_board_assessment(
        db, http, gate, monkeypatch,
        frameworks=["dpdpa"],
        per_framework={"dpdpa": [_item(ids[0], "non_compliant", "high")]},
        period=False,
        company="Legacy Co",
    )
    legacy_first = _pdf_pages(_board_pdf(http, legacy))[0]
    assert "Assessment period: not recorded" in legacy_first
    assert "Evidence cut-off: not recorded" in legacy_first


def test_scenario_7_single_consistent_gaps_count(db, http, gate, monkeypatch):
    """Scenario 7 (D0 #4): cover and appendix report the same gaps count (non + partial)."""
    ids = _ids("dpdpa", 5)
    assessment = _released_board_assessment(
        db, http, gate, monkeypatch,
        frameworks=["dpdpa"],
        per_framework={
            "dpdpa": [
                _item(ids[0], "non_compliant", "high"),
                _item(ids[1], "partially_compliant", "medium"),
                _item(ids[2], "compliant", "low"),
                _item(ids[3], "insufficient_evidence", "medium"),
                _item(ids[4], "not_applicable", "low"),
            ]
        },
    )
    text_value = _pdf_text(_board_pdf(http, assessment))
    counts = re.findall(r"(\d+) gaps identified", text_value)
    assert len(counts) >= 2
    assert set(counts) == {"2"}
    assert pdf_export.count_gaps(
        [type("Row", (), {"compliance_status": status})() for status in (
            "non_compliant", "partially_compliant", "compliant", "insufficient_evidence",
            "not_applicable",
        )]
    ) == 2
    assert pdf_export.GAP_STATUSES == ("non_compliant", "partially_compliant")


def test_scenario_8_methodology_is_framework_correct(db, http, gate, monkeypatch):
    """Scenario 8 (D0 #5): no questionnaire scale or CMMI; approved-conclusion basis and real weights."""
    iso = _ids("iso27001", 2)
    dpdpa = _ids("dpdpa", 1)
    assessment = _released_board_assessment(
        db, http, gate, monkeypatch,
        frameworks=["dpdpa", "iso27001"],
        per_framework={
            "dpdpa": [_item(dpdpa[0], "non_compliant", "high")],
            "iso27001": [_item(iso[0], "partially_compliant"), _item(iso[1], "compliant")],
        },
    )
    pages = _pdf_pages(_board_pdf(http, assessment))
    methodology = next(page for page in pages if "Assessment Methodology" in page)
    lowered = " ".join(pages).lower()
    for phrase in STALE_METHODOLOGY:
        assert phrase not in lowered, phrase
    assert "Basis of Assessment:" in methodology
    assert "individually approved" in methodology
    assert "Scoring Basis:" in methodology
    assert "Insufficient Evidence" in methodology
    assert "Organizational Controls 35%" in methodology
    assert "Obligations of Data Fiduciary 30%" in methodology
    assert "referenced by clause or control identifier" in methodology.lower() or (
        "referenced by clause or control identifier" in lowered
    )
    text_value = pdf_export.methodology_text(["iso27001"], 2)
    assert "across 2 in-scope requirements" in text_value
    for phrase in NON_LEGAL_FORBIDDEN:
        assert phrase not in text_value.lower(), phrase


def test_scenario_9_framework_conditional_copy(db, http, gate, monkeypatch):
    """Scenario 9 (D0 #6): ISO-only reports carry no DPDPA or legal-regime copy; mixed reports carry both."""
    iso = _ids("iso27001", 2)
    iso_only = _released_board_assessment(
        db, http, gate, monkeypatch,
        frameworks=["iso27001"],
        per_framework={"iso27001": [_item(iso[0], "non_compliant", "high"), _item(iso[1], "compliant")]},
        company="ISO Only Ltd",
    )
    iso_text = _pdf_text(_board_pdf(http, iso_only)).lower()
    for phrase in NON_LEGAL_FORBIDDEN:
        assert phrase not in iso_text, phrase
    assert "qualified information security auditor" in iso_text
    assert "certification audit" in iso_text
    assert "disclaimer:" in iso_text

    dpdpa = _ids("dpdpa", 1)
    mixed = _released_board_assessment(
        db, http, gate, monkeypatch,
        frameworks=["dpdpa", "iso27001"],
        per_framework={
            "dpdpa": [_item(dpdpa[0], "non_compliant", "high")],
            "iso27001": [_item(iso[0], "partially_compliant")],
        },
        company="Mixed Ltd",
    )
    mixed_text = _pdf_text(_board_pdf(http, mixed)).lower()
    assert "legal counsel" in mixed_text
    assert "qualified information security auditor" in mixed_text
    assert "privacy practice" not in mixed_text and "cmmi" not in mixed_text

    for framework_ids in (["nist_csf"], ["pci_dss"], ["iso27001", "nist_csf"]):
        for helper in (pdf_export.methodology_text(framework_ids, 1),):
            for phrase in NON_LEGAL_FORBIDDEN:
                assert phrase not in helper.lower(), (framework_ids, phrase)


def test_scenario_10_kpi_roadmap_and_dead_web_section(db, http, gate, monkeypatch):
    """Scenario 10 (D0 #7): no 'not estimated' KPI, roadmap from real Actions, no dead root-cause panel."""
    ids = _ids("dpdpa", 3)
    assessment = _seed(db, frameworks=["dpdpa"], applicable=ids)
    conclusions = _analyse(
        monkeypatch, gate, db, assessment,
        {
            "dpdpa": [
                _item(ids[0], "non_compliant", "high"),
                _item(ids[1], "partially_compliant", "medium"),
                _item(ids[2], "insufficient_evidence", "medium"),
            ]
        },
    )
    by_id = {row.requirement_id: row for row in conclusions}
    for conclusion in conclusions:
        _approve_http(http, db, assessment, conclusion)
    _finding_with_action(
        http, assessment, by_id[ids[0]],
        title="Consent records missing", owner="Anita Rao", target="2026-11-30",
        action="Build a consent ledger",
    )
    _release(db, assessment)

    pages = _pdf_pages(_board_pdf(http, assessment))
    full = " ".join(pages)
    for phrase in ("Remediation Timeline", "not estimated", "0-4 weeks", "1-3 months", "3-6 months", "6-12 months"):
        assert phrase not in full, phrase
    dashboard = next(page for page in pages if "Executive Dashboard" in page)
    assert "Insufficient Evidence" in dashboard
    roadmap = next(page for page in pages if "Remediation Actions" in page)
    assert "Build a consent ledger" in roadmap
    assert "Owner: Anita Rao" in roadmap and "Target: 30 Nov 2026" in roadmap
    assert f"Closes: {FrameworkRegistry.get('dpdpa').name} {ids[0]} - Consent records missing" in roadmap
    assert "1 identified gap(s) have no approved finding with an action yet." in roadmap
    assert full.index("Remediation Actions") < full.index("Detailed Gap Findings")

    from app.routers import web

    assert not hasattr(web, "_compute_root_cause_counts")
    template = (REPO_ROOT / "app/templates/partials/report_summary.html").read_text()
    assert "Why These Gaps Exist" not in template and "root_cause_counts" not in template
    summary = http.get(f"/assessments/{assessment.id}/report-summary")
    assert summary.status_code == 200
    assert "Why These Gaps Exist" not in summary.text


# ---------------------------------------------------------------------------
# 11. Integrated PDF (D0 #9)
# ---------------------------------------------------------------------------


def _integrated(db, http, gate, monkeypatch, *, iso_only=False):
    iso = _ids("iso27001", 1)
    dpdpa = _ids("dpdpa", 1)
    first_frameworks = ["iso27001"] if iso_only else ["dpdpa", "iso27001"]
    per_framework = (
        {"iso27001": [_item(iso[0], "non_compliant", "high")]}
        if iso_only
        else {
            "dpdpa": [_item(dpdpa[0], "non_compliant", "high")],
            "iso27001": [_item(iso[0], "partially_compliant")],
        }
    )
    first = _released_board_assessment(
        db, http, gate, monkeypatch,
        frameworks=first_frameworks,
        per_framework=per_framework,
        company="Integrated Client",
        description="Assessment A",
        prepared_by="Priya Sharma",
        reviewed_by="Ravi Menon",
    )
    engagement = db.get(Engagement, first.engagement_id)
    response = http.post(
        f"/api/engagements/{engagement.id}/integrated-reports", data={"reviewer_name": "Priya"}
    )
    assert response.status_code == 200, response.text
    snapshot = db.get(ReportSnapshot, response.json()["snapshot_id"])
    content = report_snapshots.read_snapshot_bytes(db, snapshot)
    return first, engagement, snapshot, content


def test_scenario_11_integrated_pdf_period_scope_methodology_disclaimer(
    db, http, gate, monkeypatch
):
    """Scenario 11 (D0 #1, #9): per-section period, cut-off, sign-off; scope, methodology, disclaimer pages."""
    first, _engagement, snapshot, content = _integrated(db, http, gate, monkeypatch)
    pages = _pdf_pages(content)
    full = " ".join(pages)
    today = datetime.now(timezone.utc).strftime("%d %b %Y")
    assert f"Report generated: {today}" in pages[0]
    section = next(page for page in pages if "Framework Scores (this assessment only)" in page)
    assert PERIOD_TEXT in section and CUTOFF_TEXT in section
    assert "Prepared by: Priya Sharma" in section and "Reviewed by: Ravi Menon" in section
    assert "Assessment period and evidence cut-off: not recorded" not in full
    scope = next(page for page in pages if "Scope & Limitations" in page and "Nature of Assessment" in page)
    assert "assessment period 01 Apr 2026 to 30 Jun 2026" in scope
    assert "evidence cut-off 15 Jul 2026" in scope
    methodology = next(page for page in pages if "Assessment Methodology" in page)
    assert "Basis of Assessment:" in methodology and "Disclaimer:" in methodology
    assert "legal counsel" in full.lower()
    assert full.index("Framework Scores (this assessment only)") < full.index("Assessment Methodology")



def test_scenario_11b_iso_only_integrated_pdf_has_no_legal_copy(db, http, gate, monkeypatch):
    """Scenario 11b (D0 #6, #9): an ISO-only integrated report has no DPDPA or legal-regime copy."""
    _first, _engagement, _snapshot, content = _integrated(db, http, gate, monkeypatch, iso_only=True)
    lowered = _pdf_text(content).lower()
    for phrase in NON_LEGAL_FORBIDDEN:
        assert phrase not in lowered, phrase
    assert "qualified information security auditor" in lowered
    assert "disclaimer:" in lowered


# ---------------------------------------------------------------------------
# 12. Layout overflow (D0 #10)
# ---------------------------------------------------------------------------


def test_scenario_12_many_domains_stay_on_the_page(db, http, gate, monkeypatch):
    """Scenario 12 (D0 #10): DPDPA + ISO + NIST (16 domains) never draws text or boxes off the page."""
    # 16 domains in total; ISO's first 37 controls are all in one domain, so its
    # heatmap row needs more squares than fit on one line.
    iso_domain = [
        control["id"]
        for control in FrameworkRegistry.get_all_controls_enriched("iso27001")
        if control["chapter"] == "organizational"
    ]
    assert len(iso_domain) > pdf_export.HEATMAP_SQUARES_PER_LINE * 2
    per_framework = {
        "dpdpa": [_item(_ids("dpdpa", 1)[0], "non_compliant", "high")],
        "iso27001": [
            _item(rid, "non_compliant" if index % 3 == 0 else "compliant", "high" if index % 5 == 0 else "low")
            for index, rid in enumerate(iso_domain)
        ],
        "nist_csf": [_item(_ids("nist_csf", 1)[0], "partially_compliant", "medium")],
    }
    assessment = _released_board_assessment(
        db, http, gate, monkeypatch,
        frameworks=["dpdpa", "iso27001", "nist_csf"],
        per_framework=per_framework,
        company="Wide Scope Pvt Ltd",
    )
    content = _board_pdf(http, assessment)
    tolerance = 0.5
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        first_page = " ".join((pdf.pages[0].extract_text() or "").split())
        for number, page in enumerate(pdf.pages, start=1):
            for char in page.chars:
                assert char["x0"] >= -tolerance and char["x1"] <= page.width + tolerance, (
                    number, char["text"], char["x0"], char["x1"])
                assert char["top"] >= -tolerance and char["bottom"] <= page.height + tolerance, (
                    number, char["text"], char["top"], char["bottom"])
            footer_tops = [
                char["top"] for char in page.chars
                if char["text"] == "C" and "CONFIDENTIAL" in "".join(
                    other["text"] for other in page.chars if abs(other["top"] - char["top"]) < 1
                )
            ]
            if footer_tops:
                footer_top = min(footer_tops)
                body = [char for char in page.chars if abs(char["top"] - footer_top) >= 1]
                assert all(char["bottom"] <= footer_top + tolerance for char in body), (
                    number, max(char["bottom"] for char in body), footer_top)
            for rect in page.rects:
                assert rect["x0"] >= -tolerance and rect["x1"] <= page.width + tolerance, (
                    number, rect["x0"], rect["x1"])
                assert rect["top"] >= -tolerance and rect["bottom"] <= page.height + tolerance, (
                    number, rect["top"], rect["bottom"])
    assert re.search(r"\+\d+ more assessment areas on the Executive Dashboard", first_page)
    assert pdf_export.COVER_AREA_ROWS == 7
    assert pdf_export.HEATMAP_SQUARES_PER_LINE == 17
    assert pdf_export.heatmap_row_height(1) == 14
    assert pdf_export.heatmap_row_height(37) > 14


# ---------------------------------------------------------------------------
# 13. Content-Disposition (D0 #11)
# ---------------------------------------------------------------------------

DISPOSITION = re.compile(
    r"attachment; filename=\"(?P<fallback>[A-Za-z0-9._-]+)\"; filename\*=UTF-8''(?P<encoded>[A-Za-z0-9%._~-]+)"
)


def test_scenario_13_content_disposition_is_escaped(db, http, gate, monkeypatch):
    """Scenario 13 (D0 #11): untrusted company names cannot break or inject into Content-Disposition."""
    from app.utils.http_headers import attachment_disposition

    hostile = 'Evil" Co; filename=x.exe\r\nX-Injected: 1 Café 株式会社'
    value = attachment_disposition(f"Report_{hostile}.pdf")
    match = DISPOSITION.fullmatch(value)
    assert match, value
    assert "\r" not in value and "\n" not in value
    assert unquote(match["encoded"]) == 'Report_Evil" Co; filename=x.exe' + "X-Injected: 1 Café 株式会社.pdf"
    assert match["fallback"].endswith(".pdf")

    ids = _ids("dpdpa", 1)
    assessment = _released_board_assessment(
        db, http, gate, monkeypatch,
        frameworks=["dpdpa"],
        per_framework={"dpdpa": [_item(ids[0], "non_compliant", "high")]},
        company=hostile,
    )
    assessment.scope_answers = json.dumps({})
    db.commit()
    for path in (
        f"/api/assessments/{assessment.id}/report/pdf",
        f"/assessments/{assessment.id}/evidence-checklist/pdf",
        f"/assessments/{assessment.id}/evidence-checklist/docx",
    ):
        response = http.get(path)
        assert response.status_code == 200, (path, response.text)
        header = response.headers["content-disposition"]
        assert DISPOSITION.fullmatch(header), (path, header)
        assert "x-injected" not in {key.lower() for key in response.headers}


# ---------------------------------------------------------------------------
# 14. Sign-off block and S()
# ---------------------------------------------------------------------------


def test_scenario_14_sign_off_block_through_sanitiser(db, http, gate, monkeypatch):
    """Scenario 14: the sign-off page renders free-text names through S(); ₹ becomes 'Rs.'."""
    assert pdf_export.S("₹250 Cr") == "Rs.250 Cr"
    ids = _ids("dpdpa", 1)
    assessment = _released_board_assessment(
        db, http, gate, monkeypatch,
        frameworks=["dpdpa"],
        per_framework={"dpdpa": [_item(ids[0], "non_compliant", "high")]},
        prepared_by="Priya Sharma — Lead (₹ budget) प्रिया",
    )
    pages = _pdf_pages(_board_pdf(http, assessment))
    sign_off = pages[-1]
    assert "Report Sign-off" in sign_off
    assert "Prepared by: Priya Sharma - Lead (Rs. budget)" in sign_off
    assert "Reviewed by: not recorded" in sign_off
    assert PERIOD_TEXT in sign_off and CUTOFF_TEXT in sign_off
    assert "not verified sign-ins" in sign_off
    source = Path(pdf_export.__file__).read_text()
    body = source[source.index("def _render_sign_off_page"):]
    body = body[: body.index("\ndef ", 1)]
    assert "text=S(" in body


# ---------------------------------------------------------------------------
# 15-16. Snapshots and workpaper
# ---------------------------------------------------------------------------


def test_scenario_15_snapshot_captures_basis_immutably(db, http, gate, monkeypatch):
    """Scenario 15: a gap-report snapshot freezes period, cut-off and sign-off at generation time."""
    ids = _ids("dpdpa", 1)
    assessment = _seed(
        db, frameworks=["dpdpa"], applicable=ids, prepared_by="Priya Sharma", reviewed_by="Ravi Menon"
    )
    (conclusion,) = _analyse(monkeypatch, gate, db, assessment, {"dpdpa": [_item(ids[0], "non_compliant", "high")]})
    _approve_http(http, db, assessment, conclusion)
    _release(db, assessment)

    generated = http.post(
        f"/api/assessments/{assessment.id}/snapshots",
        data={"type": "gap_report", "reviewer_name": "Priya"},
    )
    assert generated.status_code == 200, generated.text
    first = db.get(ReportSnapshot, generated.json()["snapshot_id"])
    first_bytes = report_snapshots.read_snapshot_bytes(db, first)
    first_hash = hashlib.sha256(first_bytes).hexdigest()
    assert CUTOFF_TEXT in _pdf_text(first_bytes)
    assert "Prepared by: Priya Sharma" in _pdf_text(first_bytes)

    workpaper = http.post(
        f"/api/assessments/{assessment.id}/snapshots",
        data={"type": "workpaper", "reviewer_name": "Priya"},
    )
    assert workpaper.status_code == 200, workpaper.text
    workpaper_snapshot = db.get(ReportSnapshot, workpaper.json()["snapshot_id"])
    html = report_snapshots.read_snapshot_bytes(db, workpaper_snapshot).decode("utf-8")
    assert "data-report-basis" in html
    assert "Assessment period: 01 Apr 2026 to 30 Jun 2026" in html
    assert "Evidence cut-off: 15 Jul 2026" in html

    # Change the basis the only legal way: reopen, edit, re-approve, re-release.
    conclusion = db.get(Conclusion, conclusion.id)
    assert _post_decision(http, assessment, conclusion, "reopen").status_code == 200
    changed = http.post(
        f"/api/assessments/{assessment.id}/report-basis",
        data={**PERIOD_FORM, "evidence_cutoff": "2026-08-01", "prepared_by": "Anita Rao", "reviewed_by": "Ravi Menon"},
    )
    assert changed.status_code == 200, changed.text
    db.expire_all()
    _approve_http(http, db, assessment, db.get(Conclusion, conclusion.id))
    _release(db, assessment)
    regenerated = http.post(
        f"/api/assessments/{assessment.id}/snapshots",
        data={"type": "gap_report", "reviewer_name": "Priya"},
    )
    assert regenerated.status_code == 200, regenerated.text
    second = db.get(ReportSnapshot, regenerated.json()["snapshot_id"])

    db.expire_all()
    first = db.get(ReportSnapshot, first.id)
    unchanged = report_snapshots.read_snapshot_bytes(db, first)
    assert hashlib.sha256(unchanged).hexdigest() == first_hash
    assert CUTOFF_TEXT in _pdf_text(unchanged)
    assert "Prepared by: Priya Sharma" in _pdf_text(unchanged)
    second_text = _pdf_text(report_snapshots.read_snapshot_bytes(db, second))
    assert "Evidence cut-off: 01 Aug 2026" in second_text
    assert "Prepared by: Anita Rao" in second_text
    assert "report_basis" not in report_snapshots.generated_event(db, second.id)


def test_scenario_16_workpaper_page_shows_basis(db, http, gate, monkeypatch):
    """Scenario 16: the live Workpaper header shows the period and cut-off (or 'not recorded')."""
    ids = _ids("dpdpa", 1)
    recorded = _seed(db, frameworks=["dpdpa"], applicable=ids)
    page = http.get(f"/assessments/{recorded.id}/workpaper")
    assert page.status_code == 200
    assert "Assessment period: 01 Apr 2026 to 30 Jun 2026 · Evidence cut-off: 15 Jul 2026" in page.text
    missing = _seed(db, frameworks=["dpdpa"], applicable=ids, period=False, company="No Period")
    page = http.get(f"/assessments/{missing.id}/workpaper")
    assert "Assessment period: not recorded · Evidence cut-off: not recorded" in page.text
