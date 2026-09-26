"""Contract tests for the P4-2 longitudinal synthetic demonstration."""

from __future__ import annotations

import inspect
import json
import re
import subprocess
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.config import settings
from app.database import get_db
from app.main import app
from app.models.action import Action
from app.models.analysis_run import AnalysisRun
from app.models.assessment import Assessment
from app.models.assessment_pack import AssessmentPack
from app.models.audit_event import AuditEvent
from app.models.client import Client
from app.models.conclusion import Conclusion, ConclusionRevision
from app.models.engagement import Engagement
from app.models.evidence import Evidence, EvidenceUse, EvidenceVersion
from app.models.finding import Finding
from app.models.magic_link import MagicLink
from app.models.report import GapItem, GapReport
from app.models.report_snapshot import ReportSnapshot
from app.routers import web
from app.services import evidence as evidence_service
from app.services import evidence_reuse, magic_links, remediation_rollup, report_content
from app.services.report_snapshots import generated_event
from app.services.evidence_reuse import AUDIT_METADATA_KEYS

from scripts.seed_test_companies import (
    DEMO_CLIENT_A,
    DEMO_CLIENT_B,
    DEMO_REVIEWER,
    DemoAlreadySeeded,
    LongitudinalDemo,
    _at,
    seed_longitudinal_demo,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


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
    path = tmp_path / "longitudinal.sqlite3"
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
    from app.template_config import configure_templates
    from app.routers.web import templates

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
def upload_root(tmp_path, monkeypatch) -> Path:
    root = tmp_path / "uploads"
    root.mkdir()
    monkeypatch.setattr(settings, "upload_dir", str(root))
    return root


@pytest.fixture(autouse=True)
def no_llm(monkeypatch):
    from app.services import llm_client

    def _raise(*_args, **_kwargs):
        raise AssertionError("The demo must never call the LLM.")

    monkeypatch.setattr(llm_client, "_get_client", _raise)


@pytest.fixture()
def demo(db, http) -> LongitudinalDemo:
    return seed_longitudinal_demo(db, http)


def _day(demo: LongitudinalDemo, offset: int) -> date:
    return demo.anchor + timedelta(days=offset)


def _history(action: Action) -> list[dict]:
    return json.loads(action.history_json)


def _finding_and_action(db, demo, key: str) -> tuple[Finding, Action]:
    finding = db.get(Finding, demo.finding_ids[key])
    return finding, db.get(Action, demo.action_ids[key])


def test_scenario_1_seed_runs_without_error_and_never_calls_llm(db, http, demo, upload_root):
    """Scenario 1: the complete seed returns its manifest and expected row counts."""
    assert isinstance(demo, LongitudinalDemo)
    assert set(demo.client_ids) == {"a", "b"}
    assert set(demo.engagement_ids) == {"a", "b"}
    assert set(demo.assessment_ids) == {"baseline", "validation", "nist"}
    assert len(demo.evidence_ids) == 9
    assert len(demo.finding_ids) == 6
    assert len(demo.action_ids) == 6
    assert db.query(Client).count() == 2
    assert db.query(Engagement).count() == 2
    assert db.query(Assessment).count() == 3
    assert db.query(AssessmentPack).count() == 4
    assert db.query(Evidence).count() == 9
    assert db.query(EvidenceVersion).count() == 9
    assert db.query(EvidenceUse).count() == 9
    assert db.query(Conclusion).count() == 12
    assert db.query(Finding).count() == 6
    assert db.query(Action).count() == 6
    assert db.query(MagicLink).count() == 1
    assert db.query(ReportSnapshot).count() == 1
    for action, expected in {
        "evidence_reuse.confirmed": 2,
        "magic_link.upload_received": 2,
        "magic_link.created": 1,
        "evidence_use.created": 9,
    }.items():
        assert db.query(AuditEvent).filter(AuditEvent.action == action).count() == expected
    for version in db.query(EvidenceVersion).all():
        assert (upload_root / version.storage_path).is_file()
        assert evidence_service.verify_version(db, version.id)


def test_scenario_2_dashboard_has_both_clients_and_hierarchy(db, http, demo):
    """Scenario 2: the dashboard and hierarchy pages expose the seeded portfolio."""
    client_a = db.get(Client, demo.client_ids["a"])
    client_b = db.get(Client, demo.client_ids["b"])
    engagement_a = db.get(Engagement, demo.engagement_ids["a"])
    engagement_b = db.get(Engagement, demo.engagement_ids["b"])
    assessments_a = (
        db.query(Assessment).filter_by(engagement_id=engagement_a.id).order_by(Assessment.created_at).all()
    )
    assessments_b = db.query(Assessment).filter_by(engagement_id=engagement_b.id).all()
    assert client_a.name == DEMO_CLIENT_A and client_b.name == DEMO_CLIENT_B
    assert len(assessments_a) == 2 and len(assessments_b) == 1
    assert json.loads(assessments_a[0].selected_frameworks) == ["dpdpa", "iso27001"]
    assert json.loads(assessments_a[1].selected_frameworks) == ["iso27001"]
    assert json.loads(assessments_b[0].selected_frameworks) == ["nist_csf"]
    assert {pack.pack_version for pack in db.query(AssessmentPack).filter_by(assessment_id=assessments_a[0].id)} == {"2023", "2022"}
    assert [pack.pack_version for pack in db.query(AssessmentPack).filter_by(assessment_id=assessments_a[1].id)] == ["2022"]
    assert [pack.pack_version for pack in db.query(AssessmentPack).filter_by(assessment_id=assessments_b[0].id)] == ["2.0"]
    assert engagement_a.status == engagement_b.status == "active"
    assert all(assessment.status == "completed" for assessment in assessments_a + assessments_b)

    dashboard = http.get("/")
    assert dashboard.status_code == 200
    for value in (client_a.name, client_b.name, engagement_a.name, engagement_b.name):
        assert value in dashboard.text
    assert f'href="/clients/{client_a.id}"' in dashboard.text
    assert f'href="/clients/{client_b.id}"' in dashboard.text
    assert f'href="/engagements/{engagement_a.id}"' in dashboard.text
    assert f'href="/engagements/{engagement_b.id}"' in dashboard.text
    page_a = http.get(f"/engagements/{engagement_a.id}")
    assert page_a.status_code == 200
    assert page_a.text.index(f'href="/assessments/{demo.assessment_ids["validation"]}"') < page_a.text.index(f'href="/assessments/{demo.assessment_ids["baseline"]}"')
    assert "Baseline gap assessment (DPDPA + ISO 27001)" in page_a.text
    assert "Remediation validation (ISO 27001)" in page_a.text
    page_b = http.get(f"/engagements/{engagement_b.id}")
    assert "NIST CSF 2.0 baseline gap assessment" in page_b.text
    assert "Information security policy" in page_b.text
    assert "Incident response plan" in page_b.text
    assert engagement_a.name in http.get(f"/clients/{client_a.id}").text


def test_scenario_3_dates_are_anchor_relative_and_audits_are_current(db, http, demo):
    """Scenario 3: business dates follow the anchor while append-only events stay current."""
    client_a = db.get(Client, demo.client_ids["a"])
    client_b = db.get(Client, demo.client_ids["b"])
    engagement_a = db.get(Engagement, demo.engagement_ids["a"])
    engagement_b = db.get(Engagement, demo.engagement_ids["b"])
    baseline = db.get(Assessment, demo.assessment_ids["baseline"])
    validation = db.get(Assessment, demo.assessment_ids["validation"])
    nist = db.get(Assessment, demo.assessment_ids["nist"])
    assert client_a.created_at.date() == engagement_a.created_at.date() == baseline.created_at.date() == _day(demo, -200)
    assert validation.created_at.date() == _day(demo, -7)
    assert client_b.created_at.date() == engagement_b.created_at.date() == nist.created_at.date() == _day(demo, -30)
    expected_evidence_dates = {
        "a_policy": -196, "a_ropa": -196, "a_access_q1": -196,
        "a_dr_report": -120, "a_access_memo": -40, "a_access_q3": -5,
    }
    for key, offset in expected_evidence_dates.items():
        evidence = db.get(Evidence, demo.evidence_ids[key])
        version = evidence_service.current_version(db, evidence.id)
        assert evidence.created_at.date() == version.created_at.date() == _day(demo, offset)
    q1 = db.get(Evidence, demo.evidence_ids["a_access_q1"])
    q1_version = evidence_service.current_version(db, q1.id)
    assert q1.original_filename == f"Meridian_Access_Review_{_day(demo, -196):%Y-%m}.docx"
    assert f"Quarterly User Access Review - {_day(demo, -196):%B %Y}" in q1_version.extracted_text
    assert all(event.created_at.date() >= _day(demo, -1) for event in db.query(AuditEvent).all())
    assert all(db.get(Evidence, key).created_at.date() >= _day(demo, -1) for key in [demo.evidence_ids["b_policy"], demo.evidence_ids["b_mfa_export"], demo.evidence_ids["b_mfa_fix"]])


def test_scenario_4_reuse_prompt_requires_confirmation_and_audit(db, http, demo):
    """Scenario 4: a warning-bearing candidate requires a per-item acknowledgement."""
    validation_id = demo.assessment_ids["validation"]
    candidate = evidence_reuse.reuse_candidates(db, validation_id)[0]
    assert candidate.evidence_id == demo.evidence_ids["a_access_q1"]
    source_use_id = candidate.source_use_id
    before = (db.query(EvidenceUse).count(), db.query(AuditEvent).count())
    page = http.get(f"/assessments/{validation_id}/evidence-reuse")
    assert page.status_code == 200
    assert page.text.count("data-reuse-candidate ") == 1
    assert 'data-warnings="age scope"' in page.text
    assert 'data-reuse-warning="age"' in page.text
    assert 'data-reuse-warning="scope"' in page.text
    assert "189 days" in page.text
    assert 'name="acknowledge_warnings"' in page.text
    assert "Confirm reuse" in page.text
    assert 'hx-boost="false"' in page.text
    assert f'href="/evidence/{demo.evidence_ids["a_access_q1"]}"' in page.text
    assert "Declining records nothing." in page.text
    for data in ({"reviewer_name": DEMO_REVIEWER}, {"acknowledge_warnings": "no", "reviewer_name": DEMO_REVIEWER}):
        response = http.post(f"/assessments/{validation_id}/evidence-reuse/{source_use_id}/confirm", data=data)
        assert response.status_code == 400
        assert "data-reuse-error" in response.text
        assert evidence_reuse.REUSE_ACK_REQUIRED in response.text
        assert (db.query(EvidenceUse).count(), db.query(AuditEvent).count()) == before
    response = http.post(
        f"/assessments/{validation_id}/evidence-reuse/{source_use_id}/confirm",
        data={"acknowledge_warnings": "yes", "reviewer_name": DEMO_REVIEWER},
        follow_redirects=False,
    )
    assert response.status_code == 303
    db.expire_all()
    use = db.query(EvidenceUse).filter_by(evidence_id=demo.evidence_ids["a_access_q1"], assessment_id=validation_id).one()
    assert (use.framework_id, use.requirement_id, use.relevance) == ("iso27001", "ISO.A5.18", "primary")
    events = db.query(AuditEvent).order_by(AuditEvent.created_at, AuditEvent.id).all()
    reuse_events = [row for row in events if row.action in {"evidence_use.created", "evidence_reuse.confirmed"}][-2:]
    assert [row.action for row in reuse_events] == ["evidence_use.created", "evidence_reuse.confirmed"]
    confirmed = reuse_events[1]
    metadata = json.loads(confirmed.metadata_json)
    assert confirmed.actor == f"consultant:{DEMO_REVIEWER}"
    assert confirmed.entity_type == "evidence_use" and confirmed.entity_id == use.id
    assert set(metadata) == set(AUDIT_METADATA_KEYS)
    assert metadata["age_days"] == 189
    assert metadata["warnings"] == ["age", "scope"]
    assert metadata["acknowledged_warnings"] is True
    assert metadata["reference_date"] == _day(demo, -7).isoformat()
    after_page = http.get(f"/assessments/{validation_id}/evidence-reuse")
    assert 'data-reuse-candidate ' not in after_page.text
    assert "No evidence from earlier assessments is waiting for confirmation." in after_page.text
    repeated = http.post(f"/assessments/{validation_id}/evidence-reuse/{source_use_id}/confirm", data={"acknowledge_warnings": "yes"})
    assert repeated.status_code == 409
    assert evidence_reuse.REUSE_NOT_AVAILABLE in repeated.text
    documents = http.get(f"/assessments/{validation_id}?tab=documents")
    assert 'data-evidence-reuse-link' in documents.text
    assert f'href="/assessments/{validation_id}/evidence-reuse"' in documents.text


def test_scenario_5_boundaries_invalidation_unmigrated_and_query_bound(db, http, demo, engine):
    """Scenario 5: the strict age boundary and candidate exclusions are enforced."""
    validation_id = demo.assessment_ids["validation"]
    q1 = db.get(Evidence, demo.evidence_ids["a_access_q1"])
    q1_version = evidence_service.current_version(db, q1.id)
    q1_version.created_at = _at(demo.anchor, -7 - 180)
    db.commit()
    boundary = evidence_reuse.reuse_candidates(db, validation_id)[0]
    assert boundary.age_days == 180 and boundary.warnings == ("scope",)
    q1_version.created_at = _at(demo.anchor, -7 - 181)
    db.commit()
    stale = evidence_reuse.reuse_candidates(db, validation_id)[0]
    assert stale.age_days == 181 and stale.warnings == ("age", "scope")
    assert evidence_reuse.reuse_candidates(db, demo.assessment_ids["baseline"]) == []
    assert evidence_reuse.reuse_candidates(db, demo.assessment_ids["nist"]) == []
    assert all(candidate.framework_id != "dpdpa" for candidate in evidence_reuse.reuse_candidates(db, validation_id))
    evidence_service.transition_evidence(db, evidence_id=q1.id, to_status="invalidated", actor="consultant", reason="test")
    db.commit()
    assert evidence_reuse.reuse_candidates(db, validation_id) == []
    old_post = http.post(f"/assessments/{validation_id}/evidence-reuse/{stale.source_use_id}/confirm", data={"acknowledge_warnings": "yes"})
    assert old_post.status_code == 409
    assert http.get("/assessments/unknown/evidence-reuse").status_code == 404
    unmigrated = Assessment(company_name="Unmigrated", industry="technology", company_size="small", selected_frameworks=json.dumps(["iso27001"]))
    db.add(unmigrated)
    db.commit()
    assert evidence_reuse.reuse_candidates(db, unmigrated.id) == []
    assert "not linked to an engagement" in http.get(f"/assessments/{unmigrated.id}/evidence-reuse").text
    statements = 0

    def _count(_conn, _cursor, _statement, _parameters, _context, _executemany):
        nonlocal statements
        statements += 1

    event.listen(engine, "before_cursor_execute", _count)
    try:
        db.expire_all()
        evidence_reuse.reuse_candidates(db, validation_id)
    finally:
        event.remove(engine, "before_cursor_execute", _count)
    assert statements <= 6


def test_scenario_6_reuse_audit_and_analysis_citations(db, http, demo):
    """Scenario 6: confirmed evidence is in scope and cited by the target analysis."""
    validation_id = demo.assessment_ids["validation"]
    events = [row for row in db.query(AuditEvent).filter_by(action="evidence_reuse.confirmed").all()]
    assert len(events) == 2
    metadata = [json.loads(row.metadata_json) for row in events]
    assert {item["evidence_id"] for item in metadata} == {demo.evidence_ids["a_policy"], demo.evidence_ids["a_dr_report"]}
    assert {item["age_days"] for item in metadata} == {189, 113}
    assert {tuple(item["warnings"]) for item in metadata} == {("age", "scope"), ("scope",)}
    assert all(item["acknowledged_warnings"] is True for item in metadata)
    panel = {row["id"]: row for row in evidence_service.evidence_panel_rows(db, validation_id)}
    assert panel[demo.evidence_ids["a_policy"]]["mapped_in"] is True
    assert panel[demo.evidence_ids["a_dr_report"]]["mapped_in"] is True
    assert panel[demo.evidence_ids["a_access_q3"]]["mapped_in"] is False
    assert demo.evidence_ids["a_ropa"] not in panel
    assert demo.evidence_ids["a_access_q1"] not in panel
    expected = {
        "ISO.A5.1": demo.evidence_ids["a_policy"],
        "ISO.A5.30": demo.evidence_ids["a_dr_report"],
        "ISO.A5.18": demo.evidence_ids["a_access_q3"],
    }
    for requirement_id, evidence_id in expected.items():
        conclusion = db.query(Conclusion).filter_by(assessment_id=validation_id, requirement_id=requirement_id).one()
        revision = db.query(ConclusionRevision).filter_by(conclusion_id=conclusion.id, action="proposed").one()
        citations = json.loads(revision.citations_json)
        version = evidence_service.current_version(db, evidence_id)
        assert any(citation["evidence_version_id"] == version.id for citation in citations)


def test_scenario_7_conclusions_are_independent(db, http, demo):
    """Scenario 7: each assessment has its own approved conclusion set and runs."""
    expected = {
        "baseline": {"dpdpa": {"CH3.ACCESS.1", "CH2.SECURITY.1", "CH2.CONSENT.3"}, "iso27001": {"ISO.A5.1", "ISO.A5.18", "ISO.A5.30"}},
        "validation": {"iso27001": {"ISO.A5.1", "ISO.A5.18", "ISO.A5.30"}},
        "nist": {"nist_csf": {"NIST.GV.PO.01", "NIST.PR.AA.03", "NIST.RS.MA.01"}},
    }
    all_ids = []
    for assessment_key, frameworks in expected.items():
        assessment_id = demo.assessment_ids[assessment_key]
        rows = db.query(Conclusion).filter_by(assessment_id=assessment_id).all()
        assert {
            framework_id: {
                item.requirement_id for item in rows if item.framework_id == framework_id
            }
            for framework_id in frameworks
        } == frameworks
        all_ids.extend(row.id for row in rows)
        assert all(row.version == 2 for row in rows)
        for row in rows:
            revisions = db.query(ConclusionRevision).filter_by(conclusion_id=row.id).order_by(ConclusionRevision.created_at, ConclusionRevision.id).all()
            assert [revision.action for revision in revisions] == ["proposed", "approved"]
            run = db.get(AnalysisRun, revisions[0].analysis_run_id)
            assert run.assessment_id == assessment_id
    assert len(all_ids) == len(set(all_ids))
    baseline_access = db.query(Conclusion).filter_by(assessment_id=demo.assessment_ids["baseline"], framework_id="iso27001", requirement_id="ISO.A5.18").one()
    validation_access = db.query(Conclusion).filter_by(assessment_id=demo.assessment_ids["validation"], framework_id="iso27001", requirement_id="ISO.A5.18").one()
    assert baseline_access.outcome == "non_compliant"
    assert validation_access.outcome == "compliant"
    policy_version = evidence_service.current_version(db, demo.evidence_ids["a_policy"]).id
    for framework_id, requirement_id in (("iso27001", "ISO.A5.1"), ("dpdpa", "CH2.SECURITY.1")):
        conclusion = db.query(Conclusion).filter_by(assessment_id=demo.assessment_ids["baseline"], framework_id=framework_id, requirement_id=requirement_id).one()
        revision = db.query(ConclusionRevision).filter_by(conclusion_id=conclusion.id, action="proposed").one()
        assert policy_version in revision.citations_json


def test_scenario_8_action_lifecycle_matches_spec(db, http, demo):
    """Scenario 8: findings and append-only actions match every lifecycle step."""
    expected = {
        "a_consent": ("open", "open", ["created"], "Rhea Kapoor", 30),
        "a_access": ("verified", "resolved", ["created", "status_changed", "closed", "verified"], "Arjun Mehta", -60),
        "a_dr": ("in_progress", "in_progress", ["created", "status_changed"], "Arjun Mehta", -14),
        "v_dr": ("open", "open", ["created"], "Arjun Mehta", 21),
        "b_mfa": ("closed", "in_progress", ["created", "status_changed", "closed"], "Dev Anand", 14),
        "b_ir": ("open", "open", ["created"], None, -3),
    }
    for key, (action_status, finding_status, actions, owner, target) in expected.items():
        finding, action = _finding_and_action(db, demo, key)
        assert (action.status, finding.status, action.owner, action.target_date.date()) == (action_status, finding_status, owner, _day(demo, target))
        history = _history(action)
        assert [entry["action"] for entry in history] == actions
        assert all(entry["actor"] == f"consultant:{DEMO_REVIEWER}" for entry in history)
    memo = db.get(Evidence, demo.evidence_ids["a_access_memo"])
    memo_version = evidence_service.current_version(db, memo.id)
    a_access = db.get(Action, demo.action_ids["a_access"])
    expected_evidence = {
        "evidence_id": memo.id, "evidence_version_id": memo_version.id,
        "version_number": 1, "sha256": memo_version.file_hash_sha256,
        "filename": memo_version.original_filename,
    }
    assert _history(a_access)[2]["evidence"] == expected_evidence
    assert _history(a_access)[3]["evidence"] == expected_evidence
    b_mfa = db.get(Action, demo.action_ids["b_mfa"])
    assert _history(b_mfa)[2]["evidence"]["evidence_id"] == demo.evidence_ids["b_mfa_fix"]


def test_scenario_9_rollups_and_integrated_reporting(db, http, demo):
    """Scenario 9: engagement-level remediation and reporting roll up correctly."""
    engagement_a = db.get(Engagement, demo.engagement_ids["a"])
    engagement_b = db.get(Engagement, demo.engagement_ids["b"])
    rollup_a = remediation_rollup.engagement_rollup(db, engagement_a, today=demo.anchor)
    rollup_b = remediation_rollup.engagement_rollup(db, engagement_b, today=demo.anchor)
    assert rollup_a.counts == {"open": 2, "in_progress": 1, "awaiting_verification": 0, "verified": 1, "overdue": 1, "unassigned": 0, "total": 4}
    assert rollup_b.counts == {"open": 1, "in_progress": 0, "awaiting_verification": 1, "verified": 0, "overdue": 1, "unassigned": 1, "total": 2}
    assert [row.action_id for row in rollup_a.overdue] == [demo.action_ids["a_dr"]]
    assert [row.action_id for row in rollup_b.overdue] == [demo.action_ids["b_ir"]]
    assert [row.action_id for row in rollup_b.awaiting_verification] == [demo.action_ids["b_mfa"]]
    assert http.get(f"/engagements/{engagement_a.id}/remediation").status_code == 200
    assert 'data-rollup-count="total"' in http.get(f"/engagements/{engagement_a.id}/remediation").text
    assert "4" in http.get(f"/engagements/{engagement_a.id}/remediation").text
    assert "2" in http.get(f"/engagements/{engagement_b.id}/remediation").text
    snapshot = db.query(ReportSnapshot).one()
    assert snapshot.type == "integrated_report" and snapshot.engagement_id == engagement_a.id and snapshot.is_issued is True
    source = generated_event(db, snapshot.id)["source"]
    assert [item["assessment_id"] for item in source["assessments"]] == sorted([demo.assessment_ids["baseline"], demo.assessment_ids["validation"]])
    assert db.get(Assessment, demo.assessment_ids["baseline"]).review_status == "approved"
    assert db.get(Assessment, demo.assessment_ids["validation"]).review_status == "approved"
    assert db.get(Assessment, demo.assessment_ids["nist"]).review_status != "approved"
    assert http.get(f"/engagements/{engagement_a.id}/integrated-reports").status_code == 200
    assert http.get(f"/engagements/{engagement_b.id}/integrated-reports").status_code == 200
    assert report_content.integrated_report(db, engagement_b).sections == []


def test_scenario_10_magic_link_intake_is_client_scoped(db, http, demo):
    """Scenario 10: the client uploads two requested items and leaves one outstanding."""
    link_id = demo.magic_link_id
    policy = db.get(Evidence, demo.evidence_ids["b_policy"])
    mfa = db.get(Evidence, demo.evidence_ids["b_mfa_export"])
    fix = db.get(Evidence, demo.evidence_ids["b_mfa_fix"])
    assert policy.uploaded_by == mfa.uploaded_by == f"client_link:{link_id}"
    assert policy.assessment_id is None and mfa.assessment_id is None
    assert fix.uploaded_by == "consultant" and fix.assessment_id == demo.assessment_ids["nist"]
    upload_events = db.query(AuditEvent).filter_by(action="magic_link.upload_received").all()
    assert {json.loads(row.metadata_json)["item_key"] for row in upload_events} == {"item-1", "item-2"}
    assert all("item-3" not in row.metadata_json for row in upload_events)
    rows = magic_links.magic_link_rows(db, demo.engagement_ids["b"])
    assert len(rows) == 1 and rows[0]["status"] == "active" and rows[0]["uploads_used"] == 2
    assert rows[0]["items"] == ["Information security policy", "MFA enforcement export", "Incident response plan"]
    assert not any(re.fullmatch(r"[A-Za-z0-9_-]{22}", str(value)) for value in vars(demo).values())


def test_scenario_11_seed_is_idempotently_refused(db, http, demo, upload_root, tmp_path):
    """Scenario 11: rerunning refuses before changing rows or blobs."""
    counts_before = {table: db.query(model).count() for table, model in {
        "clients": Client, "engagements": Engagement, "assessments": Assessment,
        "assessment_packs": AssessmentPack, "evidence": Evidence, "evidence_versions": EvidenceVersion,
        "evidence_uses": EvidenceUse, "conclusions": Conclusion, "findings": Finding,
        "actions": Action, "magic_links": MagicLink, "report_snapshots": ReportSnapshot,
    }.items()}
    blobs_before = sorted(str(path.relative_to(upload_root)) for path in upload_root.rglob("*") if path.is_file())
    with pytest.raises(DemoAlreadySeeded) as exc_info:
        seed_longitudinal_demo(db, http)
    assert exc_info.value.message == DemoAlreadySeeded.message
    assert counts_before == {table: db.query(model).count() for table, model in {
        "clients": Client, "engagements": Engagement, "assessments": Assessment,
        "assessment_packs": AssessmentPack, "evidence": Evidence, "evidence_versions": EvidenceVersion,
        "evidence_uses": EvidenceUse, "conclusions": Conclusion, "findings": Finding,
        "actions": Action, "magic_links": MagicLink, "report_snapshots": ReportSnapshot,
    }.items()}
    assert blobs_before == sorted(str(path.relative_to(upload_root)) for path in upload_root.rglob("*") if path.is_file())
    other_path = tmp_path / "guard.sqlite3"
    command.upgrade(_alembic_config(other_path), "head")
    other_engine = create_engine(f"sqlite:///{other_path}")
    OtherSession = sessionmaker(bind=other_engine)
    other_db = OtherSession()
    other_db.add(Client(name=DEMO_CLIENT_B, industry="it_services", size="startup"))
    other_db.commit()
    try:
        with pytest.raises(DemoAlreadySeeded):
            seed_longitudinal_demo(other_db, None)
    finally:
        other_db.close()
        other_engine.dispose()


def test_scenario_12_structural_guards(db, http, demo):
    """Scenario 12: route, source, template, and signature guards stay narrow."""
    routes = sorted((method, route.path) for route in app.routes if "/evidence-reuse" in route.path for method in route.methods)
    assert routes == [
        ("GET", "/assessments/{assessment_id}/evidence-reuse"),
        ("POST", "/assessments/{assessment_id}/evidence-reuse/{source_use_id}/confirm"),
    ]
    service_source = Path("app/services/evidence_reuse.py").read_text()
    router_source = Path("app/routers/evidence_reuse.py").read_text()
    template_source = Path("app/templates/pages/evidence_reuse.html").read_text()
    assert ".commit(" not in service_source
    assert "db.delete(" not in service_source
    assert "session.delete(" not in service_source
    assert "delete" not in service_source.lower()
    assert ".commit(" not in inspect.getsource(web.assessment_detail)
    assert re.search(r"confirm all|select all|approve all|\bmultiple\b|\|\s*safe\b|bulk", service_source + router_source + template_source, re.I) is None
    assert template_source.count('type="checkbox"') == 1
    assert "CyberAssess" not in template_source
    assert "overall_score" not in template_source
    from scripts import seed_test_companies

    assert "SessionLocal" not in inspect.getsource(seed_test_companies.seed_longitudinal_demo)
    assert "settings.database_url" not in inspect.getsource(seed_test_companies.seed_longitudinal_demo)
    assert "print(" not in inspect.getsource(seed_test_companies.seed_longitudinal_demo)
    assert "create_backup(" in inspect.getsource(seed_test_companies.seed_longitudinal_cli)
    assert "token" not in inspect.getsource(seed_test_companies.seed_longitudinal_cli).lower()
    signature = inspect.signature(evidence_reuse.confirm_reuse)
    assert "acknowledge_warnings" in signature.parameters
    assert all("list" not in str(parameter.annotation) for parameter in signature.parameters.values())


def test_scenario_13_protected_surface_is_unchanged(db, http, demo):
    """Scenario 13: the full-contract protected files remain outside the diff."""
    # P6-1: explicit llm_calls persistence (D-P6-1-E)
    protected = [
        "app/routers/web.py", "app/services/evidence.py", "app/services/magic_links.py",
        "app/services/findings.py", "app/services/remediation_rollup.py", "app/services/report_content.py",
        "app/services/report_snapshots.py", "app/routers/magic.py",
        "app/routers/evidence.py", "scripts/backup.py", "scripts/migrate_legacy.py",
        "requirements.txt", "tests/test_phase1_prefill.py",
    ]
    changed = subprocess.run(
        ["git", "diff", "--name-only", "--", *protected],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    assert changed == []
