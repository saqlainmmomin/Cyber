"""TDD ("red") contract suite for P2-1, the Evidence service.

Written before the implementation. It pins the interface that
``tasks/handoffs/2026-09-23-p2-1-evidence-service.md`` specifies, and must turn
green WITHOUT edits to its assertions. Scenario numbers in the docstrings match
the handoff's "Test scenarios" section.

Modules under contract (none exist yet):

``app.services.evidence``
    Constants (``EVIDENCE_STATUSES``, ``VERSION_STATUSES``,
    ``EVIDENCE_TRANSITIONS``, ``VERSION_TRANSITIONS``, ``SCAN_REJECTED_MESSAGE``,
    ...), the ``EvidenceError`` hierarchy, the non-committing primitives
    (``receive_evidence``, ``receive_version``, ``release_from_quarantine``,
    ``transition_evidence``, ``map_evidence``, ``unmap_evidence``), the two
    committing orchestrators (``ingest_upload``, ``ingest_new_version``), and
    the readers (``analysis_documents``, ``evidence_panel_rows``,
    ``evidence_detail``, ``current_version``, ``verify_version``).
    ``extract_text`` and ``scan_blob`` are module globals patched here.

``scripts.migrate_documents_to_evidence``
    ``run_document_migration(session) -> DocumentMigrationStats`` and
    ``main(argv) -> int`` (backup-first, like ``scripts.migrate_legacy``).

Every service-dependent test resolves the module through ``svc()`` as its first
statement, so before implementation each fails with
``ModuleNotFoundError: No module named 'app.services.evidence'`` -- a failure
for the right reason, not a typo in this file.

Test-DB strategy: a real file-backed SQLite database built by
``alembic upgrade head`` with ``PRAGMA foreign_keys=ON`` on every connection
(same pattern as ``tests/test_migrate_legacy.py``), so FK constraints --
notably ``desk_review_findings.document_id -> assessment_documents.id`` -- are
genuinely enforced. ``settings.upload_dir`` is redirected to ``tmp_path`` for
every test so no blob is ever written into the repository.
"""

from __future__ import annotations

import hashlib
import importlib
import io
import json
import logging
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401 - register all ORM tables
from app.config import settings
from app.models.assessment import Assessment, AssessmentDocument
from app.models.audit_event import AuditEvent
from app.models.client import Client
from app.models.desk_review import DeskReviewFinding
from app.models.engagement import Engagement
from app.models.evidence import Evidence, EvidenceUse, EvidenceVersion

REPO_ROOT = Path(__file__).resolve().parents[1]
P2_1_REVISION = "7a3f1e2b9c80"
P1_2_REVISION = "5c7c75960f43"
SERVICE_MODULE = "app.services.evidence"
MIGRATION_MODULE = "scripts.migrate_documents_to_evidence"

EXTRACTION_FAILED = (
    "Could not extract text from this document. If it is a scanned PDF, "
    "try uploading it as a PNG or JPEG screenshot instead."
)
UNSUPPORTED = "Unsupported file type. Upload PDF, DOCX, PNG, JPG, JPEG, or WEBP files."
SCAN_REJECTED = "File failed the malware scan and was not released from quarantine."
ENGAGEMENT_REQUIRED = (
    "This assessment is not linked to an engagement. "
    "Run scripts/migrate_legacy.py before uploading evidence."
)
LEGACY_DELETE = (
    "Legacy document: run scripts/migrate_documents_to_evidence.py before archiving it."
)


def svc():
    """The service under contract. Import lazily so a missing module fails
    each test individually (FAILED), rather than erroring collection."""

    return importlib.import_module(SERVICE_MODULE)


def migration_script():
    return importlib.import_module(MIGRATION_MODULE)


def _service_or_none():
    try:
        return importlib.import_module(SERVICE_MODULE)
    except ModuleNotFoundError as exc:
        if exc.name != SERVICE_MODULE:
            raise
        return None


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="module", autouse=True)
def _register_frameworks():
    """``Assessment.selected_frameworks`` validates against the registry, which
    is otherwise populated only by the app's startup hook."""

    from app.main import _register_frameworks as register

    register()


@pytest.fixture(autouse=True)
def upload_root(tmp_path, monkeypatch) -> Path:
    root = tmp_path / "uploads"
    root.mkdir()
    monkeypatch.setattr(settings, "upload_dir", str(root))
    return root


def _alembic_config(db_path: Path) -> Config:
    config = Config(str(REPO_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return config


@pytest.fixture()
def db_path(tmp_path) -> Path:
    path = tmp_path / "evidence.sqlite3"
    command.upgrade(_alembic_config(path), "head")
    return path


@pytest.fixture()
def engine(db_path):
    eng = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})

    @event.listens_for(eng, "connect")
    def _enable_foreign_keys(dbapi_connection, _record):  # pragma: no cover
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    yield eng
    eng.dispose()


@pytest.fixture()
def db(engine):
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def http(db, db_path, monkeypatch):
    """TestClient sharing ``db``. The lifespan's ``alembic upgrade head`` is
    pointed at the same per-test database (see tests/integration/conftest.py)."""

    from app.database import get_db
    from app.main import app
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
def extractor(monkeypatch) -> list:
    """Replace ``app.services.evidence.extract_text`` with a deterministic fake
    (no pdfplumber, no vision LLM). Records every call."""

    calls: list[tuple[Path, str]] = []

    def _fake_extract(path, file_type):
        calls.append((Path(path), file_type))
        return f"Extracted text from {Path(path).name}"

    module = _service_or_none()
    if module is not None:
        monkeypatch.setattr(module, "extract_text", _fake_extract)
    return calls


# --------------------------------------------------------------------------- #
# Seed helpers
# --------------------------------------------------------------------------- #


def _seed_hierarchy(db, *, assessments=1, frameworks=("dpdpa",), client_name="Acme Corp"):
    client = Client(name=client_name, industry="Technology", size="medium")
    db.add(client)
    db.flush()
    engagement = Engagement(client_id=client.id, name=f"{client_name} gap", status="active")
    db.add(engagement)
    db.flush()
    created = []
    for _ in range(assessments):
        assessment = Assessment(
            company_name=client_name,
            industry="Technology",
            company_size="medium",
            selected_frameworks=json.dumps(list(frameworks)),
            engagement_id=engagement.id,
        )
        db.add(assessment)
        created.append(assessment)
    db.commit()
    return client, engagement, created


def _orphan_assessment(db, name="Legacy Co") -> Assessment:
    assessment = Assessment(
        company_name=name,
        industry="Technology",
        company_size="small",
        selected_frameworks=json.dumps(["dpdpa"]),
        engagement_id=None,
    )
    db.add(assessment)
    db.commit()
    return assessment


def _legacy_doc(
    db,
    assessment,
    *,
    filename="legacy-policy.pdf",
    file_path="/nonexistent/uploads/fake/deadbeef_legacy-policy.pdf",
    text_value="Legacy extracted policy text.",
    uploaded_at=None,
    category="privacy_policy",
) -> AssessmentDocument:
    doc = AssessmentDocument(
        assessment_id=assessment.id,
        filename=filename,
        file_path=file_path,
        file_type=filename.rsplit(".", 1)[-1],
        document_category=category,
        extracted_text=text_value,
    )
    if uploaded_at is not None:
        doc.uploaded_at = uploaded_at
    db.add(doc)
    db.commit()
    return doc


def _pdf(tag: str) -> bytes:
    return b"%PDF-1.4\n% CyberAssess test document " + tag.encode() + b"\n%%EOF\n"


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _upload(ev, db, assessment, content=None, filename="Privacy Policy.pdf", category="privacy_policy"):
    return ev.ingest_upload(
        db,
        assessment_id=assessment.id,
        filename=filename,
        content=_pdf("v1") if content is None else content,
        category=category,
    )


def _blob_files(upload_root: Path) -> list[Path]:
    root = upload_root / "evidence"
    if not root.exists():
        return []
    return sorted(p for p in root.rglob("*") if p.is_file())


def _audit_rows(db) -> list[tuple[str, str, str, dict]]:
    rows = db.execute(
        text("SELECT action, entity_type, entity_id, metadata_json FROM audit_events ORDER BY rowid")
    ).all()
    return [(a, t, i, json.loads(m) if m else {}) for a, t, i, m in rows]


