"""Contract suite for P2-6 read-only assessment workpapers."""

from __future__ import annotations

import copy
import html
import inspect
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import median
from time import perf_counter

import pytest
from alembic import command
from alembic.config import Config
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.config import settings
from app.database import get_db
from app.dpdpa.framework import get_all_requirements
from app.frameworks.mappings.clusters import CONTROL_CLUSTERS
from app.frameworks.registry import FrameworkRegistry
from app.main import app
from app.models.analysis_run import AnalysisRun
from app.models.assessment import Assessment
from app.models.audit_event import AuditEvent
from app.models.client import Client
from app.models.conclusion import Conclusion, ConclusionRevision
from app.models.desk_review import DeskReviewFinding
from app.models.engagement import Engagement
from app.models.evidence import Evidence, EvidenceUse, EvidenceVersion
from app.models.questionnaire import QuestionnaireResponse
from app.services import analysis_pipeline, conclusion_review, workpaper

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
    path = tmp_path / "workpaper.sqlite3"
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


def _seed(db, *, applicable=None, frameworks=None, client_name="Acme Corp"):
    frameworks = frameworks or ["dpdpa"]
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
        selected_frameworks=json.dumps(frameworks),
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


def _stub_multi(monkeypatch, per_framework):
    from app.routers import analysis

    def _fake(**_kwargs):
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

    monkeypatch.setattr(analysis, "run_multi_framework_analysis", _fake)


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


def _entry_html(page_text: str, anchor: str) -> str:
    start = page_text.index(f'id="{anchor}"')
    end = page_text.find("data-workpaper-entry", start)
    return page_text[start:] if end == -1 else page_text[start:end]


def _add_evidence(db, assessment, *, filename="policy.pdf", text_value="Grounded quote"):
    evidence = Evidence(
        engagement_id=assessment.engagement_id,
        assessment_id=assessment.id,
        original_filename=filename,
        storage_path=filename,
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
        storage_path=filename,
        file_hash_sha256="a" * 64,
        file_size_bytes=10,
        status="active",
        original_filename=filename,
        mime_type="application/pdf",
        extracted_text=text_value,
    )
    db.add(version)
    db.flush()
    return evidence, version


def _cite_revision(db, conclusion, version, *, excerpt="Grounded quote"):
    proposal = next(row for row in _revisions(db, conclusion.id) if row.action == "proposed")
    proposal.citations_json = json.dumps(
        [
            {
                "evidence_version_id": version.id,
                "location_type": "text_span",
                "location_ref": f"chars:0-{len(excerpt)}",
                "excerpt": excerpt,
            }
        ]
    )
    db.commit()
    return proposal


def _entries(wp):
    return [
        entry
        for section in wp.sections
        for entry in section.entries + section.excluded_entries
    ]


def _database_snapshot(db, assessment):
    tables = (
        "conclusions",
        "conclusion_revisions",
        "analysis_runs",
        "audit_events",
        "evidence_uses",
        "questionnaire_responses",
        "desk_review_findings",
    )
    counts = {
        table: db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one()
        for table in tables
    }
    conclusions = db.query(Conclusion).filter_by(assessment_id=assessment.id).all()
    db.refresh(assessment)
    return {
        "counts": counts,
        "conclusions": sorted(
            (
                row.id,
                row.version,
                row.updated_at,
                row.outcome,
                row.rationale,
                row.ai_proposed,
            )
            for row in conclusions
        ),
        "assessment": (
            assessment.status,
            assessment.review_status,
            assessment.updated_at,
        ),
    }


