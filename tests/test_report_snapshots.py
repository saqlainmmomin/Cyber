"""Contract suite for P3-2 write-once report snapshots."""

from __future__ import annotations

import copy
import hashlib
import inspect
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote

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
from app.models.assessment import Assessment, _new_id
from app.models.audit_event import AuditEvent
from app.models.client import Client
from app.models.conclusion import Conclusion, ConclusionRevision
from app.models.engagement import Engagement
from app.models.questionnaire import QuestionnaireResponse
from app.models.report import GapReport
from app.models.report_snapshot import ReportSnapshot
from app.routers import web
from app.services import report_snapshots
from app.services import approved_report

REPO_ROOT = Path(__file__).resolve().parents[1]
REQS = [row["id"] for row in get_all_requirements()][:3]
INTEGRITY_MESSAGE = (
    "The stored file for this version is missing or does not match its recorded "
    "hash. Nothing was issued."
)


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
    path = tmp_path / "report-snapshots.sqlite3"
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
def fake_pdf(monkeypatch):
    from app.routers import reports

    rendered: list[bytes] = []

    def _fake(*_args, **_kwargs):
        content = f"%PDF-1.4\n% fake gap report {len(rendered) + 1}\n".encode()
        rendered.append(content)
        return content

    monkeypatch.setattr(reports, "generate_pdf", _fake)
    return rendered


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


def _run_one(db, gate, monkeypatch, *, item=None, client_name="Acme Corp", approved=True):
    assessment = _seed(db, client_name=client_name)
    _stub_single(monkeypatch, [item or _item(REQS[0])])
    gate.trigger_analysis(assessment.id, db)
    conclusion = db.query(Conclusion).filter_by(assessment_id=assessment.id).one()
    if approved:
        _direct_decision(db, conclusion, "approved")
        approved_report.record_release(db, assessment, actor="consultant:Priya")
        db.commit()
    return assessment, conclusion


def _direct_decision(db, conclusion, action, *, actor="consultant:Priya"):
    conclusion.version += 1
    db.add(
        ConclusionRevision(
            conclusion_id=conclusion.id,
            actor=actor,
            action=action,
            previous_outcome=conclusion.outcome,
            previous_rationale=conclusion.rationale,
            citations_json="[]",
            created_at=datetime.now(timezone.utc),
        )
    )
    db.commit()


def _generate(http, assessment_id, snapshot_type="gap_report", reviewer="Priya"):
    return http.post(
        f"/api/assessments/{assessment_id}/snapshots",
        data={"type": snapshot_type, "reviewer_name": reviewer},
    )


def _issue(http, assessment_id, snapshot_id, reviewer="Priya"):
    return http.post(
        f"/api/assessments/{assessment_id}/snapshots/{snapshot_id}/issue",
        data={"reviewer_name": reviewer},
    )


def _approve(http, assessment, conclusion, reviewer="Priya"):
    return http.post(
        f"/api/assessments/{assessment.id}/conclusions/{conclusion.id}/approve",
        data={"expected_version": conclusion.version, "reviewer_name": reviewer},
    )


def _events(db, snapshot_id, action=None):
    query = db.query(AuditEvent).filter_by(
        entity_type="report_snapshot", entity_id=snapshot_id
    )
    if action is not None:
        query = query.filter_by(action=action)
    return query.order_by(text("audit_events.rowid")).all()


def _snapshot_objects(db, assessment_id):
    return (
        db.query(ReportSnapshot)
        .filter_by(assessment_id=assessment_id)
        .order_by(text("report_snapshots.rowid"))
        .all()
    )


def _state(db, upload_root):
    rows = db.execute(
        text(
            "SELECT id, is_issued, storage_path, generated_at "
            "FROM report_snapshots ORDER BY rowid"
        )
    ).all()
    audit_count = db.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()
    root = upload_root / "reports"
    files = sorted(str(path.relative_to(upload_root)) for path in root.rglob("*") if path.is_file()) if root.exists() else []
    return (len(rows), audit_count, rows, files)


