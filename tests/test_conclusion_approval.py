"""Contract suite for P2-4 individual consultant approval of Conclusions."""

from __future__ import annotations

import copy
import inspect
import json
import subprocess
from datetime import datetime, timezone
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
from app.dpdpa.framework import get_all_requirements
from app.main import app
from app.models.assessment import Assessment
from app.models.client import Client
from app.models.conclusion import Conclusion, ConclusionRevision
from app.models.engagement import Engagement
from app.models.evidence import Evidence, EvidenceVersion
from app.models.questionnaire import QuestionnaireResponse
from app.models.report import GapItem, GapReport
from app.services import analysis_pipeline, conclusion_review

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
    path = tmp_path / "conclusion-approval.sqlite3"
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


def _run_one(db, gate, monkeypatch, *, item=None, client_name="Acme Corp"):
    assessment = _seed(db, client_name=client_name)
    _stub_single(monkeypatch, [item or _item(REQS[0])])
    gate.trigger_analysis(assessment.id, db)
    conclusion = db.query(Conclusion).filter_by(assessment_id=assessment.id).one()
    return assessment, conclusion


def _revisions(db, conclusion_id):
    db.expire_all()
    return (
        db.query(ConclusionRevision)
        .filter_by(conclusion_id=conclusion_id)
        .order_by(ConclusionRevision.created_at, text("conclusion_revisions.rowid"))
        .all()
    )


def _snapshot(db, conclusion):
    db.refresh(conclusion)
    return {
        "revision_ids": {row.id for row in _revisions(db, conclusion.id)},
        "version": conclusion.version,
        "outcome": conclusion.outcome,
        "rationale": conclusion.rationale,
        "evidence_summary": conclusion.evidence_summary,
        "gaps_identified": conclusion.gaps_identified,
        "risk_level": conclusion.risk_level,
        "recommended_action": conclusion.recommended_action,
        "ai_proposed": conclusion.ai_proposed,
        "updated_at": conclusion.updated_at,
    }


def _assert_snapshot(db, conclusion, expected):
    assert _snapshot(db, conclusion) == expected


def _url(assessment, conclusion, route):
    return f"/api/assessments/{assessment.id}/conclusions/{conclusion.id}/{route}"


def _edit_payload(version, **overrides):
    payload = {
        "expected_version": version,
        "reviewer_name": "Priya",
        "outcome": "non_compliant",
        "rationale": "Consultant rationale",
        "gaps_identified": "Consultant gap",
        "risk_level": "high",
        "recommended_action": "Consultant action",
    }
    payload.update(overrides)
    return payload


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


def test_scenario_1_approve_appends_one_revision_and_locks(db, http, gate, monkeypatch):
    """Scenario 1: approve preserves content, versions once, records the actor and locks."""
    assessment, conclusion = _run_one(db, gate, monkeypatch)
    before = _snapshot(db, conclusion)

    response = http.post(
        _url(assessment, conclusion, "approve"),
        data={"expected_version": 1, "reviewer_name": "Priya"},
    )

    assert response.status_code == 200
    assert f'id="conclusion-card-{conclusion.id}"' in response.text
    assert 'data-state="approved"' in response.text
    assert response.headers["X-Toast-Message"] == "Conclusion approved"
    db.refresh(conclusion)
    assert conclusion.version == 2
    for field in (
        "outcome",
        "rationale",
        "evidence_summary",
        "gaps_identified",
        "risk_level",
        "recommended_action",
        "ai_proposed",
    ):
        assert getattr(conclusion, field) == before[field]
    assert conclusion.updated_at > before["updated_at"]
    revision = _revisions(db, conclusion.id)[-1]
    assert (
        revision.action,
        revision.actor,
        revision.previous_outcome,
        revision.previous_rationale,
    ) == ("approved", "consultant:Priya", before["outcome"], before["rationale"])
    assert revision.citations_json is None and revision.analysis_run_id is None
    state = analysis_pipeline.load_conclusion_state(
        db, assessment_id=assessment.id, framework_id="dpdpa"
    )[conclusion.requirement_id]
    assert state.locked is True

    other, other_conclusion = _run_one(
        db, gate, monkeypatch, client_name="Blank Reviewer Corp"
    )
    assert http.post(
        _url(other, other_conclusion, "approve"), data={"expected_version": 1}
    ).status_code == 200
    assert _revisions(db, other_conclusion.id)[-1].actor == "consultant:Manager Review"