def test_scenario_1_approved_conclusions_render_complete_workpaper(
    db, http, gate, monkeypatch
):
    """Scenario 1: approved Conclusions render response, proposal, citation and history."""
    assessment = _seed(db, applicable=REQS[:2])
    db.add(
        QuestionnaireResponse(
            assessment_id=assessment.id,
            question_id=REQS[0],
            answer="partially_implemented",
            notes="Client note text",
        )
    )
    db.commit()
    _stub_single(
        monkeypatch,
        [
            _item(REQS[0], "partially_compliant"),
            _item(REQS[1], "compliant", gap="", risk="low", action=""),
        ],
    )
    gate.trigger_analysis(assessment.id, db)
    conclusions = db.query(Conclusion).filter_by(assessment_id=assessment.id).all()
    first = next(row for row in conclusions if row.requirement_id == REQS[0])
    evidence, version = _add_evidence(db, assessment)
    _cite_revision(db, first, version)
    run = db.query(AnalysisRun).filter_by(assessment_id=assessment.id).one()

    response = http.post(
        _url(assessment, first, "approve"),
        data={"expected_version": first.version, "reviewer_name": "Priya"},
    )
    assert response.status_code == 200

    page = http.get(f"/assessments/{assessment.id}/workpaper")
    assert page.status_code == 200
    assert page.text.count("data-workpaper-entry") == 2
    first_html = _entry_html(page.text, f"wp-dpdpa-{REQS[0]}")
    assert 'data-decision-state="approved"' in first_html
    assert re.findall(r'data-revision-action="([^"]+)"', first_html) == [
        "proposed",
        "approved",
    ]
    for expected in (
        "Priya",
        html.escape(run.model_id),
        "Client note text",
        "Partially Implemented",
        "Grounded quote",
        "no quote offered",
        f'href="/evidence/{evidence.id}"',
    ):
        assert expected in first_html
    second_html = _entry_html(page.text, f"wp-dpdpa-{REQS[1]}")
    assert 'data-decision-state="pending"' in second_html
    assert "No questionnaire response recorded for this requirement." in second_html
    assert "No evidence mapped to this requirement." in second_html
    assert "No desk-review findings for this requirement." in second_html


def test_scenario_2_full_history_reconstructs_content_and_actors(
    db, http, gate, monkeypatch
):
    """Scenario 2: full history reconstructs before/after content, runs and actors."""
    assessment, conclusion = _run_one(db, gate, monkeypatch)
    assert http.post(
        _url(assessment, conclusion, "approve"),
        data={"expected_version": 1, "reviewer_name": "Priya"},
    ).status_code == 200
    db.refresh(conclusion)
    assert http.post(
        _url(assessment, conclusion, "reopen"),
        data={"expected_version": conclusion.version, "reviewer_name": "Priya"},
    ).status_code == 200

    _stub_single(monkeypatch, [_item(REQS[0], "non_compliant", current="Second proposal")])
    gate.trigger_analysis(assessment.id, db)
    db.refresh(conclusion)
    assert http.post(
        _url(assessment, conclusion, "edit"),
        data=_edit_payload(
            conclusion.version,
            reviewer_name="Asha",
            outcome="compliant",
            rationale="Asha rationale",
            gaps_identified="",
            risk_level="low",
            recommended_action="",
        ),
    ).status_code == 200
    _stub_single(monkeypatch, [_item(REQS[0], "partially_compliant", current="Withheld proposal")])
    gate.trigger_analysis(assessment.id, db)

    wp = workpaper.build_workpaper(db, assessment)
    entry = _entries(wp)[0]
    assert [row.revision.action for row in entry.revisions] == [
        "proposed",
        "approved",
        "reopened",
        "proposed",
        "edited",
        "proposal_withheld",
    ]
    assert [row.sequence for row in entry.revisions] == list(range(1, 7))
    assert [row.outcome_after for row in entry.revisions] == [
        "partially_compliant",
        None,
        None,
        "non_compliant",
        "compliant",
        None,
    ]
    assert entry.revisions[3].revision.previous_outcome == "partially_compliant"
    assert entry.revisions[4].revision.previous_outcome == "non_compliant"
    assert entry.ai_proposal is entry.revisions[3]
    assert entry.ai_proposal.claim["outcome"] == "non_compliant"
    assert entry.revisions[5].claim["disposition"] == "withheld"
    assert len({entry.revisions[index].run.id for index in (0, 3, 5)}) == 3
    assert all(entry.revisions[index].run.status == "completed" for index in (0, 3, 5))
    assert entry.revisions[1].run is None
    assert entry.revisions[0].actor_display == "system:analysis"
    assert entry.revisions[1].actor_display == "Priya"
    assert entry.revisions[4].actor_display == "Asha"

    page = http.get(f"/assessments/{assessment.id}/workpaper")
    assert page.status_code == 200
    for expected in (
        "Edited and approved",
        "A newer AI proposal was withheld because this conclusion is locked",
        "AI proposed before edit",
        "Consultant edits carry no citations",
    ):
        assert expected in page.text
    assert "consultant:Priya" not in page.text