def _generated_meta(db, snapshot_id):
    (event_row,) = _events(db, snapshot_id, report_snapshots.GENERATED_ACTION)
    return json.loads(event_row.metadata_json)


def test_generate_issue_regenerate_preserves_the_issued_artifact(
    db, http, gate, monkeypatch, fake_pdf, upload_root
):
    """Scenario 1: generate, issue and regenerate without replacing v1."""
    assessment, conclusion = _run_one(db, gate, monkeypatch)

    first_response = _generate(http, assessment.id)
    assert first_response.status_code == 200
    assert first_response.headers["HX-Redirect"] == f"/assessments/{assessment.id}/snapshots"
    assert first_response.json()["is_issued"] is False
    first = db.get(ReportSnapshot, first_response.json()["snapshot_id"])
    assert (first.type, first.format, first.is_issued, first.engagement_id) == (
        "gap_report",
        "pdf",
        False,
        assessment.engagement_id,
    )
    assert first.storage_path == f"reports/assessments/{assessment.id}/{first.id}.pdf"
    first_path = upload_root / first.storage_path
    assert first_path.read_bytes() == fake_pdf[0]

    assert _issue(http, assessment.id, first.id).status_code == 200
    db.expire_all()
    assert db.get(ReportSnapshot, first.id).is_issued is True
    first_hash = _generated_meta(db, first.id)["sha256"]

    second_response = _generate(http, assessment.id)
    assert second_response.status_code == 200
    rows = _snapshot_objects(db, assessment.id)
    assert len(rows) == 2
    assert rows[0].is_issued is True and rows[1].is_issued is False
    assert rows[0].storage_path != rows[1].storage_path
    assert first_path.read_bytes() == fake_pdf[0]
    assert (upload_root / rows[1].storage_path).read_bytes() == fake_pdf[1]
    assert _generated_meta(db, first.id)["sha256"] == first_hash == hashlib.sha256(fake_pdf[0]).hexdigest()

    downloaded = http.get(f"/api/assessments/{assessment.id}/snapshots/{first.id}/file")
    assert downloaded.status_code == 200
    assert downloaded.content == fake_pdf[0]
    assert downloaded.headers["content-type"] == "application/pdf"
    assert downloaded.headers["X-Snapshot-Sha256"] == first_hash


def test_regeneration_keeps_drafts_and_only_newest_can_issue(
    db, http, gate, monkeypatch, fake_pdf, upload_root
):
    """Scenario 2: superseded drafts remain immutable and cannot issue."""
    assessment, _conclusion = _run_one(db, gate, monkeypatch)
    ids = [_generate(http, assessment.id).json()["snapshot_id"] for _ in range(3)]
    rows = report_snapshots.snapshot_rows(db, assessment)["gap_report"]
    assert [row.state for row in rows] == ["draft", "superseded_draft", "superseded_draft"]
    assert [row.sequence for row in rows] == [3, 2, 1]

    before = _state(db, upload_root)
    refused = _issue(http, assessment.id, ids[0])
    assert refused.status_code == 409
    assert unquote(refused.headers["X-Toast-Message"]) == (
        "A newer version of this report exists. Issue the newest version, or generate a new one."
    )
    assert _state(db, upload_root) == before
    assert _issue(http, assessment.id, ids[2]).status_code == 200

    fourth = _generate(http, assessment.id).json()["snapshot_id"]
    assert _issue(http, assessment.id, fourth).status_code == 200
    groups = report_snapshots.snapshot_rows(db, assessment)["gap_report"]
    issued = [row for row in groups if row.state == "issued"]
    assert {row.snapshot.id for row in issued} == {ids[2], fourth}
    assert [row.snapshot.id for row in issued if row.is_current_issue] == [fourth]