def test_scenario_2_concurrent_approval_returns_current_conflict_card(db, http, gate, monkeypatch):
    """Scenario 2: the second approval from the same rendered version is refused with 409."""
    assessment, conclusion = _run_one(db, gate, monkeypatch)
    payload = {"expected_version": 1, "reviewer_name": "Priya"}
    assert http.post(_url(assessment, conclusion, "approve"), data=payload).status_code == 200
    response = http.post(_url(assessment, conclusion, "approve"), data=payload)
    assert response.status_code == 409
    assert response.headers["X-Conclusion-Conflict"] == "1"
    assert response.headers["X-Toast-Message"] == (
        "Conflict: this conclusion changed since you loaded it. Nothing was saved."
    )
    assert "This conclusion changed since you loaded it" in response.text
    assert 'data-version="2"' in response.text
    assert 'name="expected_version" value="2"' in response.text
    assert [row.action for row in _revisions(db, conclusion.id)].count("approved") == 1


def test_scenario_3_cas_race_rolls_back_everything(db, http, gate, monkeypatch):
    """Scenario 3: a writer between state load and CAS produces a clean 409 rollback."""
    assessment, conclusion = _run_one(db, gate, monkeypatch)
    before = _snapshot(db, conclusion)
    real = analysis_pipeline.load_conclusion_state

    def racing_load(session, **kwargs):
        state = real(session, **kwargs)
        session.execute(
            text("UPDATE conclusions SET version = version + 1 WHERE id = :id"),
            {"id": conclusion.id},
        )
        return state

    monkeypatch.setattr(analysis_pipeline, "load_conclusion_state", racing_load)
    response = http.post(
        _url(assessment, conclusion, "approve"), data={"expected_version": 1}
    )
    assert response.status_code == 409
    _assert_snapshot(db, conclusion, before)


def test_scenario_4_edit_withhold_reopen_and_apply(db, http, gate, monkeypatch):
    """Scenario 4: edit locks one human revision, withholds reruns, then reopen permits apply."""
    assessment, conclusion = _run_one(db, gate, monkeypatch)
    evidence_summary, cluster_id = conclusion.evidence_summary, conclusion.cluster_id
    response = http.post(
        _url(assessment, conclusion, "edit"), data=_edit_payload(1)
    )
    assert response.status_code == 200
    db.refresh(conclusion)
    assert conclusion.version == 2 and conclusion.ai_proposed is False
    assert conclusion.evidence_summary == evidence_summary and conclusion.cluster_id == cluster_id
    assert [row.action for row in _revisions(db, conclusion.id)][-1] == "edited"
    edited_snapshot = _snapshot(db, conclusion)

    _stub_single(
        monkeypatch,
        [_item(REQS[0], "compliant", current="New AI state", gap="", risk="low", action="")],
    )
    gate.trigger_analysis(assessment.id, db)
    db.refresh(conclusion)
    for field in edited_snapshot:
        if field != "revision_ids":
            assert getattr(conclusion, field) == edited_snapshot[field]
    assert _revisions(db, conclusion.id)[-1].action == "proposal_withheld"
    page = http.get(f"/assessments/{assessment.id}/conclusions")
    assert "A newer AI proposal was withheld" in page.text and "Compliant" in page.text

    assert http.post(
        _url(assessment, conclusion, "reopen"), data={"expected_version": 2}
    ).status_code == 200
    _stub_single(
        monkeypatch,
        [_item(REQS[0], "compliant", current="Applied AI state", gap="", risk="low", action="")],
    )
    gate.trigger_analysis(assessment.id, db)
    db.refresh(conclusion)
    assert conclusion.outcome == "compliant" and conclusion.ai_proposed is True
    assert _revisions(db, conclusion.id)[-1].action == "proposed"
    assert "A newer AI proposal was withheld" not in http.get(
        f"/assessments/{assessment.id}/conclusions"
    ).text