def _versions(db, evidence_id) -> list[EvidenceVersion]:
    return (
        db.query(EvidenceVersion)
        .filter(EvidenceVersion.evidence_id == evidence_id)
        .order_by(EvidenceVersion.version_number)
        .all()
    )


def _counts(db) -> dict[str, int]:
    db.expire_all()
    return {
        "evidence": db.query(Evidence).count(),
        "evidence_versions": db.query(EvidenceVersion).count(),
        "evidence_uses": db.query(EvidenceUse).count(),
        "audit_events": db.query(AuditEvent).count(),
    }


# --------------------------------------------------------------------------- #
# 1-3. Upload, quarantine, hashing
# --------------------------------------------------------------------------- #


def test_upload_creates_evidence_and_first_version_with_correct_hash(db, upload_root, extractor):
    """Scenario 1."""
    ev = svc()
    _client, engagement, (assessment,) = _seed_hierarchy(db)
    content = _pdf("scenario-1")

    result = _upload(ev, db, assessment, content=content, filename="Privacy Policy.pdf")

    assert result.released is True
    db.expire_all()
    evidence = db.query(Evidence).one()
    version = db.query(EvidenceVersion).one()
    expected_hash = _sha(content)

    assert result.evidence.id == evidence.id and result.version.id == version.id
    assert evidence.engagement_id == engagement.id
    assert evidence.assessment_id == assessment.id
    assert evidence.original_filename == "Privacy Policy.pdf"
    assert evidence.mime_type == "application/pdf"
    assert evidence.file_hash_sha256 == expected_hash
    assert len(evidence.file_hash_sha256) == 64
    assert evidence.file_size_bytes == len(content)
    assert evidence.status == "active"
    assert evidence.uploaded_by == "consultant"
    assert evidence.document_category == "privacy_policy"

    assert version.evidence_id == evidence.id
    assert version.version_number == 1
    assert version.status == "active"
    assert version.file_hash_sha256 == expected_hash
    assert version.file_size_bytes == len(content)
    assert version.original_filename == "Privacy Policy.pdf"
    assert version.mime_type == "application/pdf"
    assert version.storage_path == f"evidence/{engagement.id}/{evidence.id}/v1.pdf"
    assert version.extracted_text == "Extracted text from v1.pdf"

    # Evidence's own file columns are v1's, frozen.
    assert evidence.storage_path == version.storage_path

    blob = upload_root / version.storage_path
    assert blob.read_bytes() == content
    assert ev.blob_path(version.storage_path) == blob
    assert "Privacy" not in version.storage_path and "Policy" not in version.storage_path
    assert extractor == [(blob, "pdf")]

    assessment = db.get(Assessment, assessment.id)
    assert assessment.status == "documents_uploaded"


def test_upload_passes_through_quarantine_with_placeholder_warning_and_audit_trail(db, extractor, caplog):
    """Scenario 2."""
    ev = svc()
    _client, _engagement, (assessment,) = _seed_hierarchy(db)
    caplog.set_level(logging.WARNING, logger=SERVICE_MODULE)

    result = _upload(ev, db, assessment)

    assert any(
        "Malware scanning is not configured" in record.getMessage()
        for record in caplog.records
        if record.name == SERVICE_MODULE and record.levelno == logging.WARNING
    )
    rows = _audit_rows(db)
    assert [(action, etype) for action, etype, _id, _meta in rows] == [
        ("evidence.created", "evidence"),
        ("evidence_version.created", "evidence_version"),
        ("evidence_version.status_changed", "evidence_version"),
        ("evidence.status_changed", "evidence"),
    ]
    created, version_created, version_changed, evidence_changed = rows
    assert created[2] == result.evidence.id
    assert created[3]["sha256"] == result.evidence.file_hash_sha256
    assert created[3]["version_id"] == result.version.id
    assert version_created[2] == result.version.id
    assert version_created[3]["version_number"] == 1
    assert (version_changed[3]["from"], version_changed[3]["to"]) == ("quarantined", "active")
    assert (evidence_changed[3]["from"], evidence_changed[3]["to"]) == ("quarantined", "active")
    actors = [a for (a,) in db.execute(text("SELECT actor FROM audit_events ORDER BY rowid"))]
    assert actors == ["consultant", "consultant", ev.SCAN_ACTOR, ev.SCAN_ACTOR]
    assert ev.SCAN_ACTOR == "system:scan-placeholder"


def test_scan_rejection_commits_rejected_rows_without_extraction(db, extractor, monkeypatch):
    """Scenario 3 (service level)."""
    ev = svc()
    _client, _engagement, (assessment,) = _seed_hierarchy(db)
    monkeypatch.setattr(ev, "scan_blob", lambda path: False)

    result = _upload(ev, db, assessment)

    assert result.released is False
    db.expire_all()
    evidence = db.query(Evidence).one()
    version = db.query(EvidenceVersion).one()
    assert evidence.status == "rejected"
    assert version.status == "rejected"
    assert version.extracted_text is None
    assert extractor == []
    assert db.get(Assessment, assessment.id).status == "created"
    assert ev.analysis_documents(db, assessment.id) == []