def test_issue_is_one_way_single_and_source_guarded(db, http, gate, monkeypatch, fake_pdf):
    """Scenario 3: issue is one-way and produces one release event."""
    assessment, _conclusion = _run_one(db, gate, monkeypatch)
    snapshot_id = _generate(http, assessment.id).json()["snapshot_id"]
    assert _issue(http, assessment.id, snapshot_id).status_code == 200
    refused = _issue(http, assessment.id, snapshot_id)
    assert refused.status_code == 409
    assert unquote(refused.headers["X-Toast-Message"]) == "This version is already issued."
    assert db.get(ReportSnapshot, snapshot_id).is_issued is True
    assert len(_events(db, snapshot_id, report_snapshots.ISSUED_ACTION)) == 1

    with pytest.raises(report_snapshots.SnapshotNotIssuable):
        report_snapshots.issue_snapshot(
            db, db.get(ReportSnapshot, snapshot_id), actor="consultant:Priya"
        )
    db.rollback()

    service_source = inspect.getsource(report_snapshots)
    router_source = (REPO_ROOT / "app/routers/snapshots.py").read_text()
    combined = service_source + router_source
    assert re.search(r"\.is_issued\s*=(?!=)", combined) is None
    assert re.search(r"SET\s+is_issued\s*=\s*0", combined, re.I) is None
    assert "update(ReportSnapshot" not in combined
    assert service_source.count(".open(") == 1
    assert '.open("xb")' in service_source
    for forbidden in ("write_bytes(", "write_text(", '"wb"', "'wb'", '"ab"', "'ab'"):
        assert forbidden not in service_source
    assert "delete" not in combined.lower()
    assert service_source.count(".unlink(") == 1
    assert router_source.count(".unlink(") == 1
    assert ".commit(" not in service_source
    assert ".commit(" in router_source


def test_issued_snapshot_survives_conclusion_and_analysis_changes(
    db, http, gate, monkeypatch, fake_pdf, upload_root
):
    """Scenario 4: later source changes cannot alter an issued file."""
    assessment, conclusion = _run_one(db, gate, monkeypatch)
    first_id = _generate(http, assessment.id).json()["snapshot_id"]
    assert _issue(http, assessment.id, first_id).status_code == 200
    first_meta = _generated_meta(db, first_id)
    first_bytes = (upload_root / db.get(ReportSnapshot, first_id).storage_path).read_bytes()

    _direct_decision(db, conclusion, "reopened")
    _direct_decision(db, conclusion, "approved")
    approved_report.record_release(db, assessment, actor="consultant:Priya")
    db.commit()
    db.refresh(conclusion)
    _stub_single(monkeypatch, [_item(REQS[0], status="non_compliant", gap="Different gap")])
    gate.trigger_analysis(assessment.id, db)
    downloaded = http.get(f"/api/assessments/{assessment.id}/snapshots/{first_id}/file")
    assert downloaded.content == first_bytes
    assert hashlib.sha256(first_bytes).hexdigest() == first_meta["sha256"]
    assert report_snapshots.snapshot_rows(db, assessment)["gap_report"][0].source_changed is True

    second_id = _generate(http, assessment.id).json()["snapshot_id"]
    second_meta = _generated_meta(db, second_id)
    assert second_meta["source"]["conclusion_versions"] != first_meta["source"]["conclusion_versions"]
    assert second_meta["source"]["gap_report_id"] != first_meta["source"]["gap_report_id"]