def test_scenario_3_finding_to_history_to_evidence_path(db, http, gate, monkeypatch):
    """Scenario 3: report findings link through full history to an evidence version."""
    assessment = _seed(db, applicable=[REQS[0]])
    _stub_single(monkeypatch, [_item(REQS[0], "non_compliant", risk="high")])
    gate.trigger_analysis(assessment.id, db)
    conclusion = db.query(Conclusion).filter_by(assessment_id=assessment.id).one()
    evidence, version = _add_evidence(db, assessment)
    _cite_revision(db, conclusion, version)
    assert http.post(
        _url(assessment, conclusion, "approve"),
        data={"expected_version": 1, "reviewer_name": "Priya"},
    ).status_code == 200

    fragment = f'href="/assessments/{assessment.id}/workpaper#wp-dpdpa-{REQS[0]}"'
    report = http.get(f"/assessments/{assessment.id}/report-summary")
    assert report.status_code == 200
    assert report.text.count(fragment) >= 2
    assert f'href="/assessments/{assessment.id}/workpaper"' in report.text
    conclusions = http.get(f"/assessments/{assessment.id}/conclusions")
    assert fragment in conclusions.text
    page = http.get(f"/assessments/{assessment.id}/workpaper")
    assert page.text.count(f'id="wp-dpdpa-{REQS[0]}"') == 1
    entry_html = _entry_html(page.text, f"wp-dpdpa-{REQS[0]}")
    assert entry_html.count("data-revision-action") == 2
    assert f'href="/evidence/{evidence.id}"' in entry_html
    detail = http.get(f"/evidence/{evidence.id}")
    assert detail.status_code == 200
    assert "a" * 64 in detail.text
    source = (REPO_ROOT / "app/templates/components/workpaper_entry.html").read_text()
    assert "<details" not in source


def test_scenario_4_scope_split_unconcluded_and_unrestricted_values(
    db, http, gate, monkeypatch
):
    """Scenario 4: current scope splits exclusions and lists applicable unconcluded rows."""
    assessment = _seed(db, applicable=[REQS[0]], client_name="Scope A")
    _stub_single(monkeypatch, [_item(REQS[0]), _item(REQS[1])])
    gate.trigger_analysis(assessment.id, db)
    page = http.get(f"/assessments/{assessment.id}/workpaper")
    first = page.text.index(f'id="wp-dpdpa-{REQS[0]}"')
    heading = page.text.index("Excluded by scope enforcement")
    second = page.text.index(f'id="wp-dpdpa-{REQS[1]}"')
    assert first < heading < second
    assert 'data-in-scope="false"' in _entry_html(page.text, f"wp-dpdpa-{REQS[1]}")
    assert "Scope-enforced to not applicable at analysis time" in page.text
    assert page.text.count("data-workpaper-entry") == 2

    assessment_b = _seed(db, applicable=REQS[:3], client_name="Scope B")
    _stub_single(monkeypatch, [_item(REQS[0])])
    gate.trigger_analysis(assessment_b.id, db)
    wp = workpaper.build_workpaper(db, assessment_b)
    assert [row["requirement_id"] for row in wp.sections[0].unconcluded] == REQS[1:3]
    page_b = http.get(f"/assessments/{assessment_b.id}/workpaper")
    assert page_b.text.count("data-workpaper-unconcluded") == 2
    assert f'id="wp-dpdpa-{REQS[1]}"' in page_b.text
    assert "Applicable requirements with no conclusion" in page_b.text

    for raw in (None, "not json", "[]"):
        assessment_b.applicable_requirements = raw
        db.flush()
        unrestricted = workpaper.build_workpaper(db, assessment_b)
        assert unrestricted.applicable is None
        assert len(unrestricted.sections[0].unconcluded) == 40