def test_scan_rejection_over_json_compat_route_is_422(db, http, extractor, monkeypatch):
    """Scenario 3 (HTTP)."""
    ev = svc()
    _client, _engagement, (assessment,) = _seed_hierarchy(db)
    monkeypatch.setattr(ev, "scan_blob", lambda path: False)

    response = http.post(
        f"/api/assessments/{assessment.id}/documents",
        data={"category": "privacy_policy"},
        files={"file": ("policy.pdf", io.BytesIO(_pdf("rejected")), "application/pdf")},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == SCAN_REJECTED
    assert ev.SCAN_REJECTED_MESSAGE == SCAN_REJECTED
    db.expire_all()
    assert db.query(Evidence).one().status == "rejected"


# --------------------------------------------------------------------------- #
# 4-5. Versioning
# --------------------------------------------------------------------------- #


def test_new_version_supersedes_prior_version_on_release(db, upload_root, extractor):
    """Scenario 4."""
    ev = svc()
    _client, engagement, (assessment,) = _seed_hierarchy(db)
    v1_bytes, v2_bytes = _pdf("v1"), _pdf("v2")
    first = _upload(ev, db, assessment, content=v1_bytes, filename="policy-2025.pdf")

    second = ev.ingest_new_version(
        db,
        evidence_id=first.evidence.id,
        filename="policy-2026.pdf",
        content=v2_bytes,
        change_reason="Annual policy refresh",
    )

    assert second.released is True
    db.expire_all()
    v1, v2 = _versions(db, first.evidence.id)
    assert (v1.version_number, v1.status) == (1, "superseded")
    assert (v2.version_number, v2.status) == (2, "active")
    assert v2.file_hash_sha256 == _sha(v2_bytes) != v1.file_hash_sha256
    assert v2.storage_path == f"evidence/{engagement.id}/{first.evidence.id}/v2.pdf"
    assert v2.change_reason == "Annual policy refresh"
    assert v2.original_filename == "policy-2026.pdf"
    assert (upload_root / v1.storage_path).read_bytes() == v1_bytes  # never overwritten
    assert (upload_root / v2.storage_path).read_bytes() == v2_bytes

    evidence = db.get(Evidence, first.evidence.id)
    assert evidence.status == "active"
    assert evidence.file_hash_sha256 == _sha(v1_bytes)  # frozen v1 fields
    assert evidence.storage_path == v1.storage_path
    assert evidence.original_filename == "policy-2025.pdf"
    assert ev.current_version(db, evidence.id).id == v2.id

    docs = ev.analysis_documents(db, assessment.id)
    assert [(d["filename"], d["text"]) for d in docs] == [
        ("policy-2026.pdf", "Extracted text from v2.pdf")
    ]

    changes = [
        (entity_id, meta["from"], meta["to"])
        for action, _t, entity_id, meta in _audit_rows(db)
        if action == "evidence_version.status_changed"
    ]
    assert changes[-2:] == [(v1.id, "active", "superseded"), (v2.id, "quarantined", "active")]


def test_rejected_new_version_leaves_prior_version_active(db, extractor, monkeypatch):
    """Scenario 5."""
    ev = svc()
    _client, _engagement, (assessment,) = _seed_hierarchy(db)
    first = _upload(ev, db, assessment)
    monkeypatch.setattr(ev, "scan_blob", lambda path: False)

    second = ev.ingest_new_version(
        db,
        evidence_id=first.evidence.id,
        filename="policy.pdf",
        content=_pdf("infected"),
        change_reason="Replacement from client",
    )

    assert second.released is False
    db.expire_all()
    v1, v2 = _versions(db, first.evidence.id)
    assert v1.status == "active"
    assert v2.status == "rejected"
    assert v2.extracted_text is None
    assert db.get(Evidence, first.evidence.id).status == "active"
    assert [d["text"] for d in ev.analysis_documents(db, assessment.id)] == [
        "Extracted text from v1.pdf"
    ]


# --------------------------------------------------------------------------- #
# 6-7. State machine
# --------------------------------------------------------------------------- #

EXPECTED_EVIDENCE_TRANSITIONS = {
    ("quarantined", "active"): ("system", False),
    ("quarantined", "rejected"): ("system", False),
    ("active", "invalidated"): ("consultant", True),
    ("invalidated", "active"): ("consultant", True),
    ("active", "archived"): ("consultant", False),
    ("invalidated", "archived"): ("consultant", False),
    ("rejected", "archived"): ("consultant", False),
    ("archived", "active"): ("consultant", True),
}
EXPECTED_VERSION_TRANSITIONS = {
    ("quarantined", "active"),
    ("quarantined", "rejected"),
    ("active", "superseded"),
}


def test_state_machine_tables_are_exactly_the_designed_graph():
    """Scenario 6: the graph itself is the contract."""
    ev = svc()
    assert ev.EVIDENCE_STATUSES == ("quarantined", "active", "rejected", "invalidated", "archived")
    assert ev.VERSION_STATUSES == ("quarantined", "active", "superseded", "rejected")
    assert {
        pair: (rule.actor_kind, rule.requires_reason)
        for pair, rule in ev.EVIDENCE_TRANSITIONS.items()
    } == EXPECTED_EVIDENCE_TRANSITIONS
    assert set(ev.VERSION_TRANSITIONS) == EXPECTED_VERSION_TRANSITIONS
    assert ev.RELEVANCE_VALUES == ("primary", "supporting", "contextual")


def test_every_pair_outside_the_graph_is_an_invalid_transition():
    """Scenario 6: exhaustive -- including self-transitions."""
    ev = svc()
    for from_status in ev.EVIDENCE_STATUSES:
        for to_status in ev.EVIDENCE_STATUSES:
            if (from_status, to_status) in EXPECTED_EVIDENCE_TRANSITIONS:
                continue
            for actor_kind in ("consultant", "system"):
                with pytest.raises(ev.InvalidTransition) as info:
                    ev.check_evidence_transition(from_status, to_status, actor_kind=actor_kind)
                assert info.value.message == (
                    f"Invalid evidence transition: {from_status} -> {to_status}."
                )
                assert info.value.status_code == 409
    for from_status in ev.VERSION_STATUSES:
        for to_status in ev.VERSION_STATUSES:
            if (from_status, to_status) in EXPECTED_VERSION_TRANSITIONS:
                ev.check_version_transition(from_status, to_status)
                continue
            with pytest.raises(ev.InvalidTransition) as info:
                ev.check_version_transition(from_status, to_status)
            assert info.value.message == (
                f"Invalid evidence version transition: {from_status} -> {to_status}."
            )


def test_actor_kind_and_unknown_status_are_enforced():
    """Scenario 6: nobody can manually release a file from quarantine."""
    ev = svc()
    with pytest.raises(ev.TransitionNotPermitted) as info:
        ev.check_evidence_transition("quarantined", "active", actor_kind="consultant")
    assert info.value.status_code == 403
    assert info.value.message == (
        "Transition quarantined -> active is system-driven and cannot be requested directly."
    )
    with pytest.raises(ev.TransitionNotPermitted) as info:
        ev.check_evidence_transition("active", "archived", actor_kind="system")
    assert info.value.message == "Transition active -> archived requires a consultant."
    with pytest.raises(ev.EvidenceValidationError) as info:
        ev.check_evidence_transition("active", "purged", actor_kind="consultant")
    assert info.value.status_code == 422
    assert info.value.message == "Unknown evidence status 'purged'."

    rule = ev.check_evidence_transition("active", "invalidated", actor_kind="consultant")
    assert (rule.actor_kind, rule.requires_reason) == ("consultant", True)


def test_transition_service_rejects_without_side_effects(db, extractor):
    """Scenario 6: service refusals leave status and audit trail untouched."""
    ev = svc()
    _client, _engagement, (assessment,) = _seed_hierarchy(db)
    evidence_id = _upload(ev, db, assessment).evidence.id
    before = _counts(db)

    with pytest.raises(ev.InvalidTransition):
        ev.transition_evidence(db, evidence_id=evidence_id, to_status="quarantined", actor="consultant")
    db.rollback()
    with pytest.raises(ev.EvidenceValidationError) as info:
        ev.transition_evidence(
            db, evidence_id=evidence_id, to_status="invalidated", actor="consultant", reason="   "
        )
    assert info.value.message == "A reason is required for this transition."
    db.rollback()
    with pytest.raises(ev.EvidenceNotFound) as info:
        ev.transition_evidence(db, evidence_id="missing", to_status="archived", actor="consultant")
    assert info.value.message == "Evidence not found"
    db.rollback()

    assert db.get(Evidence, evidence_id).status == "active"
    assert _counts(db) == before


def test_consultant_transitions_drive_analysis_visibility(db, upload_root, extractor):
    """Scenario 7."""
    ev = svc()
    _client, _engagement, (assessment,) = _seed_hierarchy(db)
    result = _upload(ev, db, assessment)
    evidence_id = result.evidence.id
    blob = upload_root / result.version.storage_path

    def visible():
        return [d["id"] for d in ev.analysis_documents(db, assessment.id)]

    def panel():
        return [row["id"] for row in ev.evidence_panel_rows(db, assessment.id)]

    ev.transition_evidence(
        db, evidence_id=evidence_id, to_status="invalidated", actor="consultant", reason="Draft, not the approved policy"
    )
    db.commit()
    assert visible() == []
    assert panel() == [evidence_id]  # still listed, with its status

    ev.transition_evidence(
        db, evidence_id=evidence_id, to_status="active", actor="consultant", reason="Confirmed as approved version"
    )
    db.commit()
    assert visible() == [evidence_id]

    ev.transition_evidence(db, evidence_id=evidence_id, to_status="archived", actor="consultant")
    db.commit()
    assert visible() == []
    assert panel() == []
    db.expire_all()
    assert db.get(Evidence, evidence_id).status == "archived"
    assert len(_versions(db, evidence_id)) == 1
    assert blob.exists()  # soft delete: blob retained (D11)

    ev.transition_evidence(
        db, evidence_id=evidence_id, to_status="active", actor="consultant", reason="Archived in error"
    )
    db.commit()
    assert visible() == [evidence_id]

    changes = [
        (meta["from"], meta["to"], meta["reason"])
        for action, _t, _id, meta in _audit_rows(db)
        if action == "evidence.status_changed"
    ]
    assert changes[1:] == [
        ("active", "invalidated", "Draft, not the approved policy"),
        ("invalidated", "active", "Confirmed as approved version"),
        ("active", "archived", None),
        ("archived", "active", "Archived in error"),
    ]


def test_restore_requires_an_active_version(db, extractor, monkeypatch):
    """Scenario 7: rejected -> archived -> active is refused."""
    ev = svc()
    _client, _engagement, (assessment,) = _seed_hierarchy(db)
    monkeypatch.setattr(ev, "scan_blob", lambda path: False)
    evidence_id = _upload(ev, db, assessment).evidence.id

    ev.transition_evidence(db, evidence_id=evidence_id, to_status="archived", actor="consultant")
    db.commit()
    with pytest.raises(ev.InvalidTransition) as info:
        ev.transition_evidence(
            db, evidence_id=evidence_id, to_status="active", actor="consultant", reason="Restore"
        )
    assert info.value.message == "Evidence has no active version to restore."
    db.rollback()
    assert db.get(Evidence, evidence_id).status == "archived"


# --------------------------------------------------------------------------- #
# 8. Duplicates
# --------------------------------------------------------------------------- #


def test_duplicate_upload_rules(db, upload_root, extractor):
    """Scenario 8: refuse within scope, allow across assessments / after archive."""
    ev = svc()
    _client, _engagement, (first_assessment, second_assessment) = _seed_hierarchy(db, assessments=2)
    content = _pdf("same-bytes")
    original = _upload(ev, db, first_assessment, content=content, filename="Consent Form.pdf")
    before_counts, before_blobs = _counts(db), _blob_files(upload_root)

    with pytest.raises(ev.DuplicateEvidence) as info:
        _upload(ev, db, first_assessment, content=content, filename="consent-copy.pdf")
    assert info.value.status_code == 409
    assert info.value.existing_evidence_id == original.evidence.id
    assert info.value.message == (
        "This file is identical to 'Consent Form.pdf' already in this engagement's evidence."
    )
    assert _counts(db) == before_counts
    assert _blob_files(upload_root) == before_blobs

    # Different assessment in the same engagement: a separate receipt.
    other = _upload(ev, db, second_assessment, content=content, filename="Consent Form.pdf")
    assert other.evidence.id != original.evidence.id

    # After archiving, the same bytes may be uploaded again.
    ev.transition_evidence(db, evidence_id=original.evidence.id, to_status="archived", actor="consultant")
    db.commit()
    again = _upload(ev, db, first_assessment, content=content, filename="Consent Form.pdf")
    assert again.released is True
    assert db.query(Evidence).count() == 3


def test_duplicate_version_rules(db, extractor):
    """Scenario 8: identical to current -> refused; revert to superseded -> allowed."""
    ev = svc()
    _client, _engagement, (assessment,) = _seed_hierarchy(db)
    v1_bytes, v2_bytes = _pdf("v1"), _pdf("v2")
    evidence_id = _upload(ev, db, assessment, content=v1_bytes).evidence.id
    ev.ingest_new_version(db, evidence_id=evidence_id, filename="p.pdf", content=v2_bytes, change_reason="Update")

    with pytest.raises(ev.DuplicateEvidence) as info:
        ev.ingest_new_version(db, evidence_id=evidence_id, filename="p.pdf", content=v2_bytes, change_reason="Again")
    assert info.value.message == "This file is identical to the current version (v2)."

    reverted = ev.ingest_new_version(
        db, evidence_id=evidence_id, filename="p.pdf", content=v1_bytes, change_reason="Revert to 2025 wording"
    )
    assert reverted.version.version_number == 3
    db.expire_all()
    assert [v.status for v in _versions(db, evidence_id)] == ["superseded", "superseded", "active"]


# --------------------------------------------------------------------------- #
# 9. EvidenceUse mapping
# --------------------------------------------------------------------------- #


def test_evidence_use_mapping_validation_and_audit(db, extractor):
    """Scenario 9."""
    ev = svc()
    _client, _engagement, (assessment,) = _seed_hierarchy(db, frameworks=("dpdpa", "iso27001"))
    evidence_id = _upload(ev, db, assessment).evidence.id

    use = ev.map_evidence(
        db,
        evidence_id=evidence_id,
        assessment_id=assessment.id,
        framework_id="dpdpa",
        requirement_id="CH2.CONSENT.1",
        relevance="primary",
        actor="consultant",
    )
    db.commit()
    db.expire_all()
    stored = db.query(EvidenceUse).one()
    assert stored.id == use.id
    assert (stored.evidence_id, stored.assessment_id, stored.framework_id, stored.requirement_id, stored.relevance) == (
        evidence_id, assessment.id, "dpdpa", "CH2.CONSENT.1", "primary",
    )
    action, entity_type, entity_id, meta = _audit_rows(db)[-1]
    assert (action, entity_type, entity_id) == ("evidence_use.created", "evidence_use", use.id)
    assert meta == {
        "assessment_id": assessment.id,
        "evidence_id": evidence_id,
        "framework_id": "dpdpa",
        "relevance": "primary",
        "requirement_id": "CH2.CONSENT.1",
    }

    def attempt(**overrides):
        kwargs = dict(
            evidence_id=evidence_id,
            assessment_id=assessment.id,
            framework_id="iso27001",
            requirement_id="ISO.A5.1",
            relevance="supporting",
            actor="consultant",
        )
        kwargs.update(overrides)
        try:
            return ev.map_evidence(db, **kwargs)
        finally:
            db.rollback()

    with pytest.raises(ev.DuplicateMapping) as info:
        attempt(framework_id="dpdpa", requirement_id="CH2.CONSENT.1", relevance="supporting")
    assert info.value.message == "This evidence is already mapped to that requirement."
    with pytest.raises(ev.EvidenceValidationError) as info:
        attempt(framework_id="nist_csf", requirement_id="NIST.GV.OC.01")
    assert info.value.message == "Framework 'nist_csf' is not selected for this assessment."
    with pytest.raises(ev.EvidenceValidationError) as info:
        attempt(requirement_id="ISO.NOPE.99")
    assert info.value.message == "Unknown requirement 'ISO.NOPE.99' for framework 'iso27001'."
    with pytest.raises(ev.EvidenceValidationError) as info:
        attempt(relevance="critical")
    assert info.value.message == "Relevance must be one of: primary, supporting, contextual."
    with pytest.raises(ev.EvidenceNotFound) as info:
        attempt(assessment_id="missing")
    assert info.value.message == "Assessment not found"

    _other_client, _other_engagement, (foreign_assessment,) = _seed_hierarchy(
        db, client_name="Other Client", frameworks=("iso27001",)
    )
    with pytest.raises(ev.EvidenceValidationError) as info:
        attempt(assessment_id=foreign_assessment.id)
    assert info.value.message == "Evidence and assessment belong to different engagements."

    ev.transition_evidence(
        db, evidence_id=evidence_id, to_status="invalidated", actor="consultant", reason="Superseded by client"
    )
    db.commit()
    with pytest.raises(ev.EvidenceConflict) as info:
        attempt()
    assert info.value.status_code == 409
    assert info.value.message == "Only active evidence can be mapped to a requirement."
    assert db.query(EvidenceUse).count() == 1


def test_mapped_evidence_feeds_other_assessment_and_unmap_removes_it(db, extractor):
    """Scenario 9: the D-P2-1-A membership rule's OR-clause."""
    ev = svc()
    _client, _engagement, (origin, other) = _seed_hierarchy(db, assessments=2)
    evidence_id = _upload(ev, db, origin).evidence.id
    assert ev.analysis_documents(db, other.id) == []

    use = ev.map_evidence(
        db,
        evidence_id=evidence_id,
        assessment_id=other.id,
        framework_id="dpdpa",
        requirement_id="CH2.CONSENT.1",
        relevance="supporting",
        actor="consultant",
    )
    db.commit()

    assert [d["id"] for d in ev.analysis_documents(db, other.id)] == [evidence_id]
    (row,) = ev.evidence_panel_rows(db, other.id)
    assert row["mapped_in"] is True
    assert row["can_archive"] is False and row["can_add_version"] is False
    (origin_row,) = ev.evidence_panel_rows(db, origin.id)
    assert origin_row["mapped_in"] is False
    assert origin_row["can_archive"] is True and origin_row["can_add_version"] is True

    ev.unmap_evidence(db, evidence_id=evidence_id, use_id=use.id, actor="consultant")
    db.commit()
    assert ev.analysis_documents(db, other.id) == []
    assert db.query(EvidenceUse).count() == 0
    assert _audit_rows(db)[-1][0] == "evidence_use.deleted"
    with pytest.raises(ev.EvidenceNotFound) as info:
        ev.unmap_evidence(db, evidence_id=evidence_id, use_id=use.id, actor="consultant")
    assert info.value.message == "Evidence use not found"


# --------------------------------------------------------------------------- #
# 10-11. Readers and the pipeline
# --------------------------------------------------------------------------- #

ANALYSIS_DOCUMENT_KEYS = {"id", "filename", "category", "text", "legacy_document_id", "source"}


def test_analysis_documents_shape_order_and_legacy_fallback(db, extractor):
    """Scenario 10."""
    ev = svc()
    _client, _engagement, (assessment,) = _seed_hierarchy(db)
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    newer_legacy = _legacy_doc(db, assessment, filename="b.pdf", text_value="B text", uploaded_at=base + timedelta(days=1))
    older_legacy = _legacy_doc(db, assessment, filename="a.pdf", text_value="A text", uploaded_at=base, category="dpia")
    evidence_id = _upload(ev, db, assessment, category=None).evidence.id

    docs = ev.analysis_documents(db, assessment.id)

    assert all(set(d) == ANALYSIS_DOCUMENT_KEYS for d in docs)
    assert [d["source"] for d in docs] == ["evidence", "legacy", "legacy"]
    evidence_doc, first_legacy, second_legacy = docs
    assert evidence_doc == {
        "id": evidence_id,
        "filename": "Privacy Policy.pdf",
        "category": "other",
        "text": "Extracted text from v1.pdf",
        "legacy_document_id": None,
        "source": "evidence",
    }
    assert first_legacy == {
        "id": older_legacy.id,
        "filename": "a.pdf",
        "category": "dpia",
        "text": "A text",
        "legacy_document_id": older_legacy.id,
        "source": "legacy",
    }
    assert second_legacy["id"] == newer_legacy.id


def test_migrated_but_archived_legacy_document_is_not_resurrected(db, extractor):
    """Scenario 10: a legacy row is hidden once ANY Evidence shares its id."""
    ev = svc()
    _client, engagement, (assessment,) = _seed_hierarchy(db)
    doc = _legacy_doc(db, assessment)
    evidence, version = ev.receive_evidence(
        db,
        evidence_id=doc.id,
        engagement_id=engagement.id,
        assessment_id=assessment.id,
        filename=doc.filename,
        content=doc.extracted_text.encode(),
        file_type="txt",
        category=doc.document_category,
        uploaded_by="migration:assessment_documents",
        actor="system:migration",
        allow_duplicate=True,
    )
    ev.release_from_quarantine(db, version_id=version.id, actor="system:migration")
    version.extracted_text = doc.extracted_text
    db.commit()

    (migrated,) = ev.analysis_documents(db, assessment.id)
    assert migrated["source"] == "evidence"
    assert migrated["legacy_document_id"] == doc.id  # FK-safe for desk review

    ev.transition_evidence(db, evidence_id=doc.id, to_status="archived", actor="consultant")
    db.commit()
    assert ev.analysis_documents(db, assessment.id) == []
    assert ev.evidence_panel_rows(db, assessment.id) == []


def test_analysis_documents_query_budget(db, engine, extractor):
    """Scenario 10: <= 4 statements regardless of row count."""
    ev = svc()
    _client, _engagement, (assessment,) = _seed_hierarchy(db)
    for tag in ("one", "two", "three"):
        _upload(ev, db, assessment, content=_pdf(tag), filename=f"{tag}.pdf")
    _legacy_doc(db, assessment, filename="l1.pdf")
    _legacy_doc(db, assessment, filename="l2.pdf")
    db.expire_all()

    statements: list[str] = []

    def _count(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    event.listen(engine, "before_cursor_execute", _count)
    try:
        docs = ev.analysis_documents(db, assessment.id)
    finally:
        event.remove(engine, "before_cursor_execute", _count)

    assert len(docs) == 5
    assert len(statements) <= 4, statements


def test_desk_review_reads_evidence_and_stays_fk_valid(db, extractor, monkeypatch):
    """Scenario 11: the historical dict shape reaches the LLM seam, and
    DeskReviewFinding.document_id only ever holds assessment_documents ids."""
    ev = svc()
    import app.services.desk_review as desk_review

    _client, _engagement, (assessment,) = _seed_hierarchy(db)
    legacy = _legacy_doc(db, assessment, filename="legacy.pdf", text_value="Legacy text")
    evidence_id = _upload(ev, db, assessment, filename="new-policy.pdf").evidence.id
    seen: dict = {}

    def _fake_desk_review(documents, company_name, industry):
        seen["documents"] = documents
        return {
            "evidence_map": {
                "CH2.CONSENT.1": [
                    {"document": d["filename"], "quote": "q", "location": "p1"} for d in documents
                ]
            },
            "absence_findings": [],
            "signal_flags": [],
            "document_catalog": [],
            "coverage_summary": {},
        }

    monkeypatch.setattr(desk_review, "_call_claude_desk_review", _fake_desk_review)
    summary = desk_review.run_desk_review(assessment.id, db)

    assert summary.status == "completed", summary.error_message
    assert [set(d) for d in seen["documents"]] == [{"id", "filename", "category", "text"}] * 2
    assert {d["filename"] for d in seen["documents"]} == {"new-policy.pdf", "legacy.pdf"}
    assert {d["id"] for d in seen["documents"]} == {evidence_id, legacy.id}
    db.expire_all()
    links = {
        f.source_location + ":" + str(f.document_id)
        for f in db.query(DeskReviewFinding).filter(DeskReviewFinding.finding_type == "evidence")
    }
    assert links == {"p1:None", f"p1:{legacy.id}"}


# --------------------------------------------------------------------------- #
# 12-13. Refusals that must write nothing
# --------------------------------------------------------------------------- #


def test_upload_to_unmigrated_assessment_is_refused(db, upload_root, extractor):
    """Scenario 12."""
    ev = svc()
    orphan = _orphan_assessment(db)

    with pytest.raises(ev.EngagementRequired) as info:
        _upload(ev, db, orphan)
    assert info.value.status_code == 409
    assert info.value.message == ENGAGEMENT_REQUIRED
    assert _counts(db) == {"evidence": 0, "evidence_versions": 0, "evidence_uses": 0, "audit_events": 0}
    assert _blob_files(upload_root) == []

    with pytest.raises(ev.EvidenceNotFound) as info:
        ev.ingest_upload(db, assessment_id="missing", filename="a.pdf", content=_pdf("x"), category=None)
    assert info.value.message == "Assessment not found"


def test_unmigrated_assessment_upload_over_http_is_409(db, http, extractor):
    """Scenario 12 (HTTP)."""
    svc()
    orphan = _orphan_assessment(db)
    response = http.post(
        f"/api/assessments/{orphan.id}/documents",
        data={"category": "privacy_policy"},
        files={"file": ("policy.pdf", io.BytesIO(_pdf("orphan")), "application/pdf")},
    )
    assert response.status_code == 409
    assert response.json()["detail"] == ENGAGEMENT_REQUIRED


@pytest.mark.parametrize(
    ("filename", "content", "extracted", "error_name", "status_code", "message"),
    [
        ("notes.txt", b"plain text", "text", "UnsupportedFileType", 400, UNSUPPORTED),
        ("empty.pdf", b"", "text", "EvidenceValidationError", 422, "The uploaded file is empty."),
        ("scanned.pdf", _pdf("scan"), "   \n ", "EvidenceValidationError", 422, EXTRACTION_FAILED),
    ],
    ids=["unsupported-type", "empty-file", "empty-extraction"],
)
def test_upload_validation_failures_write_nothing(
    db, upload_root, monkeypatch, filename, content, extracted, error_name, status_code, message
):
    """Scenario 13."""
    ev = svc()
    monkeypatch.setattr(ev, "extract_text", lambda path, file_type: extracted)
    _client, _engagement, (assessment,) = _seed_hierarchy(db)

    with pytest.raises(getattr(ev, error_name)) as info:
        _upload(ev, db, assessment, content=content, filename=filename)

    assert info.value.status_code == status_code
    assert info.value.message == message
    assert isinstance(info.value, ev.EvidenceError)
    assert _counts(db) == {"evidence": 0, "evidence_versions": 0, "evidence_uses": 0, "audit_events": 0}
    assert _blob_files(upload_root) == []
    assert db.get(Assessment, assessment.id).status == "created"


def test_new_version_validation_order(db, upload_root, extractor):
    """Scenario 13: status -> reason -> type -> duplicate."""
    ev = svc()
    _client, _engagement, (assessment,) = _seed_hierarchy(db)
    content = _pdf("v1")
    evidence_id = _upload(ev, db, assessment, content=content).evidence.id
    blobs = _blob_files(upload_root)

    def attempt(**overrides):
        kwargs = dict(evidence_id=evidence_id, filename="p.pdf", content=_pdf("v2"), change_reason="Refresh")
        kwargs.update(overrides)
        return ev.ingest_new_version(db, **kwargs)

    with pytest.raises(ev.EvidenceValidationError) as info:
        attempt(change_reason="  ", filename="p.txt")
    assert info.value.message == "A change reason is required when uploading a new version."
    with pytest.raises(ev.UnsupportedFileType):
        attempt(filename="p.txt", content=content)
    with pytest.raises(ev.DuplicateEvidence):
        attempt(content=content)
    with pytest.raises(ev.EvidenceNotFound):
        attempt(evidence_id="missing")
    assert _blob_files(upload_root) == blobs

    ev.transition_evidence(db, evidence_id=evidence_id, to_status="archived", actor="consultant")
    db.commit()
    with pytest.raises(ev.InvalidTransition) as info:
        attempt(change_reason="  ")
    assert info.value.message == "Cannot add a version to evidence in status 'archived'."
    assert len(_versions(db, evidence_id)) == 1


def test_new_version_refused_while_a_version_is_quarantined(db, extractor):
    """Scenario 13: a pending quarantined version blocks further versions."""
    ev = svc()
    _client, _engagement, (assessment,) = _seed_hierarchy(db)
    evidence_id = _upload(ev, db, assessment).evidence.id
    ev.receive_version(
        db, evidence_id=evidence_id, filename="p.pdf", content=_pdf("pending"), change_reason="Pending", actor="consultant"
    )
    db.commit()

    with pytest.raises(ev.InvalidTransition) as info:
        ev.ingest_new_version(db, evidence_id=evidence_id, filename="p.pdf", content=_pdf("v3"), change_reason="Next")
    assert info.value.message == "A new version is already awaiting release from quarantine."
    (row,) = ev.evidence_panel_rows(db, assessment.id)
    assert row["can_add_version"] is False
    assert row["current_version_number"] == 1
    assert row["version_count"] == 2


# --------------------------------------------------------------------------- #
# 14-15. HTTP surfaces
# --------------------------------------------------------------------------- #


def test_json_compat_document_routes(db, http, upload_root, extractor):
    """Scenario 14 (JSON compat)."""
    svc()
    _client, _engagement, (assessment,) = _seed_hierarchy(db)
    legacy = _legacy_doc(db, assessment)
    base = f"/api/assessments/{assessment.id}/documents"

    created = http.post(
        base,
        data={"category": "privacy_policy"},
        files={"file": ("policy.pdf", io.BytesIO(_pdf("compat")), "application/pdf")},
    )
    assert created.status_code == 201, created.text
    body = created.json()
    db.expire_all()
    evidence = db.query(Evidence).one()
    assert body["id"] == evidence.id
    assert body["status"] == "active"
    assert body["assessment_id"] == assessment.id
    assert body["file_type"] == "pdf"
    assert body["document_category"] == "privacy_policy"
    assert body["text_length"] == len("Extracted text from v1.pdf")
    assert db.query(AssessmentDocument).count() == 1  # only the seeded legacy row

    listed = http.get(base)
    assert listed.status_code == 200
    statuses = {row["id"]: row["status"] for row in listed.json()}
    assert statuses == {evidence.id: "active", legacy.id: "legacy"}

    archived = http.delete(f"{base}/{evidence.id}")
    assert archived.status_code == 204
    db.expire_all()
    assert db.get(Evidence, evidence.id).status == "archived"
    assert len(_blob_files(upload_root)) == 1
    assert {row["id"] for row in http.get(base).json()} == {legacy.id}

    refused = http.delete(f"{base}/{legacy.id}")
    assert refused.status_code == 409
    assert refused.json()["detail"] == LEGACY_DELETE
    assert db.get(AssessmentDocument, legacy.id) is not None

    missing = http.delete(f"{base}/does-not-exist")
    assert missing.status_code == 404
    assert missing.json()["detail"] == "Document not found"


def test_json_compat_delete_refuses_mapped_in_evidence(db, http, extractor):
    """Scenario 14: only the originating assessment may archive."""
    ev = svc()
    _client, _engagement, (origin, other) = _seed_hierarchy(db, assessments=2)
    evidence_id = _upload(ev, db, origin).evidence.id
    ev.map_evidence(
        db, evidence_id=evidence_id, assessment_id=other.id, framework_id="dpdpa",
        requirement_id="CH2.CONSENT.1", relevance="contextual", actor="consultant",
    )
    db.commit()

    response = http.delete(f"/api/assessments/{other.id}/documents/{evidence_id}")
    assert response.status_code == 404
    db.expire_all()
    assert db.get(Evidence, evidence_id).status == "active"


def test_htmx_document_routes_and_evidence_page(db, http, extractor):
    """Scenario 14 (HTML)."""
    svc()
    client_row, engagement, (assessment,) = _seed_hierarchy(db)

    uploaded = http.post(
        f"/assessments/{assessment.id}/upload",
        data={"category": "privacy_policy"},
        files={"file": ("Privacy Policy.pdf", io.BytesIO(_pdf("htmx-v1")), "application/pdf")},
    )
    assert uploaded.status_code == 200
    assert "Privacy Policy.pdf" in uploaded.text
    db.expire_all()
    evidence = db.query(Evidence).one()
    assert db.query(AssessmentDocument).count() == 0

    versioned = http.post(
        f"/assessments/{assessment.id}/evidence/{evidence.id}/versions",
        data={"change_reason": "Client sent signed copy"},
        files={"file": ("Privacy Policy signed.pdf", io.BytesIO(_pdf("htmx-v2")), "application/pdf")},
    )
    assert versioned.status_code == 200
    db.expire_all()
    v1, v2 = _versions(db, evidence.id)
    assert (v1.status, v2.status) == ("superseded", "active")

    page = http.get(f"/evidence/{evidence.id}")
    assert page.status_code == 200
    assert v1.file_hash_sha256 in page.text and v2.file_hash_sha256 in page.text
    assert "Superseded" in page.text
    assert client_row.name in page.text and engagement.name in page.text
    assert http.get("/evidence/does-not-exist").status_code == 404

    archived = http.delete(f"/assessments/{assessment.id}/documents/{evidence.id}")
    assert archived.status_code == 200
    db.expire_all()
    assert db.get(Evidence, evidence.id).status == "archived"
    assert "Privacy Policy" not in archived.text


def test_htmx_upload_errors_render_the_status_partial(db, http, extractor):
    """Scenario 14: errors keep the existing 200 + error partial pattern."""
    svc()
    _client, _engagement, (assessment,) = _seed_hierarchy(db)
    response = http.post(
        f"/assessments/{assessment.id}/upload",
        data={"category": "privacy_policy"},
        files={"file": ("notes.xyz", io.BytesIO(b"content"), "application/octet-stream")},
    )
    assert response.status_code == 200
    assert UNSUPPORTED in response.text
    assert db.query(Evidence).count() == 0


EVIDENCE_OUT_KEYS = {
    "id", "engagement_id", "assessment_id", "original_filename", "mime_type",
    "document_category", "status", "uploaded_by", "file_hash_sha256",
    "file_size_bytes", "created_at", "current_version", "versions", "uses",
}
VERSION_OUT_KEYS = {
    "id", "version_number", "status", "original_filename", "mime_type",
    "file_hash_sha256", "file_size_bytes", "change_reason", "text_length", "created_at",
}
USE_OUT_KEYS = {"id", "evidence_id", "assessment_id", "framework_id", "requirement_id", "relevance", "created_at"}


def test_evidence_json_api(db, http, extractor):
    """Scenario 15."""
    ev = svc()
    _client, _engagement, (assessment,) = _seed_hierarchy(db)
    evidence_id = _upload(ev, db, assessment).evidence.id
    base = f"/api/evidence/{evidence_id}"

    detail = http.get(base)
    assert detail.status_code == 200
    body = detail.json()
    assert set(body) == EVIDENCE_OUT_KEYS
    assert set(body["current_version"]) == VERSION_OUT_KEYS
    assert "extracted_text" not in json.dumps(body)
    assert body["current_version"]["text_length"] == len("Extracted text from v1.pdf")
    assert http.get("/api/evidence/does-not-exist").status_code == 404

    versioned = http.post(
        f"{base}/versions",
        data={"change_reason": "Annual refresh"},
        files={"file": ("policy-v2.pdf", io.BytesIO(_pdf("api-v2")), "application/pdf")},
    )
    assert versioned.status_code == 201, versioned.text
    body = versioned.json()
    assert body["current_version"]["version_number"] == 2
    assert [v["status"] for v in body["versions"]] == ["superseded", "active"]

    no_reason = http.post(f"{base}/transitions", json={"to_status": "invalidated"})
    assert no_reason.status_code == 422
    assert no_reason.json()["detail"] == "A reason is required for this transition."
    invalidated = http.post(f"{base}/transitions", json={"to_status": "invalidated", "reason": "Unsigned draft"})
    assert invalidated.status_code == 200
    assert invalidated.json()["status"] == "invalidated"
    bad_edge = http.post(f"{base}/transitions", json={"to_status": "quarantined"})
    assert bad_edge.status_code == 409
    assert bad_edge.json()["detail"] == "Invalid evidence transition: invalidated -> quarantined."
    unknown = http.post(f"{base}/transitions", json={"to_status": "bogus"})
    assert unknown.status_code == 422
    assert unknown.json()["detail"] == "Unknown evidence status 'bogus'."
    http.post(f"{base}/transitions", json={"to_status": "active", "reason": "Signed copy confirmed"})

    mapped = http.post(
        f"{base}/uses",
        json={
            "assessment_id": assessment.id,
            "framework_id": "dpdpa",
            "requirement_id": "CH2.CONSENT.1",
            "relevance": "primary",
        },
    )
    assert mapped.status_code == 201, mapped.text
    assert set(mapped.json()) == USE_OUT_KEYS
    use_id = mapped.json()["id"]
    assert [u["id"] for u in http.get(base).json()["uses"]] == [use_id]
    assert http.delete(f"{base}/uses/{use_id}").status_code == 204
    assert http.delete(f"{base}/uses/{use_id}").status_code == 404


def test_system_edge_over_http_is_403(db, http, extractor):
    """Scenario 15: a consultant cannot release quarantine through the API."""
    ev = svc()
    _client, engagement, (assessment,) = _seed_hierarchy(db)
    evidence, _version = ev.receive_evidence(
        db,
        engagement_id=engagement.id,
        assessment_id=assessment.id,
        filename="pending.pdf",
        content=_pdf("pending"),
        category=None,
        uploaded_by="consultant",
        actor="consultant",
    )
    db.commit()

    response = http.post(f"/api/evidence/{evidence.id}/transitions", json={"to_status": "active"})
    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Transition quarantined -> active is system-driven and cannot be requested directly."
    )
    db.expire_all()
    assert db.get(Evidence, evidence.id).status == "quarantined"


def test_evidence_panel_rows_shape(db, extractor, monkeypatch):
    """Scenario 14: the Documents-tab row contract."""
    ev = svc()
    _client, _engagement, (assessment,) = _seed_hierarchy(db)
    legacy = _legacy_doc(db, assessment)
    good = _upload(ev, db, assessment, content=_pdf("good"), filename="good.pdf")
    monkeypatch.setattr(ev, "scan_blob", lambda path: False)
    bad = _upload(ev, db, assessment, content=_pdf("bad"), filename="bad.pdf")

    rows = {row["id"]: row for row in ev.evidence_panel_rows(db, assessment.id)}
    assert set(rows) == {legacy.id, good.evidence.id, bad.evidence.id}
    expected_keys = {
        "id", "source", "filename", "category", "file_type", "status", "version_count",
        "current_version_number", "sha256_prefix", "text_length", "uploaded_at",
        "mapped_in", "can_archive", "can_add_version",
    }
    assert all(set(row) == expected_keys for row in rows.values())

    good_row = rows[good.evidence.id]
    assert (good_row["source"], good_row["status"], good_row["file_type"]) == ("evidence", "active", "pdf")
    assert good_row["sha256_prefix"] == good.version.file_hash_sha256[:12]
    assert (good_row["version_count"], good_row["current_version_number"]) == (1, 1)
    assert (good_row["can_archive"], good_row["can_add_version"]) == (True, True)

    bad_row = rows[bad.evidence.id]
    assert bad_row["status"] == "rejected"
    assert bad_row["current_version_number"] is None
    assert (bad_row["can_archive"], bad_row["can_add_version"]) == (True, False)

    legacy_row = rows[legacy.id]
    assert (legacy_row["source"], legacy_row["status"]) == ("legacy", "legacy")
    assert legacy_row["sha256_prefix"] is None
    assert (legacy_row["mapped_in"], legacy_row["can_archive"], legacy_row["can_add_version"]) == (
        False, False, False,
    )


# --------------------------------------------------------------------------- #
# 16. Alembic revision
# --------------------------------------------------------------------------- #


def test_p2_1_revision_is_head_and_adds_columns_and_constraints(db_path, engine):
    """Scenario 16."""
    script = ScriptDirectory.from_config(_alembic_config(db_path))
    assert script.get_revision("3d8b6f0a2c51").down_revision == P2_1_REVISION

    inspector = inspect(engine)
    evidence_columns = {c["name"]: c for c in inspector.get_columns("evidence")}
    assert evidence_columns["assessment_id"]["nullable"] is True
    assert evidence_columns["document_category"]["nullable"] is True
    assert any(
        fk["referred_table"] == "assessments" and fk["constrained_columns"] == ["assessment_id"]
        for fk in inspector.get_foreign_keys("evidence")
    )
    assert "ix_evidence_assessment_id" in {i["name"] for i in inspector.get_indexes("evidence")}

    version_columns = {c["name"]: c for c in inspector.get_columns("evidence_versions")}
    assert version_columns["status"]["nullable"] is False
    assert version_columns["original_filename"]["nullable"] is False
    assert version_columns["mime_type"]["nullable"] is False
    assert version_columns["extracted_text"]["nullable"] is True
    assert "ix_evidence_versions_file_hash_sha256" in {
        i["name"] for i in inspector.get_indexes("evidence_versions")
    }
    assert "uq_evidence_versions_evidence_id_version_number" in {
        u["name"] for u in inspector.get_unique_constraints("evidence_versions")
    }
    assert "uq_evidence_uses_mapping" in {u["name"] for u in inspector.get_unique_constraints("evidence_uses")}


def test_version_number_uniqueness_is_enforced_by_the_database(db):
    """Scenario 16."""
    _client, engagement, _assessments = _seed_hierarchy(db)
    evidence = Evidence(
        engagement_id=engagement.id,
        original_filename="p.pdf",
        storage_path="evidence/x/y/v1.pdf",
        file_hash_sha256="0" * 64,
        file_size_bytes=1,
        mime_type="application/pdf",
        status="active",
        uploaded_by="consultant",
    )
    db.add(evidence)
    db.flush()
    common = dict(
        evidence_id=evidence.id,
        version_number=1,
        storage_path="evidence/x/y/v1.pdf",
        file_hash_sha256="0" * 64,
        file_size_bytes=1,
    )
    extra = dict(status="active", original_filename="p.pdf", mime_type="application/pdf")
    db.add(EvidenceVersion(**common, **extra))
    db.flush()
    db.add(EvidenceVersion(**common, **extra))
    with pytest.raises(IntegrityError):
        db.flush()


def test_downgrade_past_p2_1_refuses_while_evidence_exists(db_path, engine):
    """Scenario 16."""
    config = _alembic_config(db_path)
    now = datetime.now(timezone.utc).isoformat()
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO clients (id, name, industry, size, retention_years, created_at, updated_at) "
                 "VALUES ('c1', 'Acme', 'Technology', 'small', 7, :now, :now)"),
            {"now": now},
        )
        conn.execute(
            text("INSERT INTO engagements (id, client_id, name, type, status, created_at, updated_at) "
                 "VALUES ('e1', 'c1', 'Gap', 'gap_assessment', 'active', :now, :now)"),
            {"now": now},
        )
        conn.execute(
            text("INSERT INTO evidence (id, engagement_id, original_filename, storage_path, file_hash_sha256, "
                 "file_size_bytes, mime_type, status, uploaded_by, created_at) VALUES "
                 "('ev1', 'e1', 'p.pdf', 'evidence/e1/ev1/v1.pdf', :h, 1, 'application/pdf', 'active', 'consultant', :now)"),
            {"h": "0" * 64, "now": now},
        )

    with pytest.raises(RuntimeError, match="Refusing to downgrade past P2-1"):
        command.downgrade(config, P1_2_REVISION)
    assert "assessment_id" in {c["name"] for c in inspect(engine).get_columns("evidence")}