@pytest.mark.parametrize(
    ("payload", "status", "message"),
    [
        ({"outcome": "bad"}, 422, None),
        ({"risk_level": "urgent"}, 422, None),
        ({"expected_version": None}, 422, None),
        ({"rationale": "   "}, 400, None),
        ({"gaps_identified": ""}, 400, None),
    ],
)
def test_scenario_5_edit_validation_writes_nothing(
    db, http, gate, monkeypatch, payload, status, message
):
    """Scenario 5: invalid edit values and missing versions cannot change history or content."""
    assessment, conclusion = _run_one(db, gate, monkeypatch)
    before = _snapshot(db, conclusion)
    body = _edit_payload(1)
    if payload.get("expected_version", 1) is None:
        body.pop("expected_version")
    else:
        body.update(payload)
    response = http.post(_url(assessment, conclusion, "edit"), data=body)
    assert response.status_code == status
    _assert_snapshot(db, conclusion, before)


def test_scenario_5_noop_edit_has_actionable_toast(db, http, gate, monkeypatch):
    """Scenario 5: a no-op edit is rejected with guidance and an HTMX toast header."""
    assessment, conclusion = _run_one(db, gate, monkeypatch)
    before = _snapshot(db, conclusion)
    body = {
        "expected_version": 1,
        "outcome": conclusion.outcome,
        "rationale": conclusion.rationale,
        "gaps_identified": conclusion.gaps_identified,
        "risk_level": conclusion.risk_level,
        "recommended_action": conclusion.recommended_action,
    }
    response = http.post(_url(assessment, conclusion, "edit"), data=body)
    assert response.status_code == 400
    assert "No changes to save" in response.json()["detail"]
    assert "X-Toast-Message" in response.headers
    _assert_snapshot(db, conclusion, before)


def test_scenario_6_reject_transitions_and_new_proposal(db, http, gate, monkeypatch):
    """Scenario 6: reject is non-locking, can be approved, and a rerun supersedes rejection."""
    assessment, conclusion = _run_one(db, gate, monkeypatch)
    content = _snapshot(db, conclusion)
    response = http.post(_url(assessment, conclusion, "reject"), data={"expected_version": 1})
    assert response.status_code == 200 and 'data-state="rejected"' in response.text
    db.refresh(conclusion)
    assert conclusion.version == 2 and conclusion.outcome == content["outcome"]
    assert analysis_pipeline.load_conclusion_state(
        db, assessment_id=assessment.id, framework_id="dpdpa"
    )[conclusion.requirement_id].locked is False
    assert http.post(
        _url(assessment, conclusion, "reject"), data={"expected_version": 2}
    ).status_code == 400
    assert http.post(
        _url(assessment, conclusion, "approve"), data={"expected_version": 2}
    ).status_code == 200

    other, other_conclusion = _run_one(db, gate, monkeypatch, client_name="Rerun Corp")
    assert http.post(
        _url(other, other_conclusion, "reject"), data={"expected_version": 1}
    ).status_code == 200
    _stub_single(monkeypatch, [_item(REQS[0], "compliant", gap="", risk="low", action="")])
    result = gate.trigger_analysis(other.id, db)
    run_id = result["analysis_run_ids"]["dpdpa"]
    from app.models.analysis_run import AnalysisRun

    claim = json.loads(db.get(AnalysisRun, run_id).claims_json)["claims"][0]
    assert claim["disposition"] == "applied"
    page = http.get(f"/assessments/{other.id}/conclusions")
    assert 'data-state="pending"' in page.text and "/reject" in page.text


def test_scenario_7_reopen_only_unlocks_approved_content(db, http, gate, monkeypatch):
    """Scenario 7: reopen is invalid while pending and unlocks an approved Conclusion."""
    assessment, conclusion = _run_one(db, gate, monkeypatch)
    before = _snapshot(db, conclusion)
    assert http.post(
        _url(assessment, conclusion, "reopen"), data={"expected_version": 1}
    ).status_code == 400
    _assert_snapshot(db, conclusion, before)
    assert http.post(
        _url(assessment, conclusion, "approve"), data={"expected_version": 1}
    ).status_code == 200
    approved = _snapshot(db, conclusion)
    response = http.post(
        _url(assessment, conclusion, "reopen"), data={"expected_version": 2}
    )
    assert response.status_code == 200 and 'data-state="pending"' in response.text
    db.refresh(conclusion)
    assert conclusion.version == 3 and conclusion.outcome == approved["outcome"]
    assert _revisions(db, conclusion.id)[-1].action == "reopened"
    assert analysis_pipeline.load_conclusion_state(
        db, assessment_id=assessment.id, framework_id="dpdpa"
    )[conclusion.requirement_id].locked is False