def test_scenario_5_framework_grouping_and_response_matching(
    db, http, gate, monkeypatch
):
    """Scenario 5: frameworks remain separate and responses match requirement, cluster and singleton keys."""
    iso_controls = [row.id for row in FrameworkRegistry.get_all_controls("iso27001")]
    clustered_ids = {
        control["control"]
        for cluster in CONTROL_CLUSTERS
        for control in cluster["controls"]
        if control["framework"] == "iso27001"
    }
    iso_clustered = next((row for row in iso_controls if row in clustered_ids), None)
    iso_single = next((row for row in iso_controls if row not in clustered_ids), None)
    assert iso_clustered and iso_single
    assessment = _seed(
        db,
        frameworks=["dpdpa", "iso27001"],
        applicable=[REQS[0], iso_clustered, iso_single],
        client_name="Multi",
    )
    _stub_multi(
        monkeypatch,
        {
            "dpdpa": [_item(REQS[0])],
            "iso27001": [_item(iso_clustered), _item(iso_single)],
        },
    )
    gate.trigger_analysis(assessment.id, db)
    wp = workpaper.build_workpaper(db, assessment)
    assert all(entry.client_response is None for entry in _entries(wp))
    iso_conclusions = {
        row.requirement_id: row
        for row in db.query(Conclusion).filter_by(
            assessment_id=assessment.id, framework_id="iso27001"
        )
    }
    cluster_key = iso_conclusions[iso_clustered].cluster_id
    assert cluster_key
    now = datetime.now(timezone.utc)
    db.add_all(
        [
            QuestionnaireResponse(
                assessment_id=assessment.id,
                question_id=REQS[0],
                answer="partially_implemented",
            ),
            QuestionnaireResponse(
                assessment_id=assessment.id,
                question_id=cluster_key,
                answer="planned",
            ),
            QuestionnaireResponse(
                assessment_id=assessment.id,
                question_id=f"SINGLE.{iso_single}",
                answer="not_implemented",
                submitted_at=now,
            ),
            QuestionnaireResponse(
                assessment_id=assessment.id,
                question_id=f"SINGLE.{iso_single}",
                answer="fully_implemented",
                submitted_at=now + timedelta(minutes=1),
            ),
        ]
    )
    db.commit()
    wp = workpaper.build_workpaper(db, assessment)
    by_key = {
        (entry.card.conclusion.framework_id, entry.card.conclusion.requirement_id): entry
        for entry in _entries(wp)
    }
    assert by_key[("dpdpa", REQS[0])].client_response.matched_on == "requirement"
    assert by_key[("iso27001", iso_clustered)].client_response.matched_on == "cluster"
    singleton = by_key[("iso27001", iso_single)].client_response
    assert singleton.matched_on == "singleton"
    assert singleton.answer == "fully_implemented"
    page = http.get(f"/assessments/{assessment.id}/workpaper")
    dpdpa_start = page.text.index('data-workpaper-section="dpdpa"')
    iso_start = page.text.index('data-workpaper-section="iso27001"')
    assert dpdpa_start < page.text.index(f'id="wp-dpdpa-{REQS[0]}"') < iso_start
    assert iso_start < page.text.index(f'id="wp-iso27001-{iso_clustered}"')
    assert iso_start < page.text.index(f'id="wp-iso27001-{iso_single}"')
    assert "Shared cluster question" in page.text