def test_downgrade_past_p2_1_succeeds_when_evidence_tables_are_empty(db_path, engine):
    """Scenario 16."""
    config = _alembic_config(db_path)
    assert ScriptDirectory.from_config(config).get_revision("3d8b6f0a2c51").down_revision == P2_1_REVISION
    command.downgrade(config, P1_2_REVISION)
    engine.dispose()
    inspector = inspect(engine)
    assert {"assessment_id", "document_category"}.isdisjoint(
        {c["name"] for c in inspector.get_columns("evidence")}
    )
    assert {"status", "original_filename", "mime_type", "extracted_text"}.isdisjoint(
        {c["name"] for c in inspector.get_columns("evidence_versions")}
    )
    command.upgrade(config, "head")


# --------------------------------------------------------------------------- #
# 17. Legacy document migration script
# --------------------------------------------------------------------------- #


def _seed_migration_fixture(db, upload_root: Path) -> dict:
    _client, _engagement, (assessment,) = _seed_hierarchy(db)
    orphan = _orphan_assessment(db)
    real_dir = upload_root / assessment.id
    real_dir.mkdir(parents=True)
    real_bytes = _pdf("legacy-real-file")
    real_path = real_dir / "abcd1234_policy.pdf"
    real_path.write_bytes(real_bytes)
    base = datetime(2025, 6, 1, 9, 30, tzinfo=timezone.utc)
    return {
        "assessment": assessment,
        "real_bytes": real_bytes,
        "real_path": real_path,
        "real": _legacy_doc(
            db, assessment, filename="policy.pdf", file_path=str(real_path),
            text_value="Real file text", uploaded_at=base,
        ),
        "text_only": _legacy_doc(
            db, assessment, filename="consent.docx",
            file_path="/nonexistent/uploads/x/deadbeef_consent.docx",
            text_value="Seeded consent text", uploaded_at=base + timedelta(hours=1),
            category="consent_form",
        ),
        "empty": _legacy_doc(
            db, assessment, filename="blank.pdf", file_path="/nonexistent/blank.pdf",
            text_value="", uploaded_at=base + timedelta(hours=2),
        ),
        "orphan": _legacy_doc(db, orphan, filename="orphan.pdf", uploaded_at=base + timedelta(hours=3)),
    }


