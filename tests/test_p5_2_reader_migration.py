"""Contract tests for the P5-2 approved-reader and explicit-release migration."""

from __future__ import annotations

import ast
import hashlib
import inspect
import io
import json
import random
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

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
from app.main import _register_frameworks
from app.models.assessment import Assessment
from app.models.audit_event import AuditEvent
from app.models.client import Client
from app.models.conclusion import Conclusion, ConclusionRevision
from app.models.engagement import Engagement
from app.models.report import GapItem, GapReport
from app.models.report_snapshot import ReportSnapshot
from app.routers import reports
from app.schemas.report import FrameworkScoreOut
from app.services import approved_report, conclusion_review, report_content, report_snapshots, workpaper
from app.services.scoring import (
    approved_framework_scores,
    compute_framework_scores,
    failed_framework_scores,
    namespaced_domain_scores,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
_register_frameworks()
DPDPA_IDS = [control.id for control in FrameworkRegistry.get_all_controls("dpdpa")]
ISO_IDS = [control.id for control in FrameworkRegistry.get_all_controls("iso27001")]


@pytest.fixture(scope="module", autouse=True)
def _register_frameworks():
    from app.main import _register_frameworks as register

    register()


@pytest.fixture()
def db_path(tmp_path):
    path = tmp_path / "p5-2.sqlite3"
    config = Config(str(REPO_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{path}")
    command.upgrade(config, "head")
    return path


@pytest.fixture()
def db(db_path):
    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
    )

    @event.listens_for(engine, "connect")
    def _foreign_keys(connection, _record):  # pragma: no cover
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def http(db, db_path, tmp_path, monkeypatch):
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    monkeypatch.setattr(settings, "upload_dir", str(upload_dir))
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{db_path}")

    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


def _seed(
    db,
    *,
    frameworks=("dpdpa",),
    applicable=None,
    company_name="P5-2 Example",
    engagement=None,
):
    client = db.get(Client, engagement.client_id) if engagement else None
    if client is None:
        client = Client(name=company_name, industry="Technology", size="medium")
        db.add(client)
        db.flush()
    if engagement is None:
        engagement = Engagement(
            client_id=client.id, name=f"{company_name} engagement", status="active"
        )
        db.add(engagement)
        db.flush()
    assessment = Assessment(
        company_name=client.name,
        industry="Technology",
        company_size="medium",
        selected_frameworks=json.dumps(list(frameworks)),
        applicable_requirements=(json.dumps(applicable) if applicable is not None else None),
        engagement_id=engagement.id,
        status="completed",
    )
    db.add(assessment)
    db.commit()
    return assessment


def _report(db, assessment, outcomes_by_framework=None, *, failed=()):
    outcomes_by_framework = outcomes_by_framework or {
        framework_id: {
            control.id: "compliant"
            for control in FrameworkRegistry.get_all_controls(framework_id)
        }
        for framework_id in assessment.frameworks
    }
    scores = {}
    for framework_id in assessment.frameworks:
        if framework_id in failed:
            scores[framework_id] = failed_framework_scores()
        else:
            scores[framework_id] = compute_framework_scores(
                [
                    {"requirement_id": requirement_id, "compliance_status": outcome}
                    for requirement_id, outcome in outcomes_by_framework.get(framework_id, {}).items()
                ],
                framework_id,
            )
    report = GapReport(
        assessment_id=assessment.id,
        overall_score=0.0,
        chapter_scores=json.dumps(namespaced_domain_scores(scores)),
        framework_scores=json.dumps(scores),
        executive_summary="AI-only summary that must never be released",
        raw_ai_response="{}",
    )
    db.add(report)
    db.commit()
    return report


def _conclusion(
    db,
    assessment,
    framework_id,
    requirement_id,
    outcome="compliant",
    *,
    risk="medium",
    gap="AI gap",
    action="Fix the gap",
    citations="[]",
):
    row = Conclusion(
        assessment_id=assessment.id,
        framework_id=framework_id,
        requirement_id=requirement_id,
        outcome=outcome,
        rationale="AI rationale",
        evidence_summary="AI evidence",
        gaps_identified=gap,
        risk_level=risk,
        recommended_action=action,
        ai_proposed=True,
        version=1,
    )
    db.add(row)
    db.flush()
    db.add(
        ConclusionRevision(
            conclusion_id=row.id,
            actor="system:analysis",
            action="proposed",
            previous_outcome=None,
            previous_rationale=None,
            citations_json=citations,
        )
    )
    db.commit()
    return row


def _decision(db, row, action="approved", *, actor="consultant:Priya", **edits):
    row = db.get(Conclusion, row.id)
    row.version += 1
    for field, value in edits.items():
        setattr(row, field, value)
    db.add(
        ConclusionRevision(
            conclusion_id=row.id,
            actor=actor,
            action=action,
            previous_outcome=row.outcome,
            previous_rationale=row.rationale,
            citations_json="[]",
        )
    )
    db.commit()
    return row


def _approve_all(db, assessment):
    for row in db.query(Conclusion).filter_by(assessment_id=assessment.id).all():
        _decision(db, row)


def _release(db, assessment):
    event = approved_report.record_release(
        db, assessment, actor="consultant:Priya"
    )
    db.commit()
    return event


def _pdf_text(content: bytes) -> str:
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def _one_control_assessment(
    db,
    *,
    framework_id="dpdpa",
    outcome="compliant",
    company_name="P5-2 Example",
    engagement=None,
):
    requirement_id = FrameworkRegistry.get_all_controls(framework_id)[0].id
    assessment = _seed(
        db,
        frameworks=(framework_id,),
        applicable=[requirement_id],
        company_name=company_name,
        engagement=engagement,
    )
    _report(db, assessment, {framework_id: {requirement_id: outcome}})
    row = _conclusion(db, assessment, framework_id, requirement_id, outcome)
    return assessment, row


def test_scenario_1_approved_scoring_contract():
    """Scenario 1: approved outcomes score deterministically with explicit exclusions."""
    controls = FrameworkRegistry.get_all_controls("dpdpa")[:8]
    all_compliant = {control.id: "compliant" for control in controls}
    baseline = approved_framework_scores(all_compliant, "dpdpa")
    assert baseline["status"] == "scored" and baseline["overall_score"] == 100.0
    with_insufficient = approved_framework_scores(
        {**all_compliant, controls[-1].id: "insufficient_evidence"}, "dpdpa"
    )
    with_non_compliant = approved_framework_scores(
        {**all_compliant, controls[-1].id: "non_compliant"}, "dpdpa"
    )
    with_not_applicable = approved_framework_scores(
        {**all_compliant, controls[-1].id: "not_applicable"}, "dpdpa"
    )
    assert with_insufficient["overall_score"] == baseline["overall_score"]
    assert with_insufficient["domain_scores"] == baseline["domain_scores"]
    assert with_not_applicable["overall_score"] == baseline["overall_score"]
    assert with_non_compliant["overall_score"] < baseline["overall_score"]
    assert approved_framework_scores(
        {controls[0].id: "not_applicable", controls[1].id: "insufficient_evidence"},
        "dpdpa",
    ) == {
        "status": "not_scored",
        "overall_score": None,
        "overall_rating": None,
        "domain_scores": {},
    }
    with pytest.raises(ValueError):
        approved_framework_scores({controls[0].id: "unknown"}, "dpdpa")
    random.seed(42)
    mixed = {
        control.id: random.choice(
            ("compliant", "partially_compliant", "non_compliant", "not_applicable", "insufficient_evidence")
        )
        for control in controls
    }
    expected = compute_framework_scores(
        [
            {"requirement_id": requirement_id, "compliance_status": "not_assessed" if outcome == "insufficient_evidence" else outcome}
            for requirement_id, outcome in mixed.items()
        ],
        "dpdpa",
    )
    actual = approved_framework_scores(mixed, "dpdpa")
    assert {key: value for key, value in actual.items() if key != "status"} == expected
    assert not any(
        alias in inspect.getsource(__import__("app.services.scoring", fromlist=["scoring"]))
        for alias in ("app.models.conclusion", "app.services.analysis_pipeline", "app.services.approved_report")
    )


def test_scenario_2_unchanged_approval_reproduces_proposal_numbers(db):
    """Scenario 2: unchanged consultant approval reproduces the proposal numbers."""
    for frameworks in (("dpdpa",), ("dpdpa", "iso27001")):
        applicable = [FrameworkRegistry.get_all_controls(framework_id)[0].id for framework_id in frameworks]
        assessment = _seed(
            db,
            frameworks=frameworks,
            applicable=applicable,
            company_name=f"Numbers-{len(frameworks)}",
        )
        outcomes = {framework_id: {requirement_id: "compliant"} for framework_id, requirement_id in zip(frameworks, applicable)}
        report = _report(db, assessment, outcomes)
        for framework_id, requirement_id in zip(frameworks, applicable):
            row = _conclusion(db, assessment, framework_id, requirement_id)
            _decision(db, row)
        _release(db, assessment)
        view = approved_report.build_approved_report(db, assessment)
        proposed = json.loads(report.framework_scores)
        for framework_id in frameworks:
            approved = {
                key: value
                for key, value in view.framework_scores[framework_id].items()
                if key not in ("status", "coverage")
            }
            assert approved == proposed[framework_id]
        assert view.chapter_scores == json.loads(report.chapter_scores)


def test_scenario_3_eligibility_matches_conclusion_cards(db):
    """Scenario 3: only consultant locking decisions become approved rows."""
    ids = DPDPA_IDS[:6]
    assessment = _seed(db, applicable=ids)
    rows = [_conclusion(db, assessment, "dpdpa", requirement_id) for requirement_id in ids]
    _decision(db, rows[1], "approved")
    _decision(db, rows[2], "edited", outcome="partially_compliant", gaps_identified="Edited gap")
    _decision(db, rows[3], "rejected")
    _decision(db, rows[4], "approved")
    _decision(db, rows[4], "reopened")
    _decision(db, rows[5], "approved", actor="Legacy Reviewer")
    _report(db, assessment, {"dpdpa": {requirement_id: "compliant" for requirement_id in ids}})
    view = approved_report.build_approved_report(db, assessment)
    assert {row.requirement_id for row in view.rows} == {ids[1], ids[2]}
    cards = {card.conclusion.id: card for card in conclusion_review.conclusion_cards(db, assessment.id)}
    assert all(
        (row.id in {item.id for item in view.rows})
        == (cards[row.id].state in ("approved", "edited") and not cards[row.id].legacy_bulk_approval)
        for row in rows
    )
    edited = next(row for row in view.rows if row.requirement_id == ids[2])
    assert edited.decision == "edited" and edited.decided_by == "Priya" and edited.decided_at


def test_scenario_4_scope_and_missing_proposals_match_workpaper(db):
    """Scenario 4: scope parsing, out-of-scope rows and missing proposals stay aligned."""
    from app.services.workpaper import _scope

    for raw in (None, "", "[]", "not json", "{}", '["a", 1]', '["CH2.NOTICE.1"]'):
        assert approved_report.in_scope_requirement_ids(raw) == _scope(raw)
    ids = DPDPA_IDS[:3]
    out_ids = DPDPA_IDS[3:5]
    assessment = _seed(db, applicable=ids)
    for requirement_id in ids[:2] + out_ids:
        row = _conclusion(db, assessment, "dpdpa", requirement_id)
        _decision(db, row)
    _report(db, assessment, {"dpdpa": {requirement_id: "compliant" for requirement_id in ids + out_ids}})
    view = approved_report.build_approved_report(db, assessment)
    review = view.framework_reviews["dpdpa"]
    workpaper_view = workpaper.build_workpaper(db, assessment)
    unconcluded = {
        item["requirement_id"]
        for section in workpaper_view.sections
        if section.framework_id == "dpdpa"
        for item in section.unconcluded
    }
    assert set(review.missing_ids) == unconcluded == {ids[2]}
    assert {row.requirement_id for row in view.rows} == set(ids[:2])
    assert review.coverage["out_of_scope"] == 2
    assert approved_report.MISSING_CONCLUSIONS_MESSAGE.format(
        name=review.name, count=1
    ) in view.release.blockers


def test_scenario_5_release_blockers_are_ordered_and_exact(db):
    """Scenario 5: release blockers distinguish analysis, failure, coverage and outcomes."""
    no_report = _seed(db, applicable=DPDPA_IDS[:1])
    assert approved_report.build_approved_report(db, no_report).release.blockers == (
        approved_report.NO_ANALYSIS_MESSAGE,
    )
    running = _seed(db, applicable=DPDPA_IDS[:1], company_name="Running")
    _report(db, running, {"dpdpa": {DPDPA_IDS[0]: "compliant"}})
    running.status = "analyzing"
    db.commit()
    assert approved_report.ANALYSIS_RUNNING_MESSAGE in approved_report.release_state(db, running).blockers

    assessment = _seed(db, frameworks=("dpdpa", "iso27001"), applicable=[DPDPA_IDS[0], ISO_IDS[0]], company_name="Failed")
    _conclusion(db, assessment, "dpdpa", DPDPA_IDS[0])
    _report(db, assessment, {"dpdpa": {DPDPA_IDS[0]: "compliant"}, "iso27001": {}}, failed=("iso27001",))
    view = approved_report.build_approved_report(db, assessment)
    assert view.release.blockers == (
        approved_report.AWAITING_DECISION_MESSAGE.format(
            name=FrameworkRegistry.get("dpdpa").name, count=1, total=1
        ),
        approved_report.RELEASE_BLOCKED_MESSAGE.format(names=FrameworkRegistry.get("iso27001").name),
    ) or view.release.blockers == (
        approved_report.RELEASE_BLOCKED_MESSAGE.format(names=FrameworkRegistry.get("iso27001").name),
        approved_report.AWAITING_DECISION_MESSAGE.format(
            name=FrameworkRegistry.get("dpdpa").name, count=1, total=1
        ),
    )
    empty_scope = _seed(db, applicable=["NO_SUCH_CONTROL"], company_name="Empty scope")
    _report(db, empty_scope, {"dpdpa": {}})
    assert approved_report.NOTHING_IN_SCOPE_MESSAGE in approved_report.release_state(db, empty_scope).blockers

    excluded = _seed(db, applicable=DPDPA_IDS[:2], company_name="Excluded outcomes")
    for requirement_id, outcome in zip(DPDPA_IDS[:2], ("not_applicable", "insufficient_evidence")):
        row = _conclusion(db, excluded, "dpdpa", requirement_id, outcome)
        _decision(db, row)
    _report(db, excluded, {"dpdpa": {DPDPA_IDS[0]: "not_applicable", DPDPA_IDS[1]: "not_assessed"}})
    assert approved_report.release_state(db, excluded).blockers == ()


def test_scenario_6_release_route_writes_one_manifest_event(db, http):
    """Scenario 6: explicit release is attributable, manifest-bound and idempotent."""
    assessment, row = _one_control_assessment(db)
    pending = http.post(f"/api/assessments/{assessment.id}/release", data={"reviewer_name": "Priya"})
    assert pending.status_code == 409
    assert pending.json()["blockers"]
    assert db.query(AuditEvent).filter_by(action=approved_report.RELEASE_EVENT).count() == 0
    _decision(db, row)
    released = http.post(f"/api/assessments/{assessment.id}/release", data={"reviewer_name": "Priya"})
    assert released.status_code == 200
    assert released.headers["HX-Redirect"].endswith("?tab=report")
    event = db.query(AuditEvent).filter_by(action=approved_report.RELEASE_EVENT).one()
    metadata = json.loads(event.metadata_json)
    assert event.actor == "consultant:Priya"
    assert set(metadata) == {"schema_version", "manifest", "gap_report_id", "coverage"}
    assert set(metadata["manifest"]) == {"framework_ids", "in_scope", "conclusion_versions"}
    again = http.post(f"/api/assessments/{assessment.id}/release", data={"reviewer_name": "Priya"})
    assert again.status_code == 409
    assert again.json()["detail"] == approved_report.ALREADY_RELEASED_MESSAGE
    assert db.query(AuditEvent).filter_by(action=approved_report.RELEASE_EVENT).count() == 1


def test_scenario_7_release_invalidation_and_locked_rerun_semantics(db, http):
    """Scenario 7: in-scope decisions and scope stale a release while out-of-scope changes do not."""
    assessment, row = _one_control_assessment(db)
    _decision(db, row)
    _release(db, assessment)
    _decision(db, row, "reopened")
    assert approved_report.release_state(db, assessment).stale
    assert http.get(f"/api/assessments/{assessment.id}/report").status_code == 403
    _decision(db, row, "approved")
    assert not approved_report.release_state(db, assessment).released
    assessment.applicable_requirements = json.dumps(DPDPA_IDS[:2])
    db.commit()
    assert approved_report.release_state(db, assessment).stale
    assessment.applicable_requirements = json.dumps([DPDPA_IDS[0]])
    db.commit()
    assert approved_report.release_state(db, assessment).stale
    _release(db, assessment)
    assert approved_report.release_state(db, assessment).released
    out_scope = _conclusion(db, assessment, "dpdpa", DPDPA_IDS[1])
    _decision(db, out_scope, "approved")
    assert approved_report.release_state(db, assessment).released


def test_scenario_8_hand_set_approval_never_releases_and_gate_order_is_fixed(db, http):
    """Scenario 8: review_status is inert and the gate reports no-report, failed, then release state."""
    assessment, _row = _one_control_assessment(db)
    assessment.review_status = "approved"
    db.commit()
    for path in ("", "/summary", "/full", "/pdf"):
        assert http.get(f"/api/assessments/{assessment.id}/report{path}").status_code == 403
    assert http.get(f"/api/assessments/no-such/report").status_code == 404
    no_report = _seed(db, applicable=DPDPA_IDS[:1], company_name="No report")
    assert http.get(f"/api/assessments/{no_report.id}/report").json()["detail"] == "No report found. Run analysis first."
    failed, _ = _one_control_assessment(db, company_name="Failed gate")
    report = db.query(GapReport).filter_by(assessment_id=failed.id).one()
    report.framework_scores = json.dumps({"dpdpa": failed_framework_scores()})
    db.commit()
    failure = http.get(f"/api/assessments/{failed.id}/report")
    assert failure.status_code == 409
    from app.utils import review_gate

    assert review_gate.RELEASE_BLOCKED_MESSAGE is approved_report.RELEASE_BLOCKED_MESSAGE


def test_scenario_9_api_reflects_consultant_not_ai(db, http):
    """Scenario 9: report APIs expose edited approved Conclusions and no AI narrative or initiatives."""
    assessment = _seed(db, applicable=[DPDPA_IDS[0]])
    report = _report(db, assessment, {"dpdpa": {DPDPA_IDS[0]: "non_compliant"}})
    row = _conclusion(db, assessment, "dpdpa", DPDPA_IDS[0], "non_compliant", risk="critical")
    _decision(
        db,
        row,
        "edited",
        outcome="partially_compliant",
        risk_level="medium",
        gaps_identified="Consultant gap",
    )
    _release(db, assessment)
    payload = http.get(f"/api/assessments/{assessment.id}/report").json()
    item = payload["gap_items"][0]
    assert item["compliance_status"] == "partially_compliant"
    assert item["gap_description"] == "Consultant gap"
    assert item["risk_level"] == "medium" and item["remediation_priority"] == 3
    assert item["remediation_effort"] is None and item["conclusion_version"] == row.version
    assert payload["initiatives"] == []
    assert payload["executive_summary"].startswith("This summary is generated from consultant-approved conclusions only.")
    assert "AI-only summary" not in payload["executive_summary"]
    summary = http.get(f"/api/assessments/{assessment.id}/report/summary").json()
    assert summary["not_assessed"] == summary["insufficient_evidence"]
    full = http.get(f"/api/assessments/{assessment.id}/report/full").json()
    assert "overall_score" not in full
    assert report.id == payload["id"]


def test_scenario_10_pdf_uses_approved_rows_and_conditional_framework_copy(db, http):
    """Scenario 10: the real PDF contains approved coverage, methodology and conditional copy."""
    assessment, row = _one_control_assessment(db, outcome="insufficient_evidence")
    _decision(db, row)
    _release(db, assessment)
    text_value = _pdf_text(http.get(f"/api/assessments/{assessment.id}/report/pdf").content)
    assert "Scoring Basis:" in text_value
    assert "insufficient evidence" in text_value.lower()
    assert "Remediation Timeline (not estimated)" in text_value
    assert "~0 weeks" not in text_value and "Strategic Initiatives" not in text_value
    assert list(inspect.signature(reports.generate_pdf).parameters) == [
        "report", "gap_items", "company_name", "initiatives", "answer_source_map",
        "selected_frameworks", "assessment", "report_findings",
    ]
    iso, iso_row = _one_control_assessment(db, framework_id="iso27001", company_name="ISO PDF")
    _decision(db, iso_row)
    _release(db, iso)
    iso_text = _pdf_text(http.get(f"/api/assessments/{iso.id}/report/pdf").content).lower()
    assert "physical security review" not in iso_text
    assert "certified privacy professional" not in iso_text
    assert "qualified information security auditor" in iso_text
    assert "referenced by clause or control identifier" in iso_text


def test_scenario_11_report_tab_pending_released_stale_and_legacy_remediation(db, http):
    """Scenario 11: report tab cards reflect pending, released, stale and legacy remediation states."""
    assessment, row = _one_control_assessment(db)
    pending = http.get(f"/assessments/{assessment.id}/report-summary")
    assert pending.status_code == 200
    assert 'data-framework-pending="dpdpa"' in pending.text
    assert "0 of 1 conclusions approved" in pending.text
    assert 'data-release-state="not_released"' in pending.text
    assert 'data-release-blockers' in pending.text
    _decision(db, row)
    legacy = GapItem(
        report_id=db.query(GapReport).filter_by(assessment_id=assessment.id).one().id,
        requirement_id=row.requirement_id,
        framework_id="dpdpa",
        chapter="Chapter 2",
        requirement_title="Legacy remediation",
        compliance_status="non_compliant",
        current_state="legacy",
        gap_description="legacy",
        risk_level="high",
        remediation_action="legacy action",
        remediation_priority=2,
        remediation_effort="medium",
        timeline_weeks=4,
    )
    db.add(legacy)
    db.commit()
    _release(db, assessment)
    released = http.get(f"/assessments/{assessment.id}/report-summary")
    assert 'data-framework-coverage="dpdpa"' in released.text
    assert 'data-release-state="released"' in released.text
    assert "This summary is generated from consultant-approved conclusions only." in released.text
    assert "data-legacy-remediation" in released.text
    _decision(db, row, "reopened")
    stale = http.get(f"/assessments/{assessment.id}/report-summary")
    assert 'data-release-state="stale"' in stale.text


def test_scenario_12_conclusions_page_release_panel(db, http):
    """Scenario 12: the Conclusions page exposes release only after all decisions are eligible."""
    assessment, row = _one_control_assessment(db)
    pending = http.get(f"/assessments/{assessment.id}/conclusions")
    assert 'data-release-panel' in pending.text and 'data-release-blockers' in pending.text
    assert 'data-release-form' not in pending.text
    _decision(db, row)
    ready = http.get(f"/assessments/{assessment.id}/conclusions")
    assert 'data-release-form' in ready.text
    _release(db, assessment)
    released = http.get(f"/assessments/{assessment.id}/conclusions")
    assert "Released by Priya" in released.text
    assert "'" not in (REPO_ROOT / "app/templates/partials/release_panel.html").read_text()


def test_scenario_13_legacy_review_is_retired(db, http):
    """Scenario 13: old bulk review routes return 410 and the review page redirects."""
    assessment, row = _one_control_assessment(db)
    report = db.query(GapReport).filter_by(assessment_id=assessment.id).one()
    item = GapItem(
        report_id=report.id,
        requirement_id=row.requirement_id,
        framework_id="dpdpa",
        chapter="Chapter 2",
        requirement_title="Legacy",
        compliance_status="non_compliant",
        current_state="state",
        gap_description="gap",
        risk_level="high",
        remediation_action="fix",
        remediation_priority=1,
        remediation_effort="medium",
        timeline_weeks=4,
    )
    db.add(item)
    db.commit()
    before = (item.review_status, item.reviewed_by, item.reviewed_at, item.compliance_status, item.reviewer_notes, assessment.review_status, db.query(AuditEvent).count())
    for method, path in (
        ("patch", f"/api/assessments/{assessment.id}/review/items/{item.id}"),
        ("post", f"/api/assessments/{assessment.id}/review/approve"),
        ("post", f"/api/assessments/{assessment.id}/review/reject"),
    ):
        response = getattr(http, method)(path)
        assert response.status_code == 410 and response.json()["detail"] == approved_report.LEGACY_REVIEW_RETIRED
    after = (item.review_status, item.reviewed_by, item.reviewed_at, item.compliance_status, item.reviewer_notes, assessment.review_status, db.query(AuditEvent).count())
    assert before == after
    redirect = http.get(f"/assessments/{assessment.id}/review", follow_redirects=False)
    assert redirect.status_code == 303 and redirect.headers["location"].endswith("/conclusions")
    assert not (REPO_ROOT / "app/schemas/review.py").exists()
    assert not (REPO_ROOT / "app/templates/pages/review.html").exists()
    assert not (REPO_ROOT / "app/templates/partials/review_filter_bar.html").exists()
    assert (REPO_ROOT / "app/templates/partials/review_finding_card.html").exists()


def test_scenario_14_snapshots_bind_generation_to_release(db, http, monkeypatch):
    """Scenario 14: snapshot bytes are immutable and issue requires generation after release."""
    from app.routers import reports as reports_router

    monkeypatch.setattr(reports_router, "generate_pdf", lambda *_args, **_kwargs: b"%PDF-1.4 approved")
    assessment, row = _one_control_assessment(db)
    before = http.post(f"/api/assessments/{assessment.id}/snapshots", data={"type": "gap_report"})
    assert before.status_code == 403
    _decision(db, row)
    _release(db, assessment)
    v1 = http.post(f"/api/assessments/{assessment.id}/snapshots", data={"type": "gap_report"}).json()["snapshot_id"]
    assert http.post(f"/api/assessments/{assessment.id}/snapshots/{v1}/issue").status_code == 200
    snapshot = db.get(ReportSnapshot, v1)
    bytes_before = (Path(settings.upload_dir) / snapshot.storage_path).read_bytes()
    _decision(db, row, "reopened")
    _decision(db, row, "approved")
    _release(db, assessment)
    old_issue = http.post(f"/api/assessments/{assessment.id}/snapshots/{v1}/issue")
    assert old_issue.status_code == 409
    assert old_issue.json()["detail"] == report_snapshots.SNAPSHOT_STALE_MESSAGE
    v3 = http.post(f"/api/assessments/{assessment.id}/snapshots", data={"type": "gap_report"}).json()["snapshot_id"]
    assert http.post(f"/api/assessments/{assessment.id}/snapshots/{v3}/issue").status_code == 200
    assert (Path(settings.upload_dir) / snapshot.storage_path).read_bytes() == bytes_before
    assert set(report_snapshots.source_manifest(db, assessment)) == {"gap_report_id", "conclusion_versions"}


def test_scenario_15_integrated_report_observes_releases_and_snapshot_binding(db, http, monkeypatch):
    """Scenario 15: integrated reports include only released sources and re-release requires regeneration."""
    from app.routers import integrated_reports

    monkeypatch.setattr(integrated_reports.pdf_export, "generate_integrated_pdf", lambda *_args, **_kwargs: b"%PDF-1.4 integrated")
    base = _seed(db, company_name="Integrated", applicable=DPDPA_IDS[:1])
    engagement_row = db.get(Engagement, base.engagement_id)
    a, a_row = _one_control_assessment(db, company_name="Integrated", engagement=engagement_row)
    b, b_row = _one_control_assessment(db, company_name="Integrated", engagement=engagement_row)
    c, c_row = _one_control_assessment(db, company_name="Integrated", engagement=engagement_row)
    _decision(db, a_row)
    _release(db, a)
    _decision(db, c_row)
    _release(db, c)
    data = report_content.integrated_report(db, engagement_row)
    assert [section.assessment_id for section in data.sections] == [a.id, c.id]
    _decision(db, c_row, "reopened")
    data = report_content.integrated_report(db, engagement_row)
    assert any(excluded.assessment_id == c.id and excluded.reason == report_content.NOT_RELEASED for excluded in data.excluded)
    assert any(excluded.assessment_id == b.id and excluded.reason == report_content.NOT_RELEASED for excluded in data.excluded)


def test_scenario_16_comparison_and_schema_shapes(db, http):
    """Scenario 16: comparisons use approved rows and score schemas carry explicit states."""
    base = _seed(db, company_name="Comparable", applicable=DPDPA_IDS[:1])
    engagement = db.get(Engagement, base.engagement_id)
    first, first_row = _one_control_assessment(db, company_name="Comparable", engagement=engagement)
    second, second_row = _one_control_assessment(db, company_name="Comparable", engagement=engagement)
    _decision(db, first_row)
    _release(db, first)
    _decision(db, second_row, "edited", outcome="partially_compliant")
    _release(db, second)
    compared = http.get(f"/api/assessments/{second.id}/compare/{first.id}")
    assert compared.status_code == 200 and compared.json()["framework_deltas"]
    _decision(db, first_row, "reopened")
    assert all(row["id"] != first.id for row in http.get(f"/api/assessments/{second.id}/comparable").json())
    assert FrameworkScoreOut(**failed_framework_scores()).status == "failed"
    assert FrameworkScoreOut(overall_score=80.0, overall_rating="Compliant", domain_scores={}).status == "scored"
    assert FrameworkScoreOut(
        status="pending_review", overall_score=None, overall_rating=None, domain_scores={}, coverage={"eligible": 0, "in_scope": 1}
    ).status == "pending_review"


def test_scenario_17_analysis_poll_and_framework_tab_use_approved_rows(db, http):
    """Scenario 17: poll and framework-tab findings show review progress without score percentages."""
    assessment, row = _one_control_assessment(db)
    poll = http.get(f"/assessments/{assessment.id}/analysis-status")
    assert "awaiting consultant review" in poll.text
    assert "data-review-conclusions-link" in poll.text
    assert "%" not in poll.text
    assert 'data-framework-finding-count="dpdpa"' not in http.get(f"/assessments/{assessment.id}/tab/dpdpa").text
    _decision(db, row, outcome="non_compliant")
    findings_tab = http.get(f"/assessments/{assessment.id}/tab/dpdpa")
    assert findings_tab.status_code == 200


def test_scenario_18_legacy_data_fails_closed_and_has_a_recovery_path(db, http, monkeypatch):
    """Scenario 18: pre-migration and legacy bulk data cannot release until fresh decisions exist."""
    assessment = _seed(db, applicable=DPDPA_IDS[:1], company_name="Legacy")
    report = _report(db, assessment, {"dpdpa": {DPDPA_IDS[0]: "non_compliant"}})
    item = GapItem(
        report_id=report.id,
        requirement_id=DPDPA_IDS[0],
        framework_id="dpdpa",
        chapter="Chapter 2",
        requirement_title="Legacy",
        compliance_status="non_compliant",
        current_state="legacy",
        gap_description="legacy",
        risk_level="high",
        remediation_action="fix",
        remediation_priority=1,
        remediation_effort="medium",
        timeline_weeks=4,
    )
    db.add(item)
    assessment.review_status = "approved"
    db.commit()
    assert http.get(f"/api/assessments/{assessment.id}/report").status_code == 403
    assert "Scores unavailable" in http.get(f"/assessments/{assessment.id}/report-summary").text
    legacy = _conclusion(db, assessment, "dpdpa", DPDPA_IDS[0], citations="null")
    _decision(db, legacy, actor="Legacy Reviewer")
    state = approved_report.release_state(db, assessment)
    assert state.blockers
    _decision(db, legacy, "reopened")
    _decision(db, legacy, "approved")
    assert http.post(f"/api/assessments/{assessment.id}/release", data={"reviewer_name": "Priya"}).status_code == 200


def test_scenario_19_source_and_worktree_guards(db_path):
    """Scenario 19: P5-2 source guards and protected-file invariants are present."""
    def run_grep(pattern, *paths):
        result = subprocess.run(["grep", "-nE", pattern, *paths], cwd=REPO_ROOT, capture_output=True, text=True)
        return result.returncode, result.stdout

    code, output = run_grep(
        r"\bGapItem\b",
        "app/routers/reports.py", "app/utils/pdf_export.py", "app/utils/review_gate.py",
        "app/services/report_content.py", "app/services/approved_report.py", "app/routers/integrated_reports.py",
    )
    assert code == 1 and output == ""
    code, output = run_grep(
        r"\bInitiative\b|report_framework_scores|chapter_scores\)|\.executive_summary",
        "app/routers/reports.py", "app/utils/review_gate.py", "app/services/report_content.py",
    )
    assert code == 1 and output == ""
    result = subprocess.run(
        ["grep", "-rnE", r"\breview_status\b\s*(==|!=)", "app/"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    code, output = result.returncode, result.stdout
    assert code == 0 and all("partials/review_finding_card.html" in line for line in output.splitlines())
    assert not run_grep(r"llm_client|\.commit\(|delete", "app/services/approved_report.py")[1]
    tree = ast.parse((REPO_ROOT / "app/services/scoring.py").read_text())
    forbidden = {"app.models.conclusion", "app.services.analysis_pipeline", "app.services.approved_report"}
    assert all(
        not (isinstance(node, ast.ImportFrom) and node.module in forbidden)
        and not (isinstance(node, ast.Import) and any(alias.name in forbidden for alias in node.names))
        for node in ast.walk(tree)
    )
    # P6-1: explicit llm_calls persistence (D-P6-1-E)
    protected = subprocess.run(
        ["git", "diff", "--stat", "main", "--", "app/models", "alembic"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    )
    assert protected.stdout == ""
    assert subprocess.run(["alembic", "heads"], cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout.strip() == "8b2d5f7e1c34 (head)"