def test_scenario_6_evidence_mapping_and_desk_review_blocks(
    db, http, gate, monkeypatch
):
    """Scenario 6: mapped evidence and current desk-review findings stay requirement-specific."""
    assessment = _seed(db, applicable=REQS[:2])
    _stub_single(monkeypatch, [_item(REQS[0]), _item(REQS[1])])
    gate.trigger_analysis(assessment.id, db)
    first_evidence, first_version = _add_evidence(
        db, assessment, filename="active-policy.pdf"
    )
    second_evidence, _ = _add_evidence(db, assessment, filename="other.pdf")
    db.add_all(
        [
            EvidenceUse(
                evidence_id=first_evidence.id,
                assessment_id=assessment.id,
                framework_id="dpdpa",
                requirement_id=REQS[0],
                relevance="primary",
            ),
            EvidenceUse(
                evidence_id=second_evidence.id,
                assessment_id=assessment.id,
                framework_id="dpdpa",
                requirement_id=REQS[1],
                relevance="supporting",
            ),
            DeskReviewFinding(
                assessment_id=assessment.id,
                requirement_id=REQS[0],
                finding_type="evidence",
                content="Desk finding text",
                severity="medium",
                citations_json=None,
            ),
            DeskReviewFinding(
                assessment_id=assessment.id,
                requirement_id=REQS[0],
                finding_type="absence",
                content="No extra support",
                severity="low",
                citations_json="[]",
            ),
            DeskReviewFinding(
                assessment_id=assessment.id,
                requirement_id=None,
                finding_type="signal",
                content="Cross cutting",
                severity="info",
                citations_json="[]",
            ),
        ]
    )
    db.commit()
    wp = workpaper.build_workpaper(db, assessment)
    by_req = {entry.card.conclusion.requirement_id: entry for entry in _entries(wp)}
    assert by_req[REQS[0]].mapped_evidence == [
        {
            "use_id": by_req[REQS[0]].mapped_evidence[0]["use_id"],
            "evidence_id": first_evidence.id,
            "filename": first_version.original_filename,
            "evidence_status": "active",
            "relevance": "primary",
            "created_at": by_req[REQS[0]].mapped_evidence[0]["created_at"],
        }
    ]
    assert all(
        row["evidence_id"] != second_evidence.id
        for row in by_req[REQS[0]].mapped_evidence
    )
    assert [row["citations_captured"] for row in by_req[REQS[0]].desk_review_findings] == [
        False,
        True,
    ]
    assert all(
        row["content"] != "Cross cutting"
        for entry in _entries(wp)
        for row in entry.desk_review_findings
    )
    page = http.get(f"/assessments/{assessment.id}/workpaper")
    first_html = _entry_html(page.text, f"wp-dpdpa-{REQS[0]}")
    assert f'href="/evidence/{first_evidence.id}"' in first_html
    assert "active-policy.pdf" in first_html and "primary" in first_html
    assert "Evidence support not captured (legacy)" in first_html
    assert "No supporting citation (explicit evidence absence)" in first_html
    second_html = _entry_html(page.text, f"wp-dpdpa-{REQS[1]}")
    assert "No desk-review findings for this requirement." in second_html
    assert "No evidence mapped to this requirement." not in second_html


def test_scenario_7_empty_failed_stale_malformed_legacy_and_ungrounded_states(
    db, http, gate, monkeypatch
):
    """Scenario 7: empty, failed, stale, malformed, legacy and ungrounded states render safely."""
    assert http.get("/assessments/missing/workpaper").status_code == 404
    empty = _seed(db, applicable=[REQS[0]], client_name="Empty")
    page = http.get(f"/assessments/{empty.id}/workpaper")
    assert page.status_code == 200
    assert "No conclusions yet. Run the gap analysis first." in page.text
    assert "No analysis runs recorded." in page.text
    assert "data-workpaper-entry" not in page.text

    from app.routers import analysis

    monkeypatch.setattr(analysis, "run_gap_analysis", lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("boom")))
    with pytest.raises(HTTPException):
        gate.trigger_analysis(empty.id, db)
    failed = http.get(f"/assessments/{empty.id}/workpaper")
    assert 'data-run-status="failed"' in failed.text
    assert "RuntimeError" in failed.text
    assert "boom" not in failed.text

    now = datetime.now(timezone.utc)
    old_run = AnalysisRun(
        assessment_id=empty.id,
        framework_id="dpdpa",
        status="running",
        claims_json="{}",
        model_id="old-model",
        started_at=now - timedelta(hours=2),
    )
    fresh_run = AnalysisRun(
        assessment_id=empty.id,
        framework_id="dpdpa",
        status="running",
        claims_json="{}",
        model_id="fresh-model",
        started_at=now - timedelta(minutes=5),
    )
    malformed_run = AnalysisRun(
        assessment_id=empty.id,
        framework_id="dpdpa",
        status="completed",
        claims_json="not json",
        model_id="malformed-model",
        started_at=now - timedelta(minutes=4),
        completed_at=now - timedelta(minutes=3),
    )
    db.add_all([old_run, fresh_run, malformed_run])
    db.commit()
    runs = workpaper.build_workpaper(db, empty, now=now).runs
    assert next(row for row in runs if row.id == old_run.id).stale is True
    assert next(row for row in runs if row.id == fresh_run.id).stale is False
    stale_page = http.get(f"/assessments/{empty.id}/workpaper")
    assert 'data-run-stale="true"' in stale_page.text

    legacy = _seed(db, applicable=[REQS[0]], client_name="Legacy")
    legacy_conclusion = Conclusion(
        assessment_id=legacy.id,
        requirement_id=REQS[0],
        framework_id="dpdpa",
        cluster_id=None,
        outcome="partially_compliant",
        rationale="Migrated rationale",
        evidence_summary="",
        gaps_identified="Migrated gap",
        risk_level="medium",
        recommended_action="Migrated action",
        ai_proposed=True,
        version=1,
    )
    db.add(legacy_conclusion)
    db.flush()
    db.add_all(
        [
            ConclusionRevision(
                conclusion_id=legacy_conclusion.id,
                actor="system:migration",
                action="proposed",
                citations_json=None,
            ),
            ConclusionRevision(
                conclusion_id=legacy_conclusion.id,
                actor="Manager Review",
                action="approved",
                previous_outcome=legacy_conclusion.outcome,
                previous_rationale=legacy_conclusion.rationale,
                citations_json=None,
            ),
        ]
    )
    db.commit()
    legacy_wp = workpaper.build_workpaper(db, legacy)
    legacy_entry = _entries(legacy_wp)[0]
    assert legacy_entry.revisions[1].legacy_bulk_approval is True
    assert legacy_wp.counts["legacy_bulk"] == 1
    assert legacy_wp.counts["approved"] == 0
    legacy_page = http.get(f"/assessments/{legacy.id}/workpaper")
    for expected in (
        "No run record for this proposal (migrated from the legacy report).",
        "Evidence support not captured (legacy)",
        workpaper.LEGACY_BULK_LABEL,
    ):
        assert expected in legacy_page.text

    ungrounded = _seed(db, applicable=[REQS[0]], client_name="Ungrounded")
    _stub_single(
        monkeypatch,
        [_item(REQS[0], "compliant", quote="fabricated words not in evidence")],
    )
    gate.trigger_analysis(ungrounded.id, db)
    ungrounded_page = http.get(f"/assessments/{ungrounded.id}/workpaper")
    for expected in (
        "No grounded supporting quote",
        "Ungrounded quote offered by the model",
        "fabricated words not in evidence",
        "This supporting outcome has no grounded citation.",
    ):
        assert expected in ungrounded_page.text