def _document_snapshot(db) -> list[tuple]:
    db.expire_all()
    return [
        (d.id, d.assessment_id, d.filename, d.file_path, d.file_type, d.document_category, d.extracted_text)
        for d in db.query(AssessmentDocument).order_by(AssessmentDocument.id)
    ]


def test_document_migration_script(db, upload_root, monkeypatch):
    """Scenario 17."""
    ev = svc()
    script = migration_script()

    def _must_not_extract(*_args, **_kwargs):
        raise AssertionError("migration must copy extracted_text verbatim, never re-extract")

    monkeypatch.setattr(ev, "extract_text", _must_not_extract)
    fx = _seed_migration_fixture(db, upload_root)
    before_docs = _document_snapshot(db)

    stats = script.run_document_migration(db)

    assert (stats.migrated, stats.text_only, stats.skipped_existing, stats.skipped_orphan, stats.skipped_empty) == (
        2, 1, 0, 1, 1,
    )
    assert any("run scripts/migrate_legacy.py first" in w for w in stats.warnings)
    assert _document_snapshot(db) == before_docs
    assert fx["real_path"].read_bytes() == fx["real_bytes"]  # copied, not moved

    real = db.get(Evidence, fx["real"].id)
    (real_v1,) = _versions(db, real.id)
    assert real.assessment_id == fx["assessment"].id
    assert real.file_hash_sha256 == _sha(fx["real_bytes"])
    assert real.mime_type == "application/pdf"
    assert real.status == "active" and real_v1.status == "active"
    assert real.uploaded_by == "migration:assessment_documents"
    assert real.document_category == "privacy_policy"
    assert real_v1.extracted_text == "Real file text"
    assert real_v1.storage_path.endswith("/v1.pdf")
    assert real_v1.change_reason.startswith("Migrated from assessment_documents (original file copied from")
    assert real.created_at.replace(tzinfo=timezone.utc) == datetime(2025, 6, 1, 9, 30, tzinfo=timezone.utc)
    assert (upload_root / real_v1.storage_path).read_bytes() == fx["real_bytes"]

    text_only = db.get(Evidence, fx["text_only"].id)
    (text_v1,) = _versions(db, text_only.id)
    assert text_only.file_hash_sha256 == _sha(b"Seeded consent text")
    assert text_only.mime_type == "text/plain"
    assert text_v1.storage_path.endswith("/v1.txt")
    assert text_v1.extracted_text == "Seeded consent text"
    assert text_v1.change_reason.startswith("Migrated from assessment_documents: original file missing")
    assert text_only.original_filename == "consent.docx"

    assert db.get(Evidence, fx["empty"].id) is None
    assert db.get(Evidence, fx["orphan"].id) is None

    created_actors = {
        actor
        for (actor,) in db.execute(text("SELECT actor FROM audit_events WHERE action = 'evidence.created'"))
    }
    assert created_actors == {"system:migration"}

    docs = ev.analysis_documents(db, fx["assessment"].id)
    assert [(d["id"], d["source"]) for d in docs] == [
        (fx["real"].id, "evidence"),
        (fx["text_only"].id, "evidence"),
        (fx["empty"].id, "legacy"),
    ]


