from __future__ import annotations

import hashlib
import inspect
import io
import json
import re
import shutil
import subprocess
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from fpdf import FPDF
from sqlalchemy import create_engine, event, insert, select, text, update
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.config import settings
from app.database import Base, get_db
from app.dpdpa.framework import get_all_requirements
from app.main import app
from app.models.action import Action
from app.models.analysis_run import AnalysisRun
from app.models.assessment import Assessment, AssessmentDocument, _new_id
from app.models.assessment_pack import AssessmentPack
from app.models.audit_event import AuditEvent
from app.models.client import Client
from app.models.conclusion import Conclusion, ConclusionRevision
from app.models.desk_review import DeskReviewFinding, DeskReviewSummary
from app.models.engagement import Engagement
from app.models.evidence import Evidence, EvidenceUse, EvidenceVersion
from app.models.finding import Finding
from app.models.initiative import Initiative
from app.models.magic_link import MagicLink
from app.models.questionnaire import QuestionnaireResponse
from app.models.report import GapItem, GapReport
from app.models.report_snapshot import ReportSnapshot
from app.models.rfi import RFIDocument
from app.routers import retention as retention_router
from app.services import evidence as evidence_service
from app.services import retention

REPO_ROOT = Path(__file__).resolve().parents[1]
REQ = get_all_requirements()[0]["id"]


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
    path = tmp_path / "retention.sqlite3"
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