def test_integrity_checks_refuse_tampered_or_missing_files(
    db, http, gate, monkeypatch, fake_pdf, upload_root
):
    """Scenario 5: reads and issues fail closed on file tampering or loss."""
    assessment, _conclusion = _run_one(db, gate, monkeypatch)
    first_id = _generate(http, assessment.id).json()["snapshot_id"]
    first = db.get(ReportSnapshot, first_id)
    (upload_root / first.storage_path).write_bytes(b"tampered")
    read = http.get(f"/api/assessments/{assessment.id}/snapshots/{first_id}/file")
    assert read.status_code == 500 and read.json()["detail"] == INTEGRITY_MESSAGE
    before = _state(db, upload_root)
    issue = _issue(http, assessment.id, first_id)
    assert issue.status_code == 500
    assert issue.json()["detail"] == INTEGRITY_MESSAGE
    assert _state(db, upload_root) == before
    assert db.get(ReportSnapshot, first_id).is_issued is False

    second_id = _generate(http, assessment.id).json()["snapshot_id"]
    second = db.get(ReportSnapshot, second_id)
    (upload_root / second.storage_path).unlink()
    missing = http.get(f"/api/assessments/{assessment.id}/snapshots/{second_id}/file")
    assert missing.status_code == 500 and missing.json()["detail"] == INTEGRITY_MESSAGE


def test_release_gate_applies_to_gap_generation_and_all_issues(
    db, http, gate, monkeypatch, fake_pdf, upload_root
):
    """Scenario 6: release approval gates PDFs and every issue operation."""
    assessment, _conclusion = _run_one(db, gate, monkeypatch, approved=False)
    before = _state(db, upload_root)
    refused = _generate(http, assessment.id)
    assert refused.status_code == 403
    assert unquote(refused.headers["X-Toast-Message"]) == (
        "Report not yet approved for release. Complete the review process first."
    )
    assert _state(db, upload_root) == before

    workpaper_response = _generate(http, assessment.id, "workpaper")
    assert workpaper_response.status_code == 200
    workpaper_id = workpaper_response.json()["snapshot_id"]
    before_issue = _state(db, upload_root)
    refused_issue = _issue(http, assessment.id, workpaper_id)
    assert refused_issue.status_code == 403
    assert _state(db, upload_root) == before_issue
    _direct_decision(db, db.query(Conclusion).filter_by(assessment_id=assessment.id).one(), "approved")
    approved_report.record_release(db, assessment, actor="consultant:Priya")
    db.commit()
    refused_after_release = _issue(http, assessment.id, workpaper_id)
    assert refused_after_release.status_code == 409
    assert refused_after_release.json()["detail"] == report_snapshots.SNAPSHOT_STALE_MESSAGE

    unanalysed = _seed(db, client_name="No Report")
    before_missing = _state(db, upload_root)
    missing = _generate(http, unanalysed.id)
    assert missing.status_code == 404
    assert missing.json()["detail"] == "No report found. Run analysis first."
    assert _state(db, upload_root) == before_missing


def test_workpaper_snapshot_matches_live_page_then_stays_frozen(
    db, http, gate, monkeypatch, upload_root
):
    """Scenario 7: workpaper HTML is the exact live render captured once."""
    assessment, conclusion = _run_one(db, gate, monkeypatch, approved=False)
    response = _generate(http, assessment.id, "workpaper")
    snapshot = db.get(ReportSnapshot, response.json()["snapshot_id"])
    assert snapshot.format == "html"
    assert snapshot.storage_path == f"reports/assessments/{assessment.id}/{snapshot.id}.html"
    frozen = (upload_root / snapshot.storage_path).read_bytes().decode("utf-8")
    assert frozen == http.get(f"/assessments/{assessment.id}/workpaper").text

    served = http.get(f"/api/assessments/{assessment.id}/snapshots/{snapshot.id}/file")
    assert served.headers["content-type"] == "text/html; charset=utf-8"
    assert "content-disposition" not in served.headers
    assert _approve(http, assessment, conclusion).status_code == 200
    live = http.get(f"/assessments/{assessment.id}/workpaper").text
    assert 'data-decision-state="approved"' in live
    assert (upload_root / snapshot.storage_path).read_bytes().decode("utf-8") == frozen
    assert 'data-decision-state="approved"' not in frozen