def test_document_migration_is_idempotent(db, upload_root):
    """Scenario 17: second run is a no-op."""
    svc()
    script = migration_script()
    _seed_migration_fixture(db, upload_root)
    script.run_document_migration(db)
    counts, blobs = _counts(db), _blob_files(upload_root)

    stats = script.run_document_migration(db)

    assert (stats.migrated, stats.skipped_existing) == (0, 2)
    assert _counts(db) == counts
    assert _blob_files(upload_root) == blobs


def test_document_migration_main_backs_up_before_writing(db, db_path, upload_root, tmp_path, monkeypatch):
    """Scenario 17: backup-first CLI, like scripts/migrate_legacy.py."""
    svc()
    script = migration_script()
    _seed_migration_fixture(db, upload_root)
    argv = [
        "--db-url", f"sqlite:///{db_path}",
        "--upload-dir", str(upload_root),
        "--backup-out-dir", str(tmp_path / "backups"),
    ]

    def _explode(*_args, **_kwargs):
        raise RuntimeError("disk full")

    monkeypatch.setattr(script, "create_backup", _explode)
    assert script.main(argv) != 0
    assert _counts(db)["evidence"] == 0

    evidence_rows_at_backup: list[int] = []

    def _record(db_file, uploads, out_dir):
        evidence_rows_at_backup.append(_counts(db)["evidence"])
        return Path(out_dir) / "backup-1"

    monkeypatch.setattr(script, "create_backup", _record)
    assert script.main(argv) == 0
    assert evidence_rows_at_backup == [0]
    assert _counts(db)["evidence"] == 2