def test_scenario_8_client_and_model_text_is_escaped(db, http, gate, monkeypatch):
    """Scenario 8: client, model and desk-review text is autoescaped."""
    payload = "<script>alert(1)</script>"
    assessment = _seed(db, applicable=[REQS[0]])
    db.add(
        QuestionnaireResponse(
            assessment_id=assessment.id,
            question_id=REQS[0],
            answer="planned",
            notes=payload,
        )
    )
    db.add(
        DeskReviewFinding(
            assessment_id=assessment.id,
            requirement_id=REQS[0],
            finding_type="signal",
            content=payload,
            severity="medium",
            citations_json="[]",
        )
    )
    db.commit()
    _stub_single(monkeypatch, [_item(REQS[0], current=payload)])
    gate.trigger_analysis(assessment.id, db)
    page = http.get(f"/assessments/{assessment.id}/workpaper")
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in page.text
    assert payload not in page.text


def test_scenario_9_workpaper_is_structurally_and_behaviorally_read_only(
    db, http, gate, monkeypatch
):
    """Scenario 9: the workpaper exposes one GET and cannot mutate assessment data."""
    from app.routers import web

    workpaper_routes = {
        (method, route.path)
        for route in app.routes
        if "/workpaper" in route.path
        for method in route.methods
    }
    assert workpaper_routes == {("GET", "/assessments/{assessment_id}/workpaper")}
    forbidden_template = re.compile(
        r"<form|<button|hx-post|hx-put|hx-patch|hx-delete|expected_version|\|\s*safe\b",
        re.IGNORECASE,
    )
    for path in (
        REPO_ROOT / "app/templates/pages/workpaper.html",
        REPO_ROOT / "app/templates/components/workpaper_entry.html",
    ):
        assert forbidden_template.search(path.read_text()) is None
    source = (REPO_ROOT / "app/services/workpaper.py").read_text()
    assert "delete" not in source.lower()
    for token in (
        "db.add(",
        "db.add_all(",
        "db.merge(",
        ".commit(",
        ".flush(",
        "swap_conclusion",
        "decide(",
    ):
        assert token not in source
    assert ".commit(" not in inspect.getsource(web.workpaper_page)

    assessment = _seed(db, applicable=[REQS[0]])
    _stub_single(monkeypatch, [_item(REQS[0])])
    gate.trigger_analysis(assessment.id, db)
    conclusion = db.query(Conclusion).filter_by(assessment_id=assessment.id).one()
    assert http.post(
        _url(assessment, conclusion, "approve"),
        data={"expected_version": 1, "reviewer_name": "Priya"},
    ).status_code == 200
    url = f"/assessments/{assessment.id}/workpaper"
    for method in (http.post, http.put, http.patch, http.delete):
        assert method(url).status_code == 405
    before = _database_snapshot(db, assessment)
    first = http.get(url)
    second = http.get(url)
    assert first.status_code == second.status_code == 200
    assert _database_snapshot(db, assessment) == before
    for token in (
        "<form",
        "hx-post",
        "hx-put",
        "hx-patch",
        "hx-delete",
        'name="expected_version"',
        "data-conclusion-card",
    ):
        assert token not in first.text.lower()