@pytest.mark.parametrize("state", ["pending", "rejected", "approved", "edited"])
@pytest.mark.parametrize("route", ["approve", "edit", "reject", "reopen"])
def test_scenario_8_state_machine_matrix(db, http, gate, monkeypatch, state, route):
    """Scenario 8: every state/action pair follows the exact allowed-action matrix."""
    assessment, conclusion = _run_one(db, gate, monkeypatch)
    if state != "pending":
        _human_revision(db, conclusion, state)
    before = _snapshot(db, conclusion)
    payload = (
        _edit_payload(conclusion.version)
        if route == "edit"
        else {"expected_version": conclusion.version}
    )
    response = http.post(_url(assessment, conclusion, route), data=payload)
    allowed = conclusion_review.ACTION_BY_ROUTE[route] in conclusion_review.ALLOWED_ACTIONS[state]
    assert response.status_code == (200 if allowed else 400)
    if allowed:
        db.refresh(conclusion)
        assert conclusion.version == before["version"] + 1
    else:
        _assert_snapshot(db, conclusion, before)
    assert set(conclusion_review.ACTION_BY_ROUTE.values()) == set(
        analysis_pipeline.HUMAN_DECISION_ACTIONS
    )
    assert conclusion_review.ALLOWED_ACTIONS == {
        "pending": ("approved", "edited", "rejected"),
        "rejected": ("approved", "edited"),
        "approved": ("reopened",),
        "edited": ("reopened",),
    }


def test_scenario_9_approval_guard_and_explicit_absence(db, http, gate, monkeypatch):
    """Scenario 9: legacy evidence blocks approval; explicit absence warns but permits it."""
    assessment, conclusion = _run_one(db, gate, monkeypatch)
    proposal = _revisions(db, conclusion.id)[0]
    proposal.actor = "system:migration"
    proposal.citations_json = None
    db.commit()
    before = _snapshot(db, conclusion)
    for route, payload in (
        ("approve", {"expected_version": 1}),
        ("edit", _edit_payload(1)),
    ):
        response = http.post(_url(assessment, conclusion, route), data=payload)
        assert response.status_code == 400
        assert "not captured" in response.json()["detail"]
        _assert_snapshot(db, conclusion, before)
    page = http.get(f"/assessments/{assessment.id}/conclusions")
    assert "Evidence support was not captured" in page.text and "disabled" in page.text
    assert http.post(
        _url(assessment, conclusion, "reject"), data={"expected_version": 1}
    ).status_code == 200

    supported, compliant = _run_one(
        db,
        gate,
        monkeypatch,
        item=_item(REQS[0], "compliant", gap="", risk="low", action=""),
        client_name="Explicit Absence Corp",
    )
    page = http.get(f"/assessments/{supported.id}/conclusions")
    assert "supporting outcome has no grounded citation" in page.text
    assert http.post(
        _url(supported, compliant, "approve"), data={"expected_version": 1}
    ).status_code == 200

    incomplete, incomplete_conclusion = _run_one(
        db,
        gate,
        monkeypatch,
        item=_item(REQS[0], "non_compliant", action=""),
        client_name="Incomplete Gap Corp",
    )
    assert http.post(
        _url(incomplete, incomplete_conclusion, "approve"),
        data={"expected_version": 1},
    ).status_code == 400


def test_scenario_10_legacy_bulk_approval_is_flagged_and_replaced(db, http, gate, monkeypatch):
    """Scenario 10: migrated approvals remain locked but never count as individual approvals."""
    assessment, conclusion = _run_one(db, gate, monkeypatch)
    _human_revision(db, conclusion, "approved", actor="Manager Review")
    page = http.get(f"/assessments/{assessment.id}/conclusions")
    assert "Legacy bulk approval, not individually reviewed" in page.text
    assert 'data-state="approved"' in page.text
    assert page.text.count("/reopen") == 1
    assert 'data-count="legacy_bulk">1<' in page.text
    assert 'data-count="approved">0<' in page.text

    assert http.post(
        _url(assessment, conclusion, "reopen"), data={"expected_version": 2}
    ).status_code == 200
    assert http.post(
        _url(assessment, conclusion, "approve"),
        data={"expected_version": 3, "reviewer_name": "Priya"},
    ).status_code == 200
    page = http.get(f"/assessments/{assessment.id}/conclusions")
    assert 'data-count="legacy_bulk">0<' in page.text
    assert 'data-count="approved">1<' in page.text