def _seed(db, *, client=None, client_name="Acme Corp", name="Acme gap", status="active"):
    if client is None:
        client = Client(name=client_name, industry="Technology", size="medium")
        db.add(client)
        db.flush()
    engagement = Engagement(client_id=client.id, name=name, status=status)
    db.add(engagement)
    db.flush()
    assessment = Assessment(
        company_name=client.name,
        industry="Technology",
        company_size="medium",
        selected_frameworks=json.dumps(["dpdpa"]),
        engagement_id=engagement.id,
        applicable_requirements=json.dumps([REQ]),
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
    return client, engagement, assessment


def _pdf(value: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(0, 10, value)
    return bytes(pdf.output())


def _add_evidence(db, engagement, assessment, upload_root, *, value="evidence"):
    evidence_id = _new_id()
    version_id = _new_id()
    storage_path = f"evidence/{engagement.id}/{evidence_id}/v1.pdf"
    content = _pdf(value)
    path = upload_root / storage_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    evidence = Evidence(
        id=evidence_id,
        engagement_id=engagement.id,
        assessment_id=assessment.id,
        document_category="privacy_policy",
        original_filename="evidence.pdf",
        storage_path=storage_path,
        file_hash_sha256=hashlib.sha256(content).hexdigest(),
        file_size_bytes=len(content),
        mime_type="application/pdf",
        status="active",
        uploaded_by="consultant:Priya",
    )
    version = EvidenceVersion(
        id=version_id,
        evidence_id=evidence_id,
        version_number=1,
        storage_path=storage_path,
        file_hash_sha256=hashlib.sha256(content).hexdigest(),
        file_size_bytes=len(content),
        change_reason=None,
        status="active",
        original_filename="evidence.pdf",
        mime_type="application/pdf",
        extracted_text=value,
    )
    db.add_all([evidence, version])
    db.flush()
    return evidence, version


def _add_snapshot(db, upload_root, *, assessment_id=None, engagement_id=None, value="snapshot"):
    snapshot_id = _new_id()
    if assessment_id:
        storage_path = f"reports/assessments/{assessment_id}/{snapshot_id}.pdf"
    else:
        storage_path = f"reports/engagements/{engagement_id}/{snapshot_id}.pdf"
    path = upload_root / storage_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value.encode())
    snapshot = ReportSnapshot(
        id=snapshot_id,
        assessment_id=assessment_id,
        engagement_id=engagement_id,
        type="gap_report" if assessment_id else "integrated_report",
        format="pdf",
        storage_path=storage_path,
        is_issued=True,
    )
    db.add(snapshot)
    db.flush()
    return snapshot


def _add_structural_rows(db, assessment, *, snapshot=None):
    report = GapReport(
        assessment_id=assessment.id,
        overall_score=0,
        chapter_scores=json.dumps({}),
        executive_summary="summary",
        raw_ai_response=json.dumps({}),
        framework_scores=json.dumps({"dpdpa": {}}),
    )
    db.add(report)
    db.flush()
    db.add(
        GapItem(
            report_id=report.id,
            requirement_id=REQ,
            framework_id="dpdpa",
            cluster_id=None,
            control_reference="S.5",
            chapter="Chapter II",
            requirement_title="Requirement",
            compliance_status="non_compliant",
            current_state="state",
            gap_description="gap",
            risk_level="medium",
            remediation_action="action",
            remediation_priority=1,
            remediation_effort="medium",
            timeline_weeks=2,
        )
    )
    conclusion = Conclusion(
        assessment_id=assessment.id,
        requirement_id=REQ,
        framework_id="dpdpa",
        cluster_id=None,
        outcome="gap",
        rationale="rationale",
        evidence_summary="summary",
        gaps_identified="gap",
        risk_level="medium",
        recommended_action="action",
        ai_proposed=False,
    )
    db.add(conclusion)
    db.flush()
    finding = Finding(
        assessment_id=assessment.id,
        conclusion_id=conclusion.id,
        title="Finding",
        description="Description",
        severity="medium",
        priority=1,
        status="in_progress",
    )
    db.add(finding)
    db.flush()
    action = Action(
        finding_id=finding.id,
        title="Action",
        owner="Owner",
        target_date=None,
        status="in_progress",
        history_json=json.dumps([{"action": "created"}]),
    )
    db.add(action)
    db.flush()
    return report, conclusion, finding, action


def _audit_rows(db, *, entity_id=None, action=None):
    query = select(AuditEvent).order_by(text("rowid"))
    if entity_id is not None:
        query = query.where(AuditEvent.entity_id == entity_id)
    if action is not None:
        query = query.where(AuditEvent.action == action)
    return db.scalars(query).all()


def _metadata(event):
    return json.loads(event.metadata_json)


def _snapshot(db, upload_root):
    tables = {
        table: db.execute(text(f"SELECT * FROM {table} ORDER BY rowid")).all()
        for table in sorted(Base.metadata.tables)
    }
    files = sorted(
        (
            str(path.relative_to(upload_root)),
            hashlib.sha256(path.read_bytes()).hexdigest(),
        )
        for path in upload_root.rglob("*")
        if path.is_file()
    )
    return tables, files


def _backdate_archive(db, engagement_id, *, years, days=1):
    record = retention.archive_record(db, engagement_id)
    assert record is not None
    moment = retention.add_years(datetime.now(timezone.utc), -years) - timedelta(days=days)
    db.execute(
        update(AuditEvent).where(AuditEvent.id == record.event_id).values(created_at=moment)
    )
    db.commit()


def _archive(http, engagement_id, reviewer="Priya"):
    response = http.post(
        f"/api/engagements/{engagement_id}/archive",
        data={"reviewer_name": reviewer},
    )
    assert response.status_code == 200, response.text
    return response


def _full_engagement(db, http, gate, upload_root, *, client=None, sentinel):
    client, engagement, assessment = _seed(
        db,
        client=client,
        client_name="Full Client" if client is None else client.name,
        name=f"Full engagement {sentinel[-2:]}",
    )
    second = Assessment(
        company_name=client.name,
        industry="Technology",
        company_size="medium",
        selected_frameworks=json.dumps(["dpdpa"]),
        engagement_id=engagement.id,
        status="archived",
        applicable_requirements=json.dumps([REQ]),
    )
    db.add(second)
    db.flush()
    db.add(
        QuestionnaireResponse(
            assessment_id=second.id,
            question_id="Q2",
            answer="partially_implemented",
            notes=sentinel,
        )
    )
    report, conclusion, finding, action = _add_structural_rows(db, assessment)
    run = AnalysisRun(
        assessment_id=assessment.id,
        framework_id="dpdpa",
        status="completed",
        claims_json=json.dumps({"sentinel": sentinel}),
        model_id="test-model",
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
    )
    db.add(run)
    db.flush()
    db.add(
        ConclusionRevision(
            conclusion_id=conclusion.id,
            actor="consultant:Priya",
            action="created",
            previous_outcome=None,
            previous_rationale=None,
            citations_json=None,
            analysis_run_id=run.id,
        )
    )
    db.add(
        Initiative(
            report_id=report.id,
            initiative_id="INIT-001",
            title="Initiative",
            root_cause="Root cause",
            root_cause_category="process",
            requirements_addressed=json.dumps([REQ]),
            combined_effort="medium",
            combined_timeline_weeks=4,
            priority=1,
            budget_estimate_band=None,
            suggested_approach="Approach",
        )
    )
    db.add(
        DeskReviewSummary(
            assessment_id=assessment.id,
            document_catalog=json.dumps([]),
            coverage_summary=json.dumps({}),
            raw_ai_response=json.dumps({}),
            status="completed",
        )
    )
    db.add(
        DeskReviewFinding(
            assessment_id=assessment.id,
            finding_type="evidence",
            requirement_id=REQ,
            content="Desk review",
            citations_json=None,
        )
    )
    db.add(
        RFIDocument(
            assessment_id=assessment.id,
            title="RFI",
            introduction="Introduction",
            evidence_items=json.dumps([]),
            response_instructions="Instructions",
            appendix=None,
            total_items=0,
            critical_items=0,
            raw_ai_response=None,
        )
    )
    db.add(AssessmentPack(assessment_id=assessment.id, framework_id="dpdpa", pack_version="1"))
    evidence, version = _add_evidence(db, engagement, assessment, upload_root, value=sentinel)
    second_path = f"evidence/{engagement.id}/{evidence.id}/v2.pdf"
    second_bytes = _pdf(f"{sentinel} second")
    (upload_root / second_path).write_bytes(second_bytes)
    db.add(
        EvidenceVersion(
            id=_new_id(),
            evidence_id=evidence.id,
            version_number=2,
            storage_path=second_path,
            file_hash_sha256=hashlib.sha256(second_bytes).hexdigest(),
            file_size_bytes=len(second_bytes),
            change_reason="second",
            status="active",
            original_filename="second.pdf",
            mime_type="application/pdf",
            extracted_text=f"{sentinel} second",
        )
    )
    db.add(EvidenceUse(
        evidence_id=evidence.id,
        assessment_id=assessment.id,
        framework_id="dpdpa",
        requirement_id=REQ,
        relevance="supporting",
    ))
    db.add(
        ConclusionRevision(
            conclusion_id=conclusion.id,
            actor="consultant:Priya",
            action="edited",
            previous_outcome="gap",
            previous_rationale="rationale",
            citations_json=json.dumps([{"evidence_version_id": version.id}]),
            analysis_run_id=None,
        )
    )
    db.add(
        DeskReviewFinding(
            assessment_id=assessment.id,
            finding_type="evidence",
            requirement_id=REQ,
            content="Citation",
            citations_json=json.dumps([{"evidence_version_id": version.id}]),
        )
    )
    action.history_json = json.dumps(
        [{"action": "created", "evidence": {"evidence_version_id": version.id}}]
    )
    db.flush()
    _add_snapshot(db, upload_root, assessment_id=assessment.id, value=sentinel)
    _add_snapshot(db, upload_root, assessment_id=second.id, value=f"{sentinel} workpaper")
    _add_snapshot(db, upload_root, engagement_id=engagement.id, value=f"{sentinel} integrated")
    db.execute(
        insert(AssessmentDocument).values(
            id=_new_id(),
            assessment_id=assessment.id,
            filename="legacy.pdf",
            file_path=str(upload_root / assessment.id / "legacy.pdf"),
            file_type="pdf",
            document_category="privacy_policy",
            extracted_text=sentinel,
        )
    )
    legacy_path = upload_root / assessment.id / "legacy.pdf"
    legacy_path.parent.mkdir(parents=True, exist_ok=True)
    legacy_path.write_bytes(_pdf(f"{sentinel} legacy"))
    from app.services.magic_links import create_link

    create_link(
        db,
        engagement_id=engagement.id,
        item_titles=["Policy"],
        expires_in_days=7,
        max_uploads=20,
        max_total_mb=100,
    )
    db.commit()
    return {
        "client": client,
        "engagement": engagement,
        "assessment": assessment,
        "second_assessment": second,
        "evidence": evidence,
        "version": version,
        "finding": finding,
        "action": action,
    }


def test_scenario_1_constants_structure_and_fk_order(db):
    """Scenario 1: constants, public boundaries, route registration, and delete ordering are exact."""
    assert retention.ARCHIVED_STATUS == "archived"
    assert retention.ARCHIVABLE_STATUSES == ("active", "closed")
    assert retention.RETENTION_YEARS_RANGE == (1, 50)
    assert retention.PURGE_ORDER == (
        "evidence_uses", "actions", "findings", "conclusion_revisions", "conclusions",
        "analysis_runs", "initiatives", "gap_items", "gap_reports", "desk_review_findings",
        "desk_review_summaries", "questionnaire_responses", "rfi_documents", "assessment_packs",
        "report_snapshots", "evidence_versions", "evidence", "assessment_documents",
        "magic_links", "assessments", "engagements",
    )
    assert retention.RETAINED_TABLES == ("clients", "audit_events")
    assert retention.REFUSAL_REASONS == (
        "not_archived", "archive_record_missing", "retention_invalid",
        "retention_not_elapsed", "active_dependencies", "storage_layout_invalid",
    )
    assert retention.DEPENDENCY_CODES == (
        "evidence_used_elsewhere", "evidence_cited_elsewhere",
        "evidence_linked_elsewhere", "blob_shared_elsewhere",
    )
    assert {
        retention.ARCHIVED_EVENT,
        retention.UNARCHIVED_EVENT,
        retention.PURGE_REFUSED_EVENT,
        retention.PURGED_EVENT,
        retention.PURGE_BLOBS_REMOVED_EVENT,
        retention.RETENTION_CHANGED_EVENT,
    } == {
        "engagement.archived", "engagement.unarchived", "engagement.purge_refused",
        "engagement.purged", "engagement.purge_blobs_removed", "client.retention_changed",
    }
    assert retention.EVENT_SCHEMA_VERSION == 1
    assert retention.COMPLETION_SCRIPT_ACTOR == "system:purge-completion"
    assert retention.REASON_MESSAGES["not_archived"] == "Only an archived engagement can be purged."
    assert retention.DEPENDENCY_LABELS["blob_shared_elsewhere"] == "stored files shared with another engagement"
    assert set(Base.metadata.tables) == set(retention.PURGE_ORDER) | set(retention.RETAINED_TABLES)
    assert not set(retention.PURGE_ORDER) & set(retention.RETAINED_TABLES)
    positions = {name: index for index, name in enumerate(retention.PURGE_ORDER)}
    for table in Base.metadata.tables.values():
        for foreign_key in table.foreign_keys:
            parent = foreign_key.target_fullname.split(".", 1)[0]
            child = table.name
            if (
                child in positions
                and parent in positions
                and foreign_key.ondelete != "SET NULL"
            ):
                assert positions[child] < positions[parent]

    route_set = {
        (method, route.path)
        for route in app.routes
        if isinstance(route, APIRoute)
        for method in route.methods & {"POST", "PUT", "PATCH", "DELETE", "GET"}
        if any(token in route.path for token in ("/archive", "/unarchive", "/purge", "/retention"))
    }
    assert route_set == {
        ("POST", "/api/engagements/{engagement_id}/archive"),
        ("POST", "/api/engagements/{engagement_id}/unarchive"),
        ("GET", "/engagements/{engagement_id}/purge"),
        ("POST", "/api/engagements/{engagement_id}/purge"),
        ("POST", "/api/engagements/{engagement_id}/purge/complete"),
        ("POST", "/api/clients/{client_id}/retention"),
    }
    for function in (
        retention.archive_engagement,
        retention.unarchive_engagement,
        retention.set_client_retention,
        retention.build_purge_plan,
        retention.evaluate_purge,
        retention.retention_state,
        retention.archive_record,
        retention.pending_purges,
        retention.client_retention_view,
        retention.engagement_ids_for_path,
        retention.archived_engagement_ids,
    ):
        assert ".commit(" not in inspect.getsource(function)
    assert ".commit(" in inspect.getsource(retention.purge_engagement)
    assert ".commit(" in inspect.getsource(retention._finish_blob_removal)
    heads = subprocess.run(
        ["alembic", "heads"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout
    assert "8b2d5f7e1c34 (head)" in heads
    assert not list(REPO_ROOT.joinpath("app/models").rglob("*.py")) or all(
        "relationship(" not in path.read_text() for path in REPO_ROOT.joinpath("app/models").rglob("*.py")
    )
    app_files = list(REPO_ROOT.joinpath("app").rglob("*.py"))
    assert [path.relative_to(REPO_ROOT).as_posix() for path in app_files if "rmtree" in path.read_text()] == [
        "app/services/retention.py"
    ]
    assert all("delete(AuditEvent" not in path.read_text() for path in app_files)
    assert all("delete(Client" not in path.read_text() for path in app_files)
    assert all(
        "delete(Evidence" not in path.read_text()
        and "delete(EvidenceVersion" not in path.read_text()
        and "delete(ReportSnapshot" not in path.read_text()
        for path in app_files
        if path != REPO_ROOT / "app/services/retention.py"
    )


def test_scenario_2_archive_state_machine_and_views(db, http, upload_root, engine, monkeypatch):
    """Scenario 2: archive is audited, reversible, visible in the archive views, and refuses invalid transitions."""
    client, engagement, assessment = _seed(db)
    before = _snapshot(db, upload_root)
    response = _archive(http, engagement.id)
    assert response.headers["HX-Redirect"] == f"/engagements/{engagement.id}"
    db.expire_all()
    assert db.get(Engagement, engagement.id).status == "archived"
    events = _audit_rows(db, entity_id=engagement.id, action=retention.ARCHIVED_EVENT)
    assert len(events) == 1
    assert events[0].actor == "consultant:Priya"
    assert events[0].entity_type == "engagement"
    metadata = _metadata(events[0])
    assert set(metadata) == {"schema_version", "client_id", "previous_status", "retention_years"}
    assert metadata["previous_status"] == "active"
    assert metadata["retention_years"] == 7
    record = retention.archive_record(db, engagement.id)
    assert record is not None and record.archived_at.tzinfo is not None
    client_page = http.get(f"/clients/{client.id}").text
    assert "data-archived-engagement" in client_page
    assert f'id="archived-{engagement.id}"' in client_page
    assert f"{engagement.id}" not in http.get(
        f"/clients/{client.id}/engagements-list", headers={"HX-Request": "true"}
    ).text
    detail = http.get(f"/engagements/{engagement.id}")
    assert detail.status_code == 200
    assert "data-archived-banner" in detail.text
    assert "Eligible for permanent purge on or after" in detail.text
    assert retention.add_years(record.archived_at, 7).strftime("%d %b %Y") in detail.text
    assert "data-unarchive-control" in detail.text
    assert "data-purge-preview-link" in detail.text
    assert "data-archive-control" not in detail.text
    assert "data-archived-banner" in http.get(f"/assessments/{assessment.id}").text
    before = _snapshot(db, upload_root)
    response = http.post(f"/api/engagements/{engagement.id}/archive", data={"reviewer_name": "Priya"})
    assert response.status_code == 409 and response.json()["detail"] == retention.ALREADY_ARCHIVED
    assert _snapshot(db, upload_root) == before

    db.execute(update(Engagement).where(Engagement.id == engagement.id).values(status="draft"))
    db.commit()
    before = _snapshot(db, upload_root)
    response = http.post(f"/api/engagements/{engagement.id}/archive")
    assert response.status_code == 409 and response.json()["detail"] == retention.NOT_ARCHIVABLE
    assert _snapshot(db, upload_root) == before
    db.execute(update(Engagement).where(Engagement.id == engagement.id).values(status="active"))
    db.commit()

    for field in ("status", "desk_review_status"):
        db.execute(update(Assessment).where(Assessment.id == assessment.id).values(**{field: "analyzing"}))
        db.commit()
        before = _snapshot(db, upload_root)
        response = http.post(f"/api/engagements/{engagement.id}/archive")
        assert response.status_code == 409 and response.json()["detail"] == retention.ARCHIVE_IN_FLIGHT
        assert _snapshot(db, upload_root) == before
        db.execute(update(Assessment).where(Assessment.id == assessment.id).values(**{field: None if field == "desk_review_status" else "created"}))
        db.commit()

    def race(_db, _engagement_id):
        with engine.begin() as connection:
            connection.execute(update(Engagement).where(Engagement.id == engagement.id).values(status="closed"))
        return 0

    monkeypatch.setattr(retention, "_in_flight_count", race)
    before = _snapshot(db, upload_root)
    before_audits = _audit_rows(db)
    response = http.post(f"/api/engagements/{engagement.id}/archive")
    assert response.status_code == 409 and response.json()["detail"] == retention.ARCHIVE_CONFLICT
    db.expire_all()
    assert db.get(Engagement, engagement.id).status == "closed"
    assert _audit_rows(db) == before_audits
    monkeypatch.undo()
    response = _archive(http, engagement.id)
    assert _metadata(_audit_rows(db, entity_id=engagement.id, action=retention.ARCHIVED_EVENT)[-1])["previous_status"] == "closed"
    unknown = http.post(f"/api/engagements/missing/archive")
    assert unknown.status_code == 404 and unknown.json()["detail"] == retention.ENGAGEMENT_NOT_FOUND


def test_scenario_3_guard_matrix_reads_magic_links_and_isolation(db, http, upload_root):
    """Scenario 3: every engagement-scoped write is guarded while reads and another engagement remain usable."""
    client, engagement, assessment = _seed(db)
    report, conclusion, finding, action = _add_structural_rows(db, assessment)
    evidence, version = _add_evidence(db, engagement, assessment, upload_root)
    use = EvidenceUse(
        evidence_id=evidence.id,
        assessment_id=assessment.id,
        framework_id="dpdpa",
        requirement_id=REQ,
        relevance="supporting",
    )
    db.add(use)
    snapshot = _add_snapshot(db, upload_root, assessment_id=assessment.id)
    path = upload_root / snapshot.storage_path
    db.add(
        AuditEvent(
            actor="consultant:Priya",
            action="report_snapshot.generated",
            entity_type="report_snapshot",
            entity_id=snapshot.id,
            metadata_json=json.dumps(
                {
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "size_bytes": path.stat().st_size,
                    "storage_path": snapshot.storage_path,
                }
            ),
        )
    )
    from app.services.magic_links import create_link

    link = create_link(
        db,
        engagement_id=engagement.id,
        item_titles=["Policy"],
        expires_in_days=7,
        max_uploads=20,
        max_total_mb=100,
    )
    db.commit()
    _, other_engagement, _ = _seed(db, client=client, name="Other engagement")
    _archive(http, engagement.id)

    expected_unresolvable = {
        ("POST", "/engagements"),
        ("POST", "/assessments"),
        ("POST", "/assessments/new"),
        ("POST", "/api/assessments"),
        ("POST", "/magic/{token}"),
    }
    mutating = {"POST", "PUT", "PATCH", "DELETE"}
    exercised = set()
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        for method in route.methods & mutating:
            key = (method, route.path)
            if route.endpoint.__module__ == retention_router.__name__:
                assert retention_router.archive_write_guard not in [
                    dependency.call for dependency in route.dependant.dependencies
                ]
                continue
            calls = [dependency.call for dependency in route.dependant.dependencies]
            assert retention_router.archive_write_guard in calls
            params = re.findall(r"{([^}/]+)}", route.path)
            if not {"assessment_id", "engagement_id", "evidence_id"} & set(params):
                continue
            values = {
                "assessment_id": assessment.id,
                "engagement_id": engagement.id,
                "evidence_id": evidence.id,
                "document_id": _new_id(),
                "finding_id": finding.id,
                "action_id": action.id,
                "conclusion_id": conclusion.id,
                "snapshot_id": snapshot.id,
                "link_id": link.link.id,
                "use_id": use.id,
                "framework_id": "dpdpa",
                "item_id": "x",
            }
            url = route.path
            for parameter in params:
                url = url.replace("{" + parameter + "}", values.get(parameter, "x"))
            response = http.request(method, url, data={})
            assert response.status_code == 409, (method, route.path, response.text)
            assert response.json()["detail"] == retention.ARCHIVED_READ_ONLY
            assert response.headers["X-Toast-Type"] == "error"
            exercised.add(key)
    assert expected_unresolvable == {
        (method, route.path)
        for route in app.routes
        if isinstance(route, APIRoute)
        for method in route.methods & mutating
        if route.endpoint.__module__ != retention_router.__name__
        and not {"assessment_id", "engagement_id", "evidence_id"} & set(re.findall(r"{([^}/]+)}", route.path))
    }
    required = {
        ("POST", "/api/assessments/{assessment_id}/analyze"),
        ("POST", "/assessments/{assessment_id}/run-analysis"),
        ("POST", "/assessments/{assessment_id}/upload"),
        ("DELETE", "/assessments/{assessment_id}"),
        ("POST", "/api/evidence/{evidence_id}/transitions"),
        ("DELETE", "/api/evidence/{evidence_id}/uses/{use_id}"),
        ("POST", "/engagements/{engagement_id}/magic-links"),
        ("POST", "/api/engagements/{engagement_id}/integrated-reports"),
        ("POST", "/api/assessments/{assessment_id}/findings"),
        ("POST", "/api/assessments/{assessment_id}/conclusions/{conclusion_id}/approve"),
        ("POST", "/api/assessments/{assessment_id}/snapshots"),
        ("PATCH", "/api/assessments/{assessment_id}/review/items/{item_id}"),
    }
    assert required <= exercised
    before = _snapshot(db, upload_root)
    invalid_get = http.get(f"/magic/{link.token}")
    random_get = http.get("/magic/AAAAAAAAAAAAAAAAAAAAAA")
    assert invalid_get.status_code == random_get.status_code == 404
    assert invalid_get.content == random_get.content
    invalid_post = http.post(f"/magic/{link.token}", data={})
    random_post = http.post("/magic/AAAAAAAAAAAAAAAAAAAAAA", data={})
    assert invalid_post.status_code == random_post.status_code == 404
    assert invalid_post.content == random_post.content
    assert _snapshot(db, upload_root) == before

    for url in (
        f"/engagements/{engagement.id}",
        f"/engagements/{engagement.id}/remediation",
        f"/engagements/{engagement.id}/integrated-reports",
        f"/assessments/{assessment.id}",
        f"/assessments/{assessment.id}/findings",
        f"/assessments/{assessment.id}/conclusions",
        f"/assessments/{assessment.id}/workpaper",
        f"/assessments/{assessment.id}/snapshots",
        f"/api/assessments/{assessment.id}/snapshots/{snapshot.id}/file",
        f"/evidence/{evidence.id}",
    ):
        assert http.get(url).status_code == 200, url
    other_response = http.post(
        f"/engagements/{other_engagement.id}/magic-links",
        data={"items": "Other policy"},
    )
    assert other_response.status_code == 200
    assert retention.engagement_ids_for_path(db, {"engagement_id": engagement.id}) == {engagement.id}
    assert retention.engagement_ids_for_path(db, {"assessment_id": assessment.id}) == {engagement.id}
    assert retention.engagement_ids_for_path(db, {"evidence_id": evidence.id}) == {engagement.id}
    assert retention.engagement_ids_for_path(db, {"engagement_id": "unknown"}) == {"unknown"}
    orphan = Assessment(
        company_name="Orphan",
        industry="Technology",
        company_size="medium",
        selected_frameworks=json.dumps(["dpdpa"]),
        engagement_id=None,
    )
    db.add(orphan)
    db.commit()
    assert retention.engagement_ids_for_path(db, {"assessment_id": orphan.id}) == set()
    assert retention.archived_engagement_ids(db, {engagement.id, other_engagement.id, "unknown"}) == {engagement.id}


def test_scenario_4_unarchive_restore_restart_and_conflicts(db, http, engine, upload_root, monkeypatch):
    """Scenario 4: unarchive restores the recorded status, restarts the clock, and uses CAS."""
    client, engagement, _ = _seed(db)
    _archive(http, engagement.id)
    archive_event = retention.archive_record(db, engagement.id)
    response = http.post(f"/api/engagements/{engagement.id}/unarchive", data={"reviewer_name": "Priya"})
    assert response.status_code == 200 and response.json()["status"] == "active"
    event = _audit_rows(db, entity_id=engagement.id, action=retention.UNARCHIVED_EVENT)[-1]
    assert _metadata(event)["archive_event_id"] == archive_event.event_id
    assert _metadata(event)["restored_status"] == "active"
    assert http.post(f"/engagements/{engagement.id}/magic-links", data={"items": "Policy"}).status_code == 200

    _, closed, _ = _seed(db, client=client, name="Closed engagement", status="closed")
    _archive(http, closed.id)
    http.post(f"/api/engagements/{closed.id}/unarchive")
    db.expire_all()
    assert db.get(Engagement, closed.id).status == "closed"

    _, missing_record, _ = _seed(db, client=client, name="Missing archive record")
    db.execute(update(Engagement).where(Engagement.id == missing_record.id).values(status="archived"))
    db.commit()
    response = http.post(f"/api/engagements/{missing_record.id}/unarchive")
    assert response.status_code == 200 and response.json()["status"] == "active"
    event = _audit_rows(db, entity_id=missing_record.id, action=retention.UNARCHIVED_EVENT)[-1]
    assert _metadata(event)["archive_event_id"] is None

    _, restarted, _ = _seed(db, client=client, name="Restarted engagement")
    _archive(http, restarted.id)
    first = retention.archive_record(db, restarted.id)
    old_eligible = retention.retention_state(db, db.get(Engagement, restarted.id)).eligible_at
    http.post(f"/api/engagements/{restarted.id}/unarchive")
    _archive(http, restarted.id)
    second = retention.archive_record(db, restarted.id)
    new_eligible = retention.retention_state(db, db.get(Engagement, restarted.id)).eligible_at
    assert second.event_id != first.event_id
    assert new_eligible > old_eligible

    _, active, _ = _seed(db, client=client, name="Not archived")
    before = _snapshot(db, upload_root)
    response = http.post(f"/api/engagements/{active.id}/unarchive")
    assert response.status_code == 409 and response.json()["detail"] == retention.NOT_ARCHIVED
    assert _snapshot(db, upload_root) == before

    _, raced, _ = _seed(db, client=client, name="Unarchive race")
    _archive(http, raced.id)
    original = retention.archive_record

    def race_record(session, engagement_id):
        record = original(session, engagement_id)
        with engine.begin() as connection:
            connection.execute(update(Engagement).where(Engagement.id == engagement_id).values(status="active"))
        return record

    monkeypatch.setattr(retention, "archive_record", race_record)
    before = _snapshot(db, upload_root)
    before_audits = _audit_rows(db)
    response = http.post(f"/api/engagements/{raced.id}/unarchive")
    assert response.status_code == 409 and response.json()["detail"] == retention.UNARCHIVE_CONFLICT
    assert _audit_rows(db) == before_audits


def test_scenario_5_retention_validation_floor_and_cas(db, http, engine, upload_root, monkeypatch):
    """Scenario 5: retention settings validate, audit once, use CAS, and honor the archive-time floor."""
    client, engagement, _ = _seed(db)
    response = http.post(f"/api/clients/{client.id}/retention", data={"retention_years": "10", "reviewer_name": "Priya"})
    assert response.status_code == 200 and response.json()["retention_years"] == 10
    db.expire_all()
    assert db.get(Client, client.id).retention_years == 10
    event = _audit_rows(db, entity_id=client.id, action=retention.RETENTION_CHANGED_EVENT)[-1]
    assert event.entity_type == "client"
    assert _metadata(event) == {"from": 7, "schema_version": 1, "to": 10}
    for invalid in ("", "0", "51", "7.5", "-1", "abc", None):
        before = _snapshot(db, upload_root)
        data = {} if invalid is None else {"retention_years": invalid}
        response = http.post(f"/api/clients/{client.id}/retention", data=data)
        assert response.status_code == 400 and response.json()["detail"] == retention.RETENTION_YEARS_INVALID
        assert _snapshot(db, upload_root) == before
    before = _snapshot(db, upload_root)
    response = http.post(f"/api/clients/{client.id}/retention", data={"retention_years": "10"})
    assert response.status_code == 200
    assert response.headers["X-Toast-Message"] == "Retention unchanged"
    assert _snapshot(db, upload_root) == before
    assert http.post("/api/clients/missing/retention", data={"retention_years": "10"}).status_code == 404

    original_update = retention.update

    def race_update(model, *args, **kwargs):
        statement = original_update(model, *args, **kwargs)
        if model is Client:
            with engine.begin() as connection:
                connection.execute(update(Client).where(Client.id == client.id).values(retention_years=11))
        return statement

    monkeypatch.setattr(retention, "update", race_update)
    before = _snapshot(db, upload_root)
    before_audits = _audit_rows(db)
    response = http.post(f"/api/clients/{client.id}/retention", data={"retention_years": "12"})
    assert response.status_code == 409 and response.json()["detail"] == retention.RETENTION_CONFLICT
    assert _audit_rows(db) == before_audits
    monkeypatch.undo()
    db.execute(update(Client).where(Client.id == client.id).values(retention_years=7))
    db.commit()

    _archive(http, engagement.id)
    state = retention.retention_state(db, db.get(Engagement, engagement.id))
    assert state.retention_years_applied == 7
    db.execute(update(Client).where(Client.id == client.id).values(retention_years=2))
    db.commit()
    assert retention.retention_state(db, db.get(Engagement, engagement.id)).retention_years_applied == 7
    db.execute(update(Client).where(Client.id == client.id).values(retention_years=10))
    db.commit()
    assert retention.retention_state(db, db.get(Engagement, engagement.id)).retention_years_applied == 10
    page = http.get(f"/clients/{client.id}")
    assert 'data-retention-form' in page.text and 'value="10"' in page.text


def test_scenario_6_retention_refusal_preview_post_and_arithmetic(db, http, upload_root):
    """Scenario 6: retention blocks purge until the inclusive eligibility instant and is audited once after confirmation."""
    client, engagement, _ = _seed(db)
    _archive(http, engagement.id)
    state = retention.retention_state(db, db.get(Engagement, engagement.id))
    preview = http.get(f"/engagements/{engagement.id}/purge")
    assert preview.status_code == 200
    assert 'data-purge-reason="retention_not_elapsed"' in preview.text
    assert "data-purge-form" not in preview.text
    plan = retention.build_purge_plan(db, db.get(Engagement, engagement.id))
    for table, count in plan.row_counts.items():
        assert f'data-purge-count="{table}"' in preview.text
        assert re.search(rf'data-purge-count="{table}"[^>]*>\s*<th[^>]*>[^<]+</th>\s*<td[^>]*>{count}</td>', preview.text)
    before = _snapshot(db, upload_root)
    response = http.post(f"/api/engagements/{engagement.id}/purge", data={"confirm_name": engagement.name})
    assert response.status_code == 409
    payload = response.json()
    assert payload["reasons"] == ["retention_not_elapsed"]
    assert payload["detail"] == retention.REASON_MESSAGES["retention_not_elapsed"].format(eligible_at=state.eligible_at)
    assert payload["eligible_at"] == state.eligible_at.isoformat()
    assert payload["dependencies"] == [] and payload["layout_violations"] == 0
    after = _snapshot(db, upload_root)
    assert after[0].keys() == before[0].keys()
    for table in before[0]:
        if table == "audit_events":
            assert len(after[0][table]) == len(before[0][table]) + 1
        else:
            assert after[0][table] == before[0][table]
    refusal = _audit_rows(db, entity_id=engagement.id, action=retention.PURGE_REFUSED_EVENT)[-1]
    assert set(_metadata(refusal)) == {
        "schema_version", "reasons", "dependencies", "layout_violations",
        "archived_at", "retention_years_applied", "eligible_at",
    }
    assert retention.evaluate_purge(
        db, db.get(Engagement, engagement.id), plan, now=state.eligible_at - timedelta(microseconds=1)
    ).reasons == ("retention_not_elapsed",)
    assert "retention_not_elapsed" not in retention.evaluate_purge(
        db, db.get(Engagement, engagement.id), plan, now=state.eligible_at
    ).reasons
    leap = datetime(2028, 2, 29, tzinfo=timezone.utc)
    assert retention.add_years(leap, 1) == datetime(2029, 2, 28, tzinfo=timezone.utc)


def test_scenario_7_dependency_refusals_cover_all_codes(db, http, upload_root):
    """Scenario 7: every cross-engagement evidence dependency refuses purge with its exact code."""
    cases = []
    case_kinds = (
        "evidence_used_elsewhere",
        "evidence_cited_conclusion",
        "evidence_cited_desk",
        "evidence_cited_action",
        "evidence_linked_elsewhere",
        "blob_shared_elsewhere",
    )
    for index, kind in enumerate(case_kinds):
        code = "evidence_cited_elsewhere" if kind.startswith("evidence_cited") else kind
        client, engagement, assessment = _seed(
            db,
            client_name=f"Dependency Client {index}",
            name=f"Dependency engagement {index}",
        )
        _, other, other_assessment = _seed(
            db,
            client=client,
            name=f"Other engagement {index}",
        )
        evidence, version = _add_evidence(db, engagement, assessment, upload_root, value=f"case {index}")
        if code == "evidence_used_elsewhere":
            db.add(EvidenceUse(
                evidence_id=evidence.id,
                assessment_id=other_assessment.id,
                framework_id="dpdpa",
                requirement_id=REQ,
                relevance="supporting",
            ))
        elif kind == "evidence_cited_conclusion":
            conclusion = Conclusion(
                assessment_id=other_assessment.id,
                requirement_id=REQ,
                framework_id="dpdpa",
                outcome="gap",
                rationale="rationale",
                evidence_summary="summary",
                gaps_identified="gap",
                risk_level="medium",
                recommended_action="action",
                ai_proposed=False,
            )
            db.add(conclusion)
            db.flush()
            db.add(ConclusionRevision(
                conclusion_id=conclusion.id,
                actor="consultant:Priya",
                action="edited",
                citations_json=json.dumps([{"evidence_version_id": version.id}]),
            ))
        elif kind == "evidence_cited_desk":
            db.add(DeskReviewFinding(
                assessment_id=other_assessment.id,
                finding_type="evidence",
                requirement_id=REQ,
                content="Other desk review",
                citations_json=json.dumps([{"evidence_version_id": version.id}]),
            ))
        elif kind == "evidence_cited_action":
            _, other_conclusion, _, _ = _add_structural_rows(db, other_assessment)
            other_finding = Finding(
                assessment_id=other_assessment.id,
                conclusion_id=other_conclusion.id,
                title="Other finding",
                description="Description",
                severity="medium",
                priority=1,
                status="in_progress",
            )
            db.add(other_finding)
            db.flush()
            db.add(Action(
                finding_id=other_finding.id,
                title="Other action",
                owner=None,
                target_date=None,
                status="in_progress",
                history_json=json.dumps({"evidence_version_id": version.id}),
            ))
        elif kind == "evidence_linked_elsewhere":
            linked, _ = _add_evidence(db, other, other_assessment, upload_root, value="linked")
            linked.assessment_id = assessment.id
        else:
            other_evidence, _ = _add_evidence(db, other, other_assessment, upload_root, value="shared")
            db.add(EvidenceVersion(
                evidence_id=other_evidence.id,
                version_number=2,
                storage_path=f"evidence/{engagement.id}/shared/v2.pdf",
                file_hash_sha256="0" * 64,
                file_size_bytes=1,
                change_reason=None,
                status="active",
                original_filename="shared.pdf",
                mime_type="application/pdf",
            ))
        cases.append((engagement, assessment, evidence, version, code))
        db.commit()

    for engagement, assessment, evidence, version, code in cases:
        _archive(http, engagement.id)
        _backdate_archive(db, engagement.id, years=8)
        response = http.post(
            f"/api/engagements/{engagement.id}/purge",
            data={"confirm_name": engagement.name},
        )
        assert response.status_code == 409, response.text
        payload = response.json()
        assert payload["reasons"] == ["active_dependencies"]
        assert payload["dependencies"] == [{"code": code, "count": 1}]
        expected = retention.DEPENDENCY_LABELS[code] + " (1)"
        assert payload["detail"] == retention.REASON_MESSAGES["active_dependencies"].format(dependencies=expected)
        refusal = _audit_rows(db, entity_id=engagement.id, action=retention.PURGE_REFUSED_EVENT)[-1]
        assert [row for row in _metadata(refusal)["dependencies"] if row["count"]] == [{"code": code, "count": 1}]


def test_scenario_8_other_refusals_both_layout_and_confirmation(db, http, upload_root):
    """Scenario 8: all remaining refusal reasons, the combined case, and confirmation mismatch are fail closed."""
    client, engagement, assessment = _seed(db, name="Both engagement")
    _, other, other_assessment = _seed(db, client=client, name="Both other")
    evidence, _ = _add_evidence(db, engagement, assessment, upload_root)
    db.add(EvidenceUse(
        evidence_id=evidence.id,
        assessment_id=other_assessment.id,
        framework_id="dpdpa",
        requirement_id=REQ,
        relevance="supporting",
    ))
    db.commit()
    _archive(http, engagement.id)
    _backdate_archive(db, engagement.id, years=0, days=1)
    response = http.get(f"/engagements/{engagement.id}/purge")
    assert 'data-purge-reason="retention_not_elapsed"' in response.text
    assert 'data-purge-reason="active_dependencies"' in response.text

    _, not_archived, _ = _seed(db, client=client, name="Not archived purge")
    response = http.post(f"/api/engagements/{not_archived.id}/purge", data={"confirm_name": not_archived.name})
    assert response.status_code == 409
    assert response.json()["reasons"] == ["not_archived"]
    assert response.json()["detail"] == retention.REASON_MESSAGES["not_archived"]
    assert response.json()["dependencies"] == []

    _, no_record, _ = _seed(db, client=client, name="No archive record")
    db.execute(update(Engagement).where(Engagement.id == no_record.id).values(status="archived"))
    db.commit()
    response = http.post(f"/api/engagements/{no_record.id}/purge", data={"confirm_name": no_record.name})
    assert response.status_code == 409 and response.json()["reasons"] == ["archive_record_missing"]

    _, invalid_retention, _ = _seed(db, client=client, name="Invalid retention")
    _archive(http, invalid_retention.id)
    _backdate_archive(db, invalid_retention.id, years=8)
    db.execute(update(Client).where(Client.id == client.id).values(retention_years=0))
    db.commit()
    response = http.post(f"/api/engagements/{invalid_retention.id}/purge", data={"confirm_name": invalid_retention.name})
    assert response.status_code == 409 and response.json()["reasons"] == ["retention_invalid"]
    db.execute(update(Client).where(Client.id == client.id).values(retention_years=7))
    db.commit()

    _, bad_layout, bad_assessment = _seed(db, client=client, name="Bad layout")
    bad_evidence, bad_version = _add_evidence(db, bad_layout, bad_assessment, upload_root)
    bad_path = upload_root / "elsewhere" / "x.pdf"
    bad_path.parent.mkdir()
    bad_path.write_bytes(b"outside")
    db.execute(update(EvidenceVersion).where(EvidenceVersion.id == bad_version.id).values(storage_path="elsewhere/x.pdf"))
    db.commit()
    _archive(http, bad_layout.id)
    _backdate_archive(db, bad_layout.id, years=8)
    response = http.post(f"/api/engagements/{bad_layout.id}/purge", data={"confirm_name": bad_layout.name})
    assert response.status_code == 409
    assert response.json()["reasons"] == ["storage_layout_invalid"]
    assert response.json()["layout_violations"] == 1
    assert bad_path.exists()
    bad_path.unlink()
    response = http.get(f"/engagements/{bad_layout.id}/purge")
    assert response.status_code == 200 and 'data-purge-form' in response.text

    before = _snapshot(db, upload_root)
    for confirmation in ("wrong", "", bad_layout.name.lower()):
        response = http.post(
            f"/api/engagements/{bad_layout.id}/purge",
            data={"confirm_name": confirmation},
        )
        assert response.status_code == 400 and response.json()["detail"] == retention.CONFIRM_MISMATCH
        assert _snapshot(db, upload_root) == before
    assert http.post("/api/engagements/missing/purge", data={"confirm_name": "x"}).status_code == 404
    both_preview = http.get(f"/engagements/{engagement.id}/purge")
    assert both_preview.status_code == 200
    assert 'data-purge-reason="retention_not_elapsed"' in both_preview.text or 'data-purge-reason="active_dependencies"' in both_preview.text
    assert 'data-purge-dependency="evidence_used_elsewhere"' in both_preview.text


def test_scenario_9_successful_purge_is_scoped_audited_and_secure(db, http, gate, upload_root, db_path, engine):
    """Scenario 9: an eligible purge removes only the target engagement, its roots, and its database rows."""
    target = _full_engagement(db, http, gate, upload_root, sentinel="PURGE-SENTINEL-7Q")
    control = _full_engagement(db, http, gate, upload_root, client=target["client"], sentinel="CONTROL-SENTINEL-3K")
    _archive(http, target["engagement"].id)
    _backdate_archive(db, target["engagement"].id, years=7)
    target_engagement = db.get(Engagement, target["engagement"].id)
    target_id = target_engagement.id
    target_name = target_engagement.name
    target_assessment_id = target["assessment"].id
    target_second_assessment_id = target["second_assessment"].id
    target_evidence_id = target["evidence"].id
    target_version_id = target["version"].id
    plan = retention.build_purge_plan(db, target_engagement)
    preview = http.get(f"/engagements/{target_engagement.id}/purge")
    assert preview.status_code == 200 and "data-purge-form" in preview.text
    assert all(count > 0 for table, count in plan.row_counts.items() if table in {
        "actions", "findings", "conclusions", "analysis_runs", "initiatives", "gap_items",
        "gap_reports", "desk_review_findings", "desk_review_summaries", "questionnaire_responses",
        "rfi_documents", "assessment_packs", "report_snapshots", "evidence_versions", "evidence",
        "assessment_documents", "magic_links", "assessments", "engagements",
    })
    pre_audits = [(event.id, event.action, event.entity_id, event.metadata_json) for event in _audit_rows(db)]
    control_ids = {
        control["engagement"].id,
        control["assessment"].id,
        control["second_assessment"].id,
        control["evidence"].id,
        control["version"].id,
    }
    before_rows = {
        table: tuple(
            row for row in db.execute(text(f"SELECT * FROM {table} ORDER BY rowid")).all()
            if any(value in control_ids for value in row if isinstance(value, str))
        )
        for table in Base.metadata.tables
    }
    control_files = {
        str(path.relative_to(upload_root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in upload_root.rglob("*")
        if path.is_file() and any(
            value in str(path) for value in (control["engagement"].id, control["assessment"].id, control["second_assessment"].id)
        )
    }
    roots_before = {root: (upload_root / root).exists() for root in plan.blob_roots}
    response = http.post(
        f"/api/engagements/{target_id}/purge",
        data={"confirm_name": target_name, "reviewer_name": "Priya"},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["row_counts"] == plan.row_counts and payload["blobs_removed"] is True
    for table in retention.PURGE_ORDER:
        if table == "engagements":
            assert db.get(Engagement, target_id) is None
        elif table == "assessments":
            assert db.get(Assessment, target_assessment_id) is None
            assert db.get(Assessment, target_second_assessment_id) is None
        elif table == "evidence":
            assert db.get(Evidence, target_evidence_id) is None
        elif table == "evidence_versions":
            assert db.get(EvidenceVersion, target_version_id) is None
    assert db.get(Client, target["client"].id) is not None
    for table in Base.metadata.tables:
        remaining = tuple(
            row for row in db.execute(text(f"SELECT * FROM {table} ORDER BY rowid")).all()
            if any(value in control_ids for value in row if isinstance(value, str))
        )
        assert remaining == before_rows[table]
    current_files = {
        str(path.relative_to(upload_root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in upload_root.rglob("*")
        if path.is_file()
    }
    assert control_files.items() <= current_files.items()
    assert all(not (upload_root / root).exists() for root in plan.blob_roots)
    assert (upload_root / "evidence").exists()
    assert retention.pending_purges(db) == []
    assert http.get(f"/engagements/{target_id}").status_code == 404
    assert http.get(f"/engagements/{target_id}/purge").status_code == 404
    assert http.post(f"/api/engagements/{target_id}/purge", data={"confirm_name": target_name}).status_code == 404
    page = http.get(f"/clients/{target['client'].id}")
    assert "data-purge-record" in page.text and "Files removed" in page.text
    audit_after = [(event.id, event.action, event.entity_id, event.metadata_json) for event in _audit_rows(db)]
    assert audit_after[: len(pre_audits)] == pre_audits
    new_events = _audit_rows(db, entity_id=target_id)
    assert [event.action for event in new_events[-2:]] == [retention.PURGED_EVENT, retention.PURGE_BLOBS_REMOVED_EVENT]
    assert set(_metadata(new_events[-2])) == {
        "schema_version", "client_id", "engagement_name", "archive_event_id", "archived_at",
        "retention_years_applied", "eligible_at", "assessment_ids", "row_counts", "blob_roots",
        "blob_file_count",
    }
    assert _metadata(new_events[-2])["blob_roots"] == list(plan.blob_roots)
    completion_metadata = _metadata(new_events[-1])
    assert set(completion_metadata["removed_roots"]) | set(completion_metadata["missing_roots"]) == set(plan.blob_roots)
    assert not set(completion_metadata["removed_roots"]) & set(completion_metadata["missing_roots"])
    assert set(completion_metadata["removed_roots"]) == {
        root for root, existed in roots_before.items() if existed
    }
    assert not db.execute(text("PRAGMA foreign_key_check")).all()
    assert db.execute(text("PRAGMA integrity_check")).scalar_one() == "ok"
    db.close()
    engine.dispose()
    raw = db_path.read_bytes()
    assert b"PURGE-SENTINEL-7Q" not in raw
    assert b"CONTROL-SENTINEL-3K" in raw


def _eligible_with_blob(db, http, upload_root, *, name="Crash engagement"):
    client, engagement, assessment = _seed(
        db,
        client_name=f"Client for {name}",
        name=name,
    )
    evidence, version = _add_evidence(db, engagement, assessment, upload_root, value=name)
    db.commit()
    _archive(http, engagement.id)
    _backdate_archive(db, engagement.id, years=8)
    return client, engagement, assessment, evidence, version


def test_scenario_10_crash_safety_failure_modes_and_ledger_validation(
    db, http, upload_root, engine, monkeypatch, caplog
):
    """Scenario 10: every pre-commit and post-commit failure mode is recoverable and fail closed."""
    _, before_commit, _, _, _ = _eligible_with_blob(db, http, upload_root, name="Before commit")
    before = _snapshot(db, upload_root)
    with monkeypatch.context() as patch:
        patch.setattr(retention, "_write_purged_event", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("forced")))
        response = http.post(
            f"/api/engagements/{before_commit.id}/purge",
            data={"confirm_name": before_commit.name},
        )
    assert response.status_code == 500 and response.json()["detail"] == retention.PURGE_FAILED
    assert _snapshot(db, upload_root) == before
    assert not _audit_rows(db, entity_id=before_commit.id, action=retention.PURGED_EVENT)
    assert db.get(Engagement, before_commit.id).status == "archived"
    assert http.post(
        f"/api/engagements/{before_commit.id}/purge",
        data={"confirm_name": before_commit.name},
    ).status_code == 200

    _, fk_target, fk_assessment, _, _ = _eligible_with_blob(db, http, upload_root, name="FK backstop")
    _, fk_other, fk_other_assessment = _seed(db, name="FK other")
    _, fk_conclusion, _, _ = _add_structural_rows(db, fk_assessment)
    db.add(Finding(
        assessment_id=fk_other_assessment.id,
        conclusion_id=fk_conclusion.id,
        title="Foreign finding",
        description="Foreign reference",
        severity="medium",
        priority=1,
        status="in_progress",
    ))
    db.commit()
    before = _snapshot(db, upload_root)
    response = http.post(f"/api/engagements/{fk_target.id}/purge", data={"confirm_name": fk_target.name})
    assert response.status_code == 500 and response.json()["detail"] == retention.PURGE_FAILED
    assert _snapshot(db, upload_root) == before

    _, mismatch, _, _, _ = _eligible_with_blob(db, http, upload_root, name="Rowcount mismatch")
    real_plan = retention.build_purge_plan(db, mismatch)
    broken_counts = dict(real_plan.row_counts)
    broken_counts["gap_items"] += 1
    with monkeypatch.context() as patch:
        patch.setattr(retention, "build_purge_plan", lambda *_args, **_kwargs: replace(real_plan, row_counts=broken_counts))
        before = _snapshot(db, upload_root)
        response = http.post(f"/api/engagements/{mismatch.id}/purge", data={"confirm_name": mismatch.name})
    assert response.status_code == 500 and response.json()["detail"] == retention.PURGE_FAILED
    assert _snapshot(db, upload_root) == before

    pending_client, pending, pending_assessment, _, _ = _eligible_with_blob(db, http, upload_root, name="Pending blobs")
    pending_id = pending.id
    pending_name = pending.name
    second_root = upload_root / f"reports/engagements/{pending_id}"
    second_root.mkdir(parents=True)
    (second_root / "pending.pdf").write_bytes(b"pending")
    real_remove = retention.shutil.rmtree
    calls = []

    def fail_after_first(path):
        calls.append(path)
        if len(calls) == 1:
            return real_remove(path)
        raise OSError("permission")

    with monkeypatch.context() as patch:
        patch.setattr(retention, "_remove_tree", fail_after_first)
        response = http.post(f"/api/engagements/{pending_id}/purge", data={"confirm_name": pending_name})
    assert response.status_code == 500
    assert response.json()["detail"] == retention.PURGE_BLOBS_PENDING
    assert response.json()["records_purged"] is True and response.json()["blobs_pending"] is True
    assert db.get(Engagement, pending_id) is None
    assert _audit_rows(db, entity_id=pending_id, action=retention.PURGED_EVENT)
    assert not _audit_rows(db, entity_id=pending_id, action=retention.PURGE_BLOBS_REMOVED_EVENT)
    assert not (upload_root / f"evidence/{pending_id}").exists()
    assert second_root.exists()
    pending_rows = retention.pending_purges(db)
    assert len(pending_rows) == 1 and pending_rows[0].blob_roots
    assert "Files pending removal" in http.get(f"/clients/{pending_client.id}").text
    response = http.post(f"/api/engagements/{pending_id}/purge/complete")
    assert response.status_code == 200 and response.json()["already_complete"] is False
    assert not second_root.exists()
    completion = _audit_rows(db, entity_id=pending_id, action=retention.PURGE_BLOBS_REMOVED_EVENT)[-1]
    assert f"evidence/{pending_id}" in _metadata(completion)["missing_roots"]
    audit_count = len(_audit_rows(db, entity_id=pending_id))
    response = http.post(f"/api/engagements/{pending_id}/purge/complete")
    assert response.status_code == 200 and response.json()["already_complete"] is True
    assert len(_audit_rows(db, entity_id=pending_id)) == audit_count
    _, never, _, _, _ = _eligible_with_blob(db, http, upload_root, name="No pending")
    response = http.post(f"/api/engagements/{never.id}/purge/complete")
    assert response.status_code == 404 and response.json()["detail"] == retention.NO_PENDING_PURGE

    class SimulatedCrash(BaseException):
        pass

    _, crashed, _, _, _ = _eligible_with_blob(db, http, upload_root, name="Process death")
    crashed_id = crashed.id
    crashed_name = crashed.name
    roots = retention.build_purge_plan(db, crashed).blob_roots
    with monkeypatch.context() as patch:
        patch.setattr(retention, "_remove_tree", lambda _path: (_ for _ in ()).throw(SimulatedCrash()))
        with pytest.raises(SimulatedCrash):
            retention.purge_engagement(
                db,
                engagement_id=crashed_id,
                confirm_name=crashed_name,
                actor="consultant:Priya",
            )
    new_db = sessionmaker(bind=engine)()
    try:
        assert new_db.get(Engagement, crashed_id) is None
        assert retention.pending_purges(new_db)[0].blob_roots == roots
        from scripts import complete_purges

        output = io.StringIO()
        assert complete_purges.run(new_db, out=output) == 0
        assert f"PENDING {crashed_id}" in output.getvalue()
        assert f"COMPLETED {crashed_id}" in output.getvalue()
        output = io.StringIO()
        assert complete_purges.run(new_db, list_only=True, out=output) == 0
        assert output.getvalue() == ""
    finally:
        new_db.close()

    _, existing_ledger, _, _, _ = _eligible_with_blob(db, http, upload_root, name="Existing ledger")
    tampered = AuditEvent(
        actor="consultant:Priya",
        action=retention.PURGED_EVENT,
        entity_type="engagement",
        entity_id=existing_ledger.id,
        metadata_json=json.dumps({"assessment_ids": [], "blob_roots": []}),
    )
    db.add(tampered)
    db.commit()
    response = http.post(f"/api/engagements/{existing_ledger.id}/purge/complete")
    assert response.status_code == 409 and response.json()["detail"] == retention.PURGE_LEDGER_INCONSISTENT

    outside = upload_root.parent / "outside"
    outside.mkdir(exist_ok=True)
    (outside / "keep.txt").write_text("keep")
    tampered_id = _new_id()
    assessment_id = _new_id()
    expected_roots = list(retention._blob_roots(tampered_id, (assessment_id,)))
    variants = (
        expected_roots[:1] + ["../outside"],
        expected_roots + [f"reports/assessments/{_new_id()}"],
        expected_roots[:-1],
    )
    for roots_variant in variants:
        db.add(AuditEvent(
            actor="consultant:Priya",
            action=retention.PURGED_EVENT,
            entity_type="engagement",
            entity_id=tampered_id,
            metadata_json=json.dumps({"assessment_ids": [assessment_id], "blob_roots": roots_variant}),
        ))
        db.commit()
        response = http.post(f"/api/engagements/{tampered_id}/purge/complete")
        assert response.status_code == 409 and response.json()["detail"] == retention.PURGE_LEDGER_INVALID
        assert (outside / "keep.txt").exists()

    _, symlinked, symlink_assessment, _, _ = _eligible_with_blob(db, http, upload_root, name="Symlink root")
    symlink_target = upload_root.parent / "symlink-target"
    symlink_target.mkdir(exist_ok=True)
    (symlink_target / "keep.txt").write_text("keep")
    symlink_root = upload_root / f"evidence/{symlinked.id}"
    real_remove(symlink_root)
    symlink_root.symlink_to(symlink_target, target_is_directory=True)
    response = http.post(f"/api/engagements/{symlinked.id}/purge", data={"confirm_name": symlinked.name})
    assert response.status_code == 409 and response.json()["reasons"] == ["storage_layout_invalid"]
    assert (symlink_target / "keep.txt").exists()


def test_scenario_11_stale_preview_and_double_purge(db, http, upload_root):
    """Scenario 11: stale previews cannot purge, and committed purges are one-shot."""
    client, engagement, _ = _seed(db, client_name="Concurrency client", name="Stale preview")
    engagement_id = engagement.id
    engagement_name = engagement.name
    assert http.post(f"/api/engagements/{engagement_id}/archive").status_code == 200
    preview = http.get(f"/engagements/{engagement_id}/purge")
    assert preview.status_code == 200
    assert http.post(f"/api/engagements/{engagement_id}/unarchive").status_code == 200
    response = http.post(
        f"/api/engagements/{engagement_id}/purge",
        data={"confirm_name": engagement_name},
    )
    assert response.status_code == 409
    assert response.json()["reasons"] == ["not_archived"]
    assert db.get(Engagement, engagement_id).status == "active"
    assert not _audit_rows(db, entity_id=engagement_id, action=retention.PURGED_EVENT)
    assert client.id == db.get(Client, client.id).id

    _, purged, _, _, _ = _eligible_with_blob(
        db, http, upload_root, name="Double purge"
    )
    purged_id = purged.id
    purged_name = purged.name
    assert http.post(
        f"/api/engagements/{purged_id}/purge",
        data={"confirm_name": purged_name},
    ).status_code == 200
    second = http.post(
        f"/api/engagements/{purged_id}/purge",
        data={"confirm_name": purged_name},
    )
    assert second.status_code == 404
    assert second.json()["detail"] == retention.ALREADY_PURGED
    with pytest.raises(retention.RetentionNotFound, match=retention.ALREADY_PURGED):
        retention.purge_engagement(
            db,
            engagement_id=purged_id,
            confirm_name=purged_name,
            actor="consultant:Priya",
        )


def test_scenario_12_never_auto_purges_and_survives_lifespan(db, http, upload_root):
    """Scenario 12: purge has only its two explicit call sites and no startup trigger."""
    app_sources = {
        path: path.read_text()
        for path in (REPO_ROOT / "app").rglob("*.py")
    }
    purge_calls = [
        str(path.relative_to(REPO_ROOT))
        for path, source in app_sources.items()
        if re.search(r"purge_engagement\(", source)
    ]
    completion_calls = [
        str(path.relative_to(REPO_ROOT))
        for path, source in app_sources.items()
        if re.search(r"complete_pending_purge\(", source)
    ]
    assert set(purge_calls) == {
        "app/services/retention.py",
        "app/routers/retention.py",
    }
    assert set(completion_calls) == {
        "app/services/retention.py",
        "app/routers/retention.py",
    }
    assert "purge_engagement(" not in app_sources[REPO_ROOT / "app/main.py"]
    assert "complete_pending_purge(" not in app_sources[REPO_ROOT / "app/main.py"]
    assert "BackgroundTasks" not in app_sources[REPO_ROOT / "app/routers/retention.py"]

    _, engagement, assessment = _seed(
        db,
        client_name="Lifespan client",
        name="Survives startup",
    )
    engagement_id = engagement.id
    assert http.post(f"/api/engagements/{engagement_id}/archive").status_code == 200
    _backdate_archive(db, engagement_id, years=8)
    before = _snapshot(db, upload_root)
    with TestClient(app, raise_server_exceptions=False) as restarted:
        assert restarted.get(f"/engagements/{engagement_id}").status_code == 200
        assert restarted.get(f"/clients/{engagement.client_id}").status_code == 200
        assert restarted.get(f"/assessments/{assessment.id}").status_code == 200
    assert _snapshot(db, upload_root) == before


def test_scenario_13_only_new_retention_test_file_changes():
    """Scenario 13: no existing test file is modified by this handoff."""
    changed_tests = subprocess.run(
        ["git", "diff", "--name-only", "--", "tests"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    staged_tests = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--", "tests"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    assert changed_tests == []
    assert staged_tests == []
    assert (REPO_ROOT / "tests/test_retention.py").exists()