def test_scenario_10_reuses_conclusion_cards_once_and_preserves_states(
    db, http, gate, monkeypatch
):
    """Scenario 10: one conclusion_cards call supplies the same decision state as the review page."""
    assessment = _seed(db, applicable=REQS[:2])
    _stub_single(monkeypatch, [_item(REQS[0]), _item(REQS[1])])
    gate.trigger_analysis(assessment.id, db)
    conclusion = db.query(Conclusion).filter_by(
        assessment_id=assessment.id, requirement_id=REQS[0]
    ).one()
    assert http.post(
        _url(assessment, conclusion, "reject"),
        data={"expected_version": 1, "reviewer_name": "Priya"},
    ).status_code == 200
    real = conclusion_review.conclusion_cards
    calls = []

    def _spy(db_arg, assessment_id):
        calls.append(assessment_id)
        return real(db_arg, assessment_id)

    monkeypatch.setattr(conclusion_review, "conclusion_cards", _spy)
    page = http.get(f"/assessments/{assessment.id}/workpaper")
    assert calls == [assessment.id]
    conclusions_page = http.get(f"/assessments/{assessment.id}/conclusions")
    cards = real(db, assessment.id)
    for card in cards:
        workpaper_html = _entry_html(
            page.text,
            f"wp-{card.conclusion.framework_id}-{card.conclusion.requirement_id}",
        )
        assert f'data-decision-state="{card.state}"' in workpaper_html
        card_start = conclusions_page.text.index(f'id="conclusion-card-{card.conclusion.id}"')
        card_html = conclusions_page.text[card_start : card_start + 500]
        assert f'data-state="{card.state}"' in card_html


def test_scenario_11_counts_cover_every_decision_scope_and_run_bucket(
    db, http, gate, monkeypatch
):
    """Scenario 11: header counts exactly cover states, scope, missing Conclusions and runs."""
    concluded = ALL_REQS[:6]
    unconcluded = ALL_REQS[6]
    assessment = _seed(
        db,
        applicable=concluded[:5] + [unconcluded],
        client_name="Counts",
    )
    _stub_single(monkeypatch, [_item(requirement_id) for requirement_id in concluded])
    gate.trigger_analysis(assessment.id, db)
    rows = {
        row.requirement_id: row
        for row in db.query(Conclusion).filter_by(assessment_id=assessment.id)
    }
    assert http.post(
        _url(assessment, rows[concluded[1]], "reject"),
        data={"expected_version": 1, "reviewer_name": "Priya"},
    ).status_code == 200
    assert http.post(
        _url(assessment, rows[concluded[2]], "approve"),
        data={"expected_version": 1, "reviewer_name": "Priya"},
    ).status_code == 200
    assert http.post(
        _url(assessment, rows[concluded[3]], "edit"),
        data=_edit_payload(1),
    ).status_code == 200
    _human_revision(db, rows[concluded[4]], "approved", actor="Manager Review")
    wp = workpaper.build_workpaper(db, assessment)
    expected = {
        "conclusions": 6,
        "in_scope": 5,
        "excluded": 1,
        "unconcluded": 1,
        "pending": 2,
        "rejected": 1,
        "approved": 1,
        "edited": 1,
        "legacy_bulk": 1,
        "runs": 1,
    }
    assert wp.counts == expected
    page = http.get(f"/assessments/{assessment.id}/workpaper")
    for key, value in expected.items():
        assert re.search(
            rf'data-count="{key}"[^>]*>\s*{value}\s*<', page.text
        )