@pytest.mark.parametrize("route", ["approve", "edit", "reject", "reopen"])
def test_scenario_11_stale_foreign_and_unknown_ids(db, http, gate, monkeypatch, route):
    """Scenario 11: every route rejects stale, foreign-assessment and unknown ids."""
    assessment, conclusion = _run_one(db, gate, monkeypatch)
    before = _snapshot(db, conclusion)
    payload = _edit_payload(0) if route == "edit" else {"expected_version": 0}
    response = http.post(_url(assessment, conclusion, route), data=payload)
    assert response.status_code == 409
    if route == "edit":
        assert "Your unsaved value" in response.text
        assert "Consultant rationale" in response.text
        assert "Current state" in response.text
    _assert_snapshot(db, conclusion, before)

    other = _seed(db, client_name=f"Foreign {route}")
    foreign_url = f"/api/assessments/{other.id}/conclusions/{conclusion.id}/{route}"
    assert http.post(foreign_url, data=payload).status_code == 404
    unknown_url = f"/api/assessments/{assessment.id}/conclusions/unknown/{route}"
    assert http.post(unknown_url, data=payload).status_code == 404


def test_scenario_12_individual_only_structural_guards():
    """Scenario 12: Conclusion decisions expose no bulk-action route, control or API shape."""
    routes = {
        (next(iter(route.methods - {"HEAD", "OPTIONS"})), route.path)
        for route in app.routes
        if "/conclusions" in route.path
    }
    assert routes == {
        ("GET", "/assessments/{assessment_id}/conclusions"),
        ("POST", "/api/assessments/{assessment_id}/conclusions/{conclusion_id}/approve"),
        ("POST", "/api/assessments/{assessment_id}/conclusions/{conclusion_id}/edit"),
        ("POST", "/api/assessments/{assessment_id}/conclusions/{conclusion_id}/reject"),
        ("POST", "/api/assessments/{assessment_id}/conclusions/{conclusion_id}/reopen"),
    }
    assert all("{conclusion_id}" in path for method, path in routes if method == "POST")
    signature = inspect.signature(conclusion_review.decide)
    assert "conclusion_id" in signature.parameters
    assert all("list" not in str(parameter.annotation).lower() for parameter in signature.parameters.values())

    paths = [
        "app/templates/components/conclusion_card.html",
        "app/templates/pages/conclusions.html",
        "app/routers/conclusions.py",
        "app/services/conclusion_review.py",
    ]
    result = subprocess.run(
        ["grep", "-niE", "approve all|approve selected|select all|approve framework", *paths],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1, result.stdout
    source = (REPO_ROOT / "app/services/conclusion_review.py").read_text()
    assert "delete" not in source.lower()
    assert ".commit(" not in source


def test_scenario_13_legacy_path_and_status_are_untouched(db, http, gate, monkeypatch):
    """Scenario 13: Conclusion actions and legacy review remain isolated in both directions."""
    assessment = _seed(db, applicable=REQS)
    _stub_single(monkeypatch, [_item(requirement_id) for requirement_id in REQS])
    gate.trigger_analysis(assessment.id, db)
    conclusions = (
        db.query(Conclusion)
        .filter_by(assessment_id=assessment.id)
        .order_by(Conclusion.requirement_id)
        .all()
    )
    report = db.query(GapReport).filter_by(assessment_id=assessment.id).one()
    items = db.query(GapItem).filter_by(report_id=report.id).order_by(GapItem.id).all()
    legacy_before = (
        [
            (
                item.id,
                item.review_status,
                item.reviewed_by,
                item.reviewed_at,
                item.compliance_status,
                item.reviewer_notes,
            )
            for item in items
        ],
        assessment.review_status,
    )
    assert http.post(
        _url(assessment, conclusions[0], "approve"), data={"expected_version": 1}
    ).status_code == 200
    assert http.post(
        _url(assessment, conclusions[1], "edit"), data=_edit_payload(1)
    ).status_code == 200
    assert http.post(
        _url(assessment, conclusions[2], "reject"), data={"expected_version": 1}
    ).status_code == 200
    for item in items:
        db.refresh(item)
    db.refresh(assessment)
    assert (
        [
            (
                item.id,
                item.review_status,
                item.reviewed_by,
                item.reviewed_at,
                item.compliance_status,
                item.reviewer_notes,
            )
            for item in items
        ],
        assessment.review_status,
    ) == legacy_before

    revision_ids = {
        row.id
        for conclusion in conclusions
        for row in _revisions(db, conclusion.id)
    }
    for item in items:
        assert http.patch(
            f"/api/assessments/{assessment.id}/review/items/{item.id}",
            data={"review_status": "accepted"},
        ).status_code == 200
    response = http.post(
        f"/api/assessments/{assessment.id}/review/approve",
        data={"reviewer_name": "Legacy Reviewer"},
    )
    assert response.status_code == 200 and "HX-Redirect" in response.headers
    assert {
        row.id
        for conclusion in conclusions
        for row in _revisions(db, conclusion.id)
    } == revision_ids


def test_scenario_14_page_render_citations_divergence_identity_and_escaping(
    db, http, gate, monkeypatch
):
    """Scenario 14: page rendering covers cards, citations, divergence, identity, empty and escaped text."""
    assessment = _seed(db, applicable=REQS[:2])
    _stub_single(
        monkeypatch,
        [
            _item(REQS[0], "partially_compliant", current="<script>alert(1)</script>"),
            _item(REQS[1], "compliant", gap="", risk="low", action=""),
        ],
    )
    gate.trigger_analysis(assessment.id, db)
    conclusions = db.query(Conclusion).filter_by(assessment_id=assessment.id).all()
    first = next(row for row in conclusions if row.requirement_id == REQS[0])

    evidence = Evidence(
        engagement_id=assessment.engagement_id,
        assessment_id=assessment.id,
        original_filename="policy.pdf",
        storage_path="policy.pdf",
        file_hash_sha256="a" * 64,
        file_size_bytes=10,
        mime_type="application/pdf",
        status="active",
        uploaded_by="consultant",
    )
    db.add(evidence)
    db.flush()
    version = EvidenceVersion(
        evidence_id=evidence.id,
        version_number=1,
        storage_path="policy.pdf",
        file_hash_sha256="a" * 64,
        file_size_bytes=10,
        status="active",
        original_filename="policy.pdf",
        mime_type="application/pdf",
        extracted_text="Grounded quote",
    )
    db.add(version)
    db.flush()
    proposal = next(row for row in _revisions(db, first.id) if row.action == "proposed")
    proposal.citations_json = json.dumps(
        [
            {
                "evidence_version_id": version.id,
                "location_type": "text_span",
                "location_ref": "chars:0-14",
                "excerpt": "Grounded quote",
            }
        ]
    )
    db.commit()

    assert http.post(
        _url(assessment, first, "approve"),
        data={"expected_version": 1, "reviewer_name": "Priya"},
    ).status_code == 200
    _stub_single(
        monkeypatch,
        [
            _item(REQS[0], "non_compliant", current="Different report state"),
            _item(REQS[1], "compliant", gap="", risk="low", action=""),
        ],
    )
    gate.trigger_analysis(assessment.id, db)
    page = http.get(f"/assessments/{assessment.id}/conclusions")
    assert page.status_code == 200
    assert page.text.count("data-conclusion-card") == 2
    assert page.text.count('name="expected_version"') >= 2
    assert "Grounded quote" in page.text and "policy.pdf" in page.text
    assert f'href="/evidence/{evidence.id}"' in page.text
    assert "Report view differs" in page.text
    assert 'value="Priya"' in page.text
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in page.text
    assert "<script>alert(1)</script>" not in page.text

    empty = _seed(db, client_name="Empty Conclusions Corp")
    empty_page = http.get(f"/assessments/{empty.id}/conclusions")
    assert empty_page.status_code == 200
    assert "No conclusions yet. Run the gap analysis first." in empty_page.text
    assert http.get("/assessments/unknown/conclusions").status_code == 404


def test_scenario_15_swap_conclusion_is_cas_and_pipeline_suite_is_unchanged(
    db, gate, monkeypatch
):
    """Scenario 15: shared CAS refuses version mismatch without changing the row."""
    _assessment, conclusion = _run_one(db, gate, monkeypatch)
    before = _snapshot(db, conclusion)
    with pytest.raises(analysis_pipeline.ConclusionConflict):
        analysis_pipeline.swap_conclusion(
            db,
            conclusion,
            expected_version=99,
            values={"outcome": "compliant"},
        )
    db.rollback()
    _assert_snapshot(db, conclusion, before)