def test_audit_records_capture_exact_hash_manifest_and_actor(
    db, http, gate, monkeypatch, fake_pdf, upload_root
):
    """Scenario 8: generation and issue events hold exact provenance."""
    assessment, conclusion = _run_one(db, gate, monkeypatch)
    response = _generate(http, assessment.id)
    snapshot = db.get(ReportSnapshot, response.json()["snapshot_id"])
    generated = _events(db, snapshot.id, report_snapshots.GENERATED_ACTION)[0]
    metadata = json.loads(generated.metadata_json)
    assert set(metadata) == {
        "schema_version",
        "type",
        "format",
        "storage_path",
        "sha256",
        "size_bytes",
        "assessment_id",
        "engagement_id",
        "review_status",
        "source",
    }
    content = (upload_root / snapshot.storage_path).read_bytes()
    assert metadata["sha256"] == hashlib.sha256(content).hexdigest()
    assert metadata["size_bytes"] == len(content)
    assert metadata["storage_path"] == snapshot.storage_path
    conclusions = db.query(Conclusion).filter_by(assessment_id=assessment.id).order_by(Conclusion.id).all()
    assert metadata["source"]["conclusion_versions"] == [[row.id, row.version] for row in conclusions]
    assert metadata["source"]["gap_report_id"] == db.query(GapReport).filter_by(assessment_id=assessment.id).one().id
    assert generated.actor == "consultant:Priya"

    assert _issue(http, assessment.id, snapshot.id).status_code == 200
    issued_meta = json.loads(_events(db, snapshot.id, report_snapshots.ISSUED_ACTION)[0].metadata_json)
    assert set(issued_meta) == {"assessment_id", "engagement_id", "sha256", "type"}
    blank = _generate(http, assessment.id, "workpaper", reviewer="")
    blank_event = _events(db, blank.json()["snapshot_id"], report_snapshots.GENERATED_ACTION)[0]
    assert blank_event.actor == "consultant:Manager Review"


def test_validation_scoping_and_unknown_resources_write_nothing(
    db, http, gate, monkeypatch, fake_pdf, upload_root
):
    """Scenario 9: invalid types and cross-assessment ids are refused cleanly."""
    assessment, _conclusion = _run_one(db, gate, monkeypatch)
    for data, message in (
        ({}, "Choose a report type to generate."),
        ({"type": "bogus"}, "Unknown report type."),
        ({"type": "integrated_report"}, "Integrated engagement reports are not available yet."),
    ):
        before = _state(db, upload_root)
        response = http.post(f"/api/assessments/{assessment.id}/snapshots", data=data)
        assert response.status_code == 400
        assert response.json()["detail"] == message
        assert _state(db, upload_root) == before

    snapshot_id = _generate(http, assessment.id).json()["snapshot_id"]
    other = _seed(db, client_name="Other")
    unknown = "00000000-0000-0000-0000-000000000000"
    for method, url in (
        ("post", f"/api/assessments/{unknown}/snapshots"),
        ("post", f"/api/assessments/{unknown}/snapshots/{snapshot_id}/issue"),
        ("get", f"/api/assessments/{unknown}/snapshots/{snapshot_id}/file"),
        ("get", f"/assessments/{unknown}/snapshots"),
    ):
        before = _state(db, upload_root)
        response = (
            http.post(url, data={"type": "workpaper"})
            if method == "post"
            else http.get(url)
        )
        assert response.status_code == 404
        assert _state(db, upload_root) == before

    for snapshot_value in (snapshot_id, unknown):
        before = _state(db, upload_root)
        assert _issue(http, other.id, snapshot_value).status_code == 404
        assert http.get(f"/api/assessments/{other.id}/snapshots/{snapshot_value}/file").status_code == 404
        assert _state(db, upload_root) == before