def test_scenario_12_existing_contract_guards_remain_in_scope():
    """Scenario 12: existing pipeline, approval, scoring and white-label guards remain unchanged."""
    guarded = (
        "tests/test_conclusion_approval.py",
        "tests/test_analysis_pipeline.py",
        "tests/test_no_blended_scoring.py",
        "tests/test_white_label.py",
    )
    assert all((REPO_ROOT / path).is_file() for path in guarded)
    assert "overall_score" not in (
        REPO_ROOT / "app/templates/pages/workpaper.html"
    ).read_text()
    assert "CyberAssess" not in (
        REPO_ROOT / "app/templates/pages/workpaper.html"
    ).read_text()


def test_smoke_full_assessment_traceability(db, http, gate, monkeypatch, capsys):
    """Smoke: 41 requirements, three decisions and three runs remain read-only and traceable."""
    assessment = _seed(db, applicable=ALL_REQS, client_name="Smoke")
    evidence, _version = _add_evidence(
        db,
        assessment,
        filename="smoke-policy.pdf",
        text_value="Grounded smoke quote",
    )
    items = [
        _item(
            requirement_id,
            "non_compliant" if index == 0 else (
                "partially_compliant" if index in (1, 2) else "compliant"
            ),
            gap="Smoke gap" if index < 3 else "",
            risk="high" if index == 0 else ("medium" if index < 3 else "low"),
            action="Smoke action" if index < 3 else "",
            quote="Grounded smoke quote" if index == 0 else "",
        )
        for index, requirement_id in enumerate(ALL_REQS)
    ]
    _stub_single(monkeypatch, items)
    gate.trigger_analysis(assessment.id, db)
    conclusions = {
        row.requirement_id: row
        for row in db.query(Conclusion).filter_by(assessment_id=assessment.id)
    }
    assert http.post(
        _url(assessment, conclusions[ALL_REQS[0]], "approve"),
        data={"expected_version": 1, "reviewer_name": "Priya"},
    ).status_code == 200
    assert http.post(
        _url(assessment, conclusions[ALL_REQS[1]], "edit"),
        data=_edit_payload(
            1,
            outcome="compliant",
            rationale="Smoke edit",
            gaps_identified="",
            risk_level="low",
            recommended_action="",
        ),
    ).status_code == 200
    assert http.post(
        _url(assessment, conclusions[ALL_REQS[2]], "reject"),
        data={"expected_version": 1, "reviewer_name": "Priya"},
    ).status_code == 200
    gate.trigger_analysis(assessment.id, db)
    gate.trigger_analysis(assessment.id, db)

    revision_count_before = db.query(ConclusionRevision).count()
    timings = []
    page = None
    for _ in range(3):
        started = perf_counter()
        page = http.get(f"/assessments/{assessment.id}/workpaper")
        timings.append(perf_counter() - started)
        assert page.status_code == 200
    assert db.query(ConclusionRevision).count() == revision_count_before
    wp = workpaper.build_workpaper(db, assessment)
    assert wp.counts == {
        "conclusions": 41,
        "in_scope": 41,
        "excluded": 0,
        "unconcluded": 0,
        "pending": 39,
        "rejected": 0,
        "approved": 1,
        "edited": 1,
        "legacy_bulk": 0,
        "runs": 3,
    }
    report = http.get(f"/assessments/{assessment.id}/report-summary")
    fragment = f'/assessments/{assessment.id}/workpaper#wp-dpdpa-{ALL_REQS[0]}'
    assert fragment in report.text
    assert f'id="wp-dpdpa-{ALL_REQS[0]}"' in page.text
    edited_html = _entry_html(page.text, f"wp-dpdpa-{ALL_REQS[1]}")
    edited_actions = re.findall(r'data-revision-action="([^"]+)"', edited_html)
    assert edited_actions == [
        "proposed",
        "edited",
        "proposal_withheld",
        "proposal_withheld",
    ]
    assert f'href="/evidence/{evidence.id}"' in page.text
    detail = http.get(f"/evidence/{evidence.id}")
    assert detail.status_code == 200
    assert "a" * 64 in detail.text
    with capsys.disabled():
        print(
            "WORKPAPER_SMOKE",
            f"median_seconds={median(timings):.6f}",
            f"counts={json.dumps(wp.counts, sort_keys=True)}",
            f"edited_actions={edited_actions}",
            f"revisions_before_after={revision_count_before}/{revision_count_before}",
        )