# --------------------------------------------------------------------------- #
# 18-19. Standing guards and chain of custody
# --------------------------------------------------------------------------- #


def test_no_assessment_document_writers_or_save_upload_in_app():
    """Scenario 18. Scans .py sources only -- never __pycache__ (see handoff)."""
    offenders = []
    for path in sorted((REPO_ROOT / "app").rglob("*.py")):
        for number, line in enumerate(path.read_text().splitlines(), start=1):
            if re.search(r"(?<!class )\bAssessmentDocument\(", line) or "save_upload" in line:
                offenders.append(f"{path.relative_to(REPO_ROOT)}:{number}: {line.strip()}")
    assert offenders == []


def test_verify_version_detects_tampering_and_loss(db, upload_root, extractor):
    """Scenario 19."""
    ev = svc()
    _client, _engagement, (assessment,) = _seed_hierarchy(db)
    version = _upload(ev, db, assessment).version
    blob = upload_root / version.storage_path

    assert ev.verify_version(db, version.id) is True
    blob.write_bytes(blob.read_bytes() + b"tampered")
    assert ev.verify_version(db, version.id) is False
    blob.unlink()
    assert ev.verify_version(db, version.id) is False
    assert ev.sha256_hex(b"abc") == hashlib.sha256(b"abc").hexdigest()