def test_failure_cleanup_removes_uncommitted_files(
    db, http, gate, monkeypatch, fake_pdf, upload_root
):
    """Scenario 10: service and commit failures leave no orphan row or file."""
    assessment, _conclusion = _run_one(db, gate, monkeypatch)
    original_record = report_snapshots._record_event

    def _fail_record(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(report_snapshots, "_record_event", _fail_record)
    with pytest.raises(RuntimeError, match="boom"):
        _generate(http, assessment.id)
    db.rollback()
    assert db.query(ReportSnapshot).count() == 0
    reports_root = upload_root / "reports"
    assert not reports_root.exists() or not list(reports_root.rglob("*.*"))
    monkeypatch.setattr(report_snapshots, "_record_event", original_record)

    original_commit = db.commit
    calls = 0

    def _fail_once():
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("commit failed")
        return original_commit()

    monkeypatch.setattr(db, "commit", _fail_once)
    failed = _generate(http, assessment.id)
    assert failed.status_code == 500
    assert failed.json()["detail"] == "The report version could not be saved. Try again."
    db.rollback()
    assert db.query(ReportSnapshot).count() == 0
    assert not reports_root.exists() or not list(reports_root.rglob("*.*"))

    with pytest.raises(ValueError):
        report_snapshots.storage_path_for(snapshot_id=_new_id(), fmt="pdf")
    path = "reports/assessments/a/b.pdf"
    report_snapshots._write_file(path, b"first")
    with pytest.raises(FileExistsError):
        report_snapshots._write_file(path, b"second")
    assert (upload_root / path).read_bytes() == b"first"


def _insert_integrated(db, engagement_id, content, actor="consultant:Priya"):
    snapshot_id = _new_id()
    storage_path = report_snapshots.storage_path_for(
        snapshot_id=snapshot_id, fmt="pdf", engagement_id=engagement_id
    )
    report_snapshots._write_file(storage_path, content)
    snapshot = ReportSnapshot(
        id=snapshot_id,
        assessment_id=None,
        engagement_id=engagement_id,
        type="integrated_report",
        format="pdf",
        storage_path=storage_path,
        is_issued=False,
    )
    db.add(snapshot)
    report_snapshots._record_event(
        db,
        actor=actor,
        action=report_snapshots.GENERATED_ACTION,
        snapshot_id=snapshot_id,
        metadata={
            "schema_version": 1,
            "type": "integrated_report",
            "format": "pdf",
            "storage_path": storage_path,
            "sha256": hashlib.sha256(content).hexdigest(),
            "size_bytes": len(content),
            "assessment_id": None,
            "engagement_id": engagement_id,
            "review_status": None,
            "source": {"gap_report_id": None, "conclusion_versions": []},
        },
    )
    db.commit()
    return snapshot


def test_integrated_report_scope_is_pinned_in_issue_statement(db):
    """Scenario 11: integrated versions scope by engagement independently."""
    first_client = Client(name="Integrated A", industry="Tech", size="medium")
    second_client = Client(name="Integrated B", industry="Tech", size="medium")
    db.add_all([first_client, second_client])
    db.flush()
    first_engagement = Engagement(
        client_id=first_client.id, name="First", status="active"
    )
    second_engagement = Engagement(
        client_id=second_client.id, name="Second", status="active"
    )
    db.add_all([first_engagement, second_engagement])
    db.flush()
    older = _insert_integrated(db, first_engagement.id, b"older")
    newer = _insert_integrated(db, first_engagement.id, b"newer")
    independent = _insert_integrated(db, second_engagement.id, b"other")

    with pytest.raises(report_snapshots.SnapshotNotIssuable):
        report_snapshots.issue_snapshot(db, older, actor="consultant:Priya")
    db.rollback()
    assert report_snapshots.issue_snapshot(db, newer, actor="consultant:Priya").is_issued
    db.commit()
    assert report_snapshots.issue_snapshot(db, independent, actor="consultant:Priya").is_issued
    db.commit()
    assert report_snapshots.storage_path_for(
        snapshot_id=older.id, fmt="pdf", engagement_id=first_engagement.id
    ) == f"reports/engagements/{first_engagement.id}/{older.id}.pdf"


def test_snapshot_route_and_source_guards_are_exact():
    """Scenario 12: only the four specified append-only routes exist."""
    routes = {
        (method, route.path)
        for route in app.routes
        if "/snapshots" in getattr(route, "path", "")
        for method in getattr(route, "methods", set())
    }
    assert routes == {
        ("GET", "/assessments/{assessment_id}/snapshots"),
        ("POST", "/api/assessments/{assessment_id}/snapshots"),
        ("POST", "/api/assessments/{assessment_id}/snapshots/{snapshot_id}/issue"),
        ("GET", "/api/assessments/{assessment_id}/snapshots/{snapshot_id}/file"),
    }
    assert all(
        forbidden not in path.lower()
        for _method, path in routes
        for forbidden in ("delete", "unissue", "withdraw", "replace")
    )
    assert ".commit(" not in inspect.getsource(web.snapshots_page)


def test_report_versions_page_renders_states_controls_and_escaped_content(
    db, http, gate, monkeypatch, fake_pdf
):
    """Scenario 13: page groups versions and exposes only valid issue controls."""
    assessment, conclusion = _run_one(db, gate, monkeypatch)
    empty = http.get(f"/assessments/{assessment.id}/snapshots")
    assert empty.status_code == 200
    assert empty.text.count("data-snapshot-type=") == 2
    assert empty.text.count("No versions generated yet.") == 2

    ids = [_generate(http, assessment.id).json()["snapshot_id"] for _ in range(3)]
    assert _issue(http, assessment.id, ids[2]).status_code == 200
    fourth = _generate(http, assessment.id).json()["snapshot_id"]
    assert _issue(http, assessment.id, fourth).status_code == 200
    page = http.get(f"/assessments/{assessment.id}/snapshots").text
    assert page.count("data-snapshot-row") == 4
    assert page.count("data-issue-control") == 0
    assert "Issued (current)" in page and ">Issued<" in page
    assert "Draft (superseded)" in page
    for snapshot_id in ids + [fourth]:
        assert f"/snapshots/{snapshot_id}/file" in page
    assert "consultant:Priya" not in page and "Priya" in page

    newest = _generate(http, assessment.id).json()["snapshot_id"]
    page = http.get(f"/assessments/{assessment.id}/snapshots").text
    assert page.count("data-issue-control") == 1
    newest_row = re.search(
        rf'<tr[^>]+data-snapshot-id="{newest}".*?</tr>', page, re.S
    ).group()
    assert "data-issue-control" in newest_row

    _direct_decision(db, conclusion, "reopened")
    assessment.company_name = "<script>x</script>"
    db.commit()
    pending = http.get(f"/assessments/{assessment.id}/snapshots").text
    assert "Generating a gap report requires the report to be released." in pending
    assert "&lt;script&gt;x&lt;/script&gt;" in pending
    assert "<script>x</script>" not in pending


def test_live_routes_remain_unversioned_and_links_distinguish_them(
    db, http, gate, monkeypatch, fake_pdf, upload_root
):
    """Scenario 14: live PDF and workpaper still work without snapshot writes."""
    assessment, _conclusion = _run_one(db, gate, monkeypatch)
    before = _state(db, upload_root)
    pdf = http.get(f"/api/assessments/{assessment.id}/report/pdf")
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.content == fake_pdf[0]
    assert _state(db, upload_root) == before
    assert http.get(f"/assessments/{assessment.id}/workpaper").status_code == 200

    for relative in (
        "app/templates/pages/assessment.html",
        "app/templates/partials/analysis_complete.html",
        "app/templates/partials/report_summary.html",
    ):
        source = (REPO_ROOT / relative).read_text()
        assert '/snapshots"' in source
        assert "Live PDF" in source
        assert "Download PDF" not in source
        assert "PDF Report" not in source
