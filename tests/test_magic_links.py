"""TDD ("red") contract suite for P2-5, client magic links.

Written before the implementation. It pins the interface that
``tasks/handoffs/2026-09-23-p2-5-magic-links.md`` specifies, and must turn
green WITHOUT edits to its assertions. Scenario numbers in the docstrings match
the handoff's "Test scenarios" section.

Modules under contract (none exist yet):

``app.services.magic_links``
    Constants (``TOKEN_BYTES``, ``UPLOADS_PER_HOUR``, ``MAX_FILE_BYTES``,
    ``MULTIPART_OVERHEAD_BYTES``, ``SECURITY_HEADERS``, the fixed messages),
    the ``MagicLinkError`` hierarchy, ``generate_token``, ``token_digest``,
    ``client_actor``, ``create_link``, ``revoke_link``, ``resolve_token``,
    ``receive_client_upload``, ``redact_magic_tokens`` and
    ``MagicTokenRedactionFilter``. ``_now`` is a module global patched here.

``app.routers.magic``
    ``GET``/``POST /magic/{token}`` (client) and the two consultant routes
    under ``/engagements/{engagement_id}/magic-links``.

``app.services.evidence.ingest_engagement_upload``
    The engagement-level intake orchestrator (``assessment_id=None``).

Every test resolves ``ml()`` as its first statement, so before implementation
each fails with ``ModuleNotFoundError: No module named
'app.services.magic_links'`` -- a failure for the right reason.

Test-DB strategy: same as ``tests/test_evidence_service.py`` -- Alembic-built,
FK-enforcing SQLite per test, ``settings.upload_dir`` redirected to
``tmp_path``, and ``app.services.evidence.extract_text`` replaced by a
deterministic fake (no pdfplumber, no vision LLM).
"""

from __future__ import annotations

import hashlib
import importlib
import io
import json
import logging
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401 - register all ORM tables
from app.config import settings
from app.models.assessment import Assessment
from app.models.audit_event import AuditEvent
from app.models.client import Client
from app.models.conclusion import Conclusion
from app.models.engagement import Engagement
from app.models.evidence import Evidence, EvidenceVersion
from app.models.magic_link import MagicLink

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVICE_MODULE = "app.services.magic_links"
TOKEN_RE = re.compile(r"/magic/([A-Za-z0-9_-]{22})")

EXPECTED_SECURITY_HEADERS = {
    "referrer-policy": "no-referrer",
    "cache-control": "no-store",
    "x-robots-tag": "noindex, nofollow",
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "content-security-policy": (
        "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; "
        "frame-ancestors 'none'; base-uri 'none'"
    ),
}
INVALID_LINK = "This link is invalid or has expired. Contact your consultant for a new link."
UNSUPPORTED = "Unsupported file type. Upload PDF, DOCX, PNG, JPG, JPEG, or WEBP files."
SCAN_REJECTED = "File failed the malware scan and was not released from quarantine."
ITEMS = ["Information security policy", "Access review evidence"]


def ml():
    """The service under contract, imported lazily so a missing module fails
    each test individually."""

    return importlib.import_module(SERVICE_MODULE)


def ev():
    return importlib.import_module("app.services.evidence")


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="module", autouse=True)
def _register_frameworks():
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
    path = tmp_path / "magic.sqlite3"
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
def texts(monkeypatch) -> dict[bytes, str]:
    mapping: dict[bytes, str] = {}

    def _fake_extract(path, file_type):
        return mapping.get(Path(path).read_bytes(), f"Extracted text from {Path(path).name}")

    monkeypatch.setattr(ev(), "extract_text", _fake_extract)
    return mapping


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _seed(db, *, client_name="Acme Corp", engagement_name="Acme gap", status="active"):
    client = Client(name=client_name, industry="Technology", size="medium")
    db.add(client)
    db.flush()
    engagement = Engagement(client_id=client.id, name=engagement_name, status=status)
    db.add(engagement)
    db.flush()
    assessment = Assessment(
        company_name=client_name,
        industry="Technology",
        company_size="medium",
        selected_frameworks=json.dumps(["dpdpa"]),
        engagement_id=engagement.id,
    )
    db.add(assessment)
    db.commit()
    return client, engagement, assessment


def _create(db, engagement, *, items=ITEMS, expires_in_days=7, max_uploads=20, max_total_mb=100):
    created = ml().create_link(
        db,
        engagement_id=engagement.id,
        item_titles=list(items),
        expires_in_days=expires_in_days,
        max_uploads=max_uploads,
        max_total_mb=max_total_mb,
        actor="consultant",
    )
    db.commit()
    return created


def _pdf(tag: str, size: int | None = None) -> bytes:
    base = b"%PDF-1.4\n% CyberAssess magic-link test " + tag.encode() + b"\n"
    if size is not None:
        base = base + b"0" * max(0, size - len(base) - 6)
    return base + b"%%EOF\n"


def _post_file(http, token, *, content, filename="policy.pdf", item_key="item-1"):
    return http.post(
        f"/magic/{token}",
        data={"item_key": item_key},
        files={"file": (filename, io.BytesIO(content), "application/pdf")},
    )


def _audit(db):
    rows = db.execute(
        text("SELECT actor, action, entity_type, entity_id, metadata_json FROM audit_events ORDER BY rowid")
    ).all()
    return [(a, act, t, i, json.loads(m) if m else {}) for a, act, t, i, m in rows]


def _counts(db):
    db.expire_all()
    return (db.query(Evidence).count(), db.query(EvidenceVersion).count(), db.query(AuditEvent).count())


def _assert_security_headers(response):
    for name, value in EXPECTED_SECURITY_HEADERS.items():
        assert response.headers.get(name) == value, f"{name}: {response.headers.get(name)!r}"


class _StatementCounter:
    def __init__(self, engine):
        self.engine = engine
        self.count = 0

    def _count(self, *args):
        self.count += 1

    def __enter__(self):
        event.listen(self.engine, "before_cursor_execute", self._count)
        return self

    def __exit__(self, *exc):
        event.remove(self.engine, "before_cursor_execute", self._count)


# --------------------------------------------------------------------------- #
# 1-3. Tokens and link creation
# --------------------------------------------------------------------------- #


def test_token_generation_and_digest(monkeypatch):
    """Scenario 1: 128 bits from ``secrets.token_urlsafe``, 22 URL-safe chars,
    SHA-256 hex digest of the ASCII token."""
    m = ml()
    calls = []
    real = m.secrets.token_urlsafe

    def _spy(nbytes):
        calls.append(nbytes)
        return real(nbytes)

    monkeypatch.setattr(m.secrets, "token_urlsafe", _spy)
    tokens = {m.generate_token() for _ in range(500)}
    assert calls == [16] * 500
    assert m.TOKEN_BYTES == 16
    assert len(tokens) == 500
    assert all(re.fullmatch(r"[A-Za-z0-9_-]{22}", t) for t in tokens)
    token = next(iter(tokens))
    assert m.token_digest(token) == hashlib.sha256(token.encode("ascii")).hexdigest()


def test_create_link_stores_only_the_digest(db, db_path):
    """Scenario 2."""
    m = ml()
    _client, engagement, _assessment = _seed(db)
    before = datetime.now(timezone.utc)
    created = _create(db, engagement, expires_in_days=5, max_uploads=12, max_total_mb=40)
    token, link = created.token, created.link

    db.expire_all()
    stored = db.get(MagicLink, link.id)
    assert stored.engagement_id == engagement.id
    assert stored.token_digest == hashlib.sha256(token.encode("ascii")).hexdigest()
    assert json.loads(stored.scope_json) == {
        "items": [{"key": "item-1", "title": ITEMS[0]}, {"key": "item-2", "title": ITEMS[1]}],
        "version": 1,
    }
    assert stored.scope_json == json.dumps(json.loads(stored.scope_json), sort_keys=True)
    assert stored.max_uploads == 12
    assert stored.max_size_bytes == 40 * 1024 * 1024
    assert stored.revoked_at is None
    expires = stored.expires_at.replace(tzinfo=stored.expires_at.tzinfo or timezone.utc)
    assert before + timedelta(days=5) - timedelta(minutes=1) <= expires <= before + timedelta(days=5, minutes=1)
    assert m.client_actor(stored) == f"client_link:{stored.id}"

    (actor, action, entity_type, entity_id, meta), = _audit(db)
    assert (actor, action, entity_type, entity_id) == ("consultant", "magic_link.created", "magic_link", link.id)
    assert set(meta) == {"engagement_id", "expires_at", "item_keys", "max_size_bytes", "max_uploads"}
    assert meta["item_keys"] == ["item-1", "item-2"]

    db.close()
    dump = "\n".join(sqlite3.connect(db_path).iterdump())
    assert token not in dump
    assert token[:12] not in dump


@pytest.mark.parametrize(
    ("kwargs", "error", "message"),
    [
        ({"item_titles": []}, "MagicLinkValidationError", "Add at least one requested item."),
        ({"item_titles": ["  ", ""]}, "MagicLinkValidationError", "Add at least one requested item."),
        ({"item_titles": [f"Item {n}" for n in range(21)]}, "MagicLinkValidationError",
         "A link can request at most 20 items."),
        ({"item_titles": ["x" * 201]}, "MagicLinkValidationError",
         "Requested item titles must be 200 characters or fewer."),
        ({"item_titles": ["Policy", "policy "]}, "MagicLinkValidationError",
         "Requested item titles must be unique."),
        ({"expires_in_days": 0}, "MagicLinkValidationError", "Expiry must be between 1 and 30 days."),
        ({"expires_in_days": 31}, "MagicLinkValidationError", "Expiry must be between 1 and 30 days."),
        ({"max_uploads": 0}, "MagicLinkValidationError", "Upload limit must be between 1 and 100."),
        ({"max_uploads": 101}, "MagicLinkValidationError", "Upload limit must be between 1 and 100."),
        ({"max_total_mb": 0}, "MagicLinkValidationError", "Total size limit must be between 1 and 500 MB."),
        ({"max_total_mb": 501}, "MagicLinkValidationError", "Total size limit must be between 1 and 500 MB."),
    ],
)
def test_create_link_validation(db, kwargs, error, message):
    """Scenario 3."""
    m = ml()
    _client, engagement, _assessment = _seed(db)
    args = {"item_titles": ITEMS, "expires_in_days": 7, "max_uploads": 20, "max_total_mb": 100, **kwargs}
    with pytest.raises(getattr(m, error)) as info:
        m.create_link(db, engagement_id=engagement.id, actor="consultant", **args)
    assert info.value.message == message
    assert info.value.status_code == 422
    db.rollback()
    assert db.query(MagicLink).count() == 0
    assert db.query(AuditEvent).count() == 0


def test_create_link_requires_an_active_engagement(db):
    """Scenario 3."""
    m = ml()
    _client, archived, _assessment = _seed(db, status="archived")
    base = {"item_titles": ITEMS, "expires_in_days": 7, "max_uploads": 20, "max_total_mb": 100, "actor": "consultant"}
    with pytest.raises(m.MagicLinkNotFound) as missing:
        m.create_link(db, engagement_id="no-such-engagement", **base)
    assert (missing.value.message, missing.value.status_code) == ("Engagement not found", 404)
    with pytest.raises(m.MagicLinkConflict) as inactive:
        m.create_link(db, engagement_id=archived.id, **base)
    assert inactive.value.message == "Magic links can only be created for active engagements."
    assert inactive.value.status_code == 409


def test_consultant_create_route_shows_token_once(db, http):
    """Scenario 4."""
    m = ml()
    _client, engagement, _assessment = _seed(db)
    response = http.post(
        f"/engagements/{engagement.id}/magic-links",
        data={"items": "Information security policy\n\n  Access review evidence  \n",
              "expires_in_days": "7", "max_uploads": "20", "max_total_mb": "100"},
    )
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["referrer-policy"] == "no-referrer"
    (token,) = set(TOKEN_RE.findall(response.text))
    assert f"http://testserver/magic/{token}" in response.text
    link = db.query(MagicLink).one()
    assert link.token_digest == m.token_digest(token)
    assert [i["title"] for i in json.loads(link.scope_json)["items"]] == ITEMS

    page = http.get(f"/engagements/{engagement.id}")
    assert page.status_code == 200
    assert token not in page.text
    assert link.id[:8] in page.text
    assert "0 of 20 uploads" in page.text
    assert "Active" in page.text

    invalid = http.post(
        f"/engagements/{engagement.id}/magic-links",
        data={"items": "", "expires_in_days": "7", "max_uploads": "20", "max_total_mb": "100"},
    )
    assert invalid.status_code == 200
    assert "Add at least one requested item." in invalid.text
    assert db.query(MagicLink).count() == 1
    assert http.post(
        "/engagements/missing/magic-links",
        data={"items": "X", "expires_in_days": "7", "max_uploads": "20", "max_total_mb": "100"},
    ).status_code == 404


# --------------------------------------------------------------------------- #
# 5-7. Resolution, non-enumerability, scoped page
# --------------------------------------------------------------------------- #


def test_resolve_token_rules(db, engine, monkeypatch):
    """Scenario 5."""
    m = ml()
    _client, engagement, _assessment = _seed(db)
    created = _create(db, engagement, expires_in_days=1)
    assert m.resolve_token(db, created.token).id == created.link.id

    for malformed in ("", "short", "A" * 21, "A" * 23, "A" * 21 + "*", "A" * 21 + "="):
        with _StatementCounter(engine) as counter:
            assert m.resolve_token(db, malformed) is None
        assert counter.count == 0, f"malformed token {malformed!r} reached the database"

    assert m.resolve_token(db, m.generate_token()) is None

    real_now = m._now()
    monkeypatch.setattr(m, "_now", lambda: real_now + timedelta(days=1, seconds=1))
    assert m.resolve_token(db, created.token) is None
    monkeypatch.setattr(m, "_now", lambda: real_now)
    assert m.resolve_token(db, created.token) is not None

    engagement.status = "archived"
    db.commit()
    assert m.resolve_token(db, created.token) is None
    engagement.status = "active"
    db.commit()

    m.revoke_link(db, engagement_id=engagement.id, link_id=created.link.id, actor="consultant")
    db.commit()
    assert m.resolve_token(db, created.token) is None


def test_invalid_tokens_are_indistinguishable(db, http, texts, monkeypatch):
    """Scenario 6: malformed, unknown, expired, revoked and inactive-engagement
    tokens all get the same 404 with a byte-identical body, on GET and POST,
    with the full security header set."""
    m = ml()
    _c1, engagement, _a1 = _seed(db)
    _c2, other_engagement, _a2 = _seed(db, client_name="Other Co", engagement_name="Other gap")
    expired = _create(db, engagement, expires_in_days=1)
    revoked = _create(db, engagement)
    m.revoke_link(db, engagement_id=engagement.id, link_id=revoked.link.id, actor="consultant")
    inactive = _create(db, other_engagement)
    other_engagement.status = "archived"
    db.commit()

    real_now = m._now()
    expired.link.expires_at = real_now - timedelta(seconds=1)
    db.commit()

    tokens = ["A" * 21 + "*", "short", m.generate_token(), expired.token, revoked.token, inactive.token]
    bodies = set()
    for token in tokens:
        for response in (http.get(f"/magic/{token}"), _post_file(http, token, content=_pdf(token))):
            assert response.status_code == 404, (token, response.status_code)
            _assert_security_headers(response)
            assert INVALID_LINK in response.text
            bodies.add(response.content)
    assert len(bodies) == 1
    assert _counts(db)[0] == 0


def test_valid_page_is_scoped_to_the_link(db, http, texts):
    """Scenario 7: the client page shows the link's request items and limits,
    and nothing else from the engagement."""
    m = ml()
    client, engagement, assessment = _seed(
        db, client_name="Zyxwv Holdings", engagement_name="Zyxwv Secret Engagement"
    )
    consultant_upload = ev().ingest_upload(
        db, assessment_id=assessment.id, filename="board-minutes-confidential.pdf",
        content=_pdf("consultant"), category="other",
    )
    db.add(Conclusion(
        assessment_id=assessment.id, requirement_id="CH2.CONSENT.1", framework_id="dpdpa",
        outcome="non_compliant", rationale="CONCLUSION-SENTINEL-7731", evidence_summary="-",
        gaps_identified="-", risk_level="high", recommended_action="-", ai_proposed=True,
    ))
    db.commit()
    link = _create(db, engagement, max_uploads=5)
    _create(db, engagement, items=["Other request SENTINEL-ITEM"])

    response = http.get(f"/magic/{link.token}")
    assert response.status_code == 200
    _assert_security_headers(response)
    body = response.text
    for title in ITEMS:
        assert title in body
    assert 'value="item-1"' in body and 'value="item-2"' in body
    assert "5 of 5 uploads remaining" in body
    assert 'type="file"' in body
    assert '<meta name="referrer" content="no-referrer">' in body
    for forbidden in (
        "Zyxwv", "board-minutes-confidential", "CONCLUSION-SENTINEL", "SENTINEL-ITEM",
        client.id, engagement.id, assessment.id, consultant_upload.evidence.id, link.token,
    ):
        assert forbidden not in body, forbidden
    for external in ("<script", "<link", "src=", "http://", "https://", " action="):
        assert external not in body, external


# --------------------------------------------------------------------------- #
# 8-14. Uploads
# --------------------------------------------------------------------------- #


def test_client_upload_creates_engagement_level_evidence(db, http, texts):
    """Scenario 8."""
    m = ml()
    e = ev()
    _client, engagement, assessment = _seed(db)
    created = _create(db, engagement)
    link_id = created.link.id
    actor = f"client_link:{link_id}"
    content = _pdf("client-policy")

    response = _post_file(http, created.token, content=content, filename="ISMS Policy.pdf", item_key="item-1")
    assert response.status_code == 200, response.text
    _assert_security_headers(response)
    assert "File received: ISMS Policy.pdf" in response.text
    assert "19 of 20 uploads remaining" in response.text

    db.expire_all()
    evidence = db.query(Evidence).one()
    version = db.query(EvidenceVersion).one()
    assert evidence.engagement_id == engagement.id
    assert evidence.assessment_id is None
    assert evidence.uploaded_by == actor
    assert evidence.status == "active"
    assert evidence.file_hash_sha256 == hashlib.sha256(content).hexdigest()
    assert version.change_reason == "Client upload via magic link for requested item: Information security policy"
    assert version.extracted_text == "Extracted text from v1.pdf"
    assert created.token not in (evidence.uploaded_by + evidence.storage_path)

    audit = _audit(db)
    assert [row[1] for row in audit] == [
        "magic_link.created",
        "magic_link.upload_received",
        "evidence.created",
        "evidence_version.created",
        "evidence_version.status_changed",
        "evidence.status_changed",
    ]
    actor_of, _action, entity_type, entity_id, meta = audit[1]
    assert (actor_of, entity_type, entity_id) == (actor, "magic_link", link_id)
    assert meta == {
        "evidence_id": evidence.id,
        "item_key": "item-1",
        "magic_link_id": link_id,
        "sha256": evidence.file_hash_sha256,
        "size_bytes": len(content),
    }
    # Receipt events are the client's; scan-driven release is the placeholder's (P2-1).
    assert [row[0] for row in audit[2:]] == [actor, actor, "system:scan-placeholder", "system:scan-placeholder"]

    # Engagement-level: invisible to the assessment until a consultant maps it.
    assert e.analysis_documents(db, assessment.id) == []
    assert db.get(Assessment, assessment.id).status == "created"
    e.map_evidence(
        db, evidence_id=evidence.id, assessment_id=assessment.id, framework_id="dpdpa",
        requirement_id="CH2.CONSENT.1", relevance="primary", actor="consultant",
    )
    db.commit()
    assert [d["id"] for d in e.analysis_documents(db, assessment.id)] == [evidence.id]

    page = http.get(f"/magic/{created.token}")
    assert "ISMS Policy.pdf" in page.text and "Received" in page.text

    detail = http.get(f"/engagements/{engagement.id}")
    assert f"/evidence/{evidence.id}" in detail.text
    assert "1 of 20 uploads" in detail.text


def test_upload_must_name_one_of_the_links_items(db, http, texts):
    """Scenario 9: restricted to named request items."""
    ml()
    _client, engagement, _assessment = _seed(db)
    created = _create(db, engagement)
    _create(db, engagement, items=["A", "B", "C"])

    for bad in ("item-3", "", "../item-1"):
        response = _post_file(http, created.token, content=_pdf("x" + bad), item_key=bad)
        assert response.status_code == 422, bad
        assert "Choose one of the requested items." in response.text
        _assert_security_headers(response)
    missing = http.post(f"/magic/{created.token}", data={"item_key": "item-1"})
    assert missing.status_code == 422
    assert "Choose a file to upload." in missing.text
    assert _counts(db)[0] == 0


def test_hourly_rate_limit(db, http, texts, monkeypatch):
    """Scenario 10: durable, DB-derived per-link hourly limit."""
    m = ml()
    monkeypatch.setattr(m, "UPLOADS_PER_HOUR", 2)
    _client, engagement, _assessment = _seed(db)
    created = _create(db, engagement)

    assert _post_file(http, created.token, content=_pdf("r1")).status_code == 200
    assert _post_file(http, created.token, content=_pdf("r2")).status_code == 200
    limited = _post_file(http, created.token, content=_pdf("r3"))
    assert limited.status_code == 429
    _assert_security_headers(limited)
    assert "Too many uploads in the last hour. Try again later." in limited.text
    assert 1 <= int(limited.headers["retry-after"]) <= 3600
    assert _counts(db)[0] == 2

    for evidence in db.query(Evidence).all():
        evidence.created_at = evidence.created_at - timedelta(minutes=61)
    db.commit()
    assert _post_file(http, created.token, content=_pdf("r3")).status_code == 200


def test_upload_count_limit_includes_rejected_receipts(db, http, texts, monkeypatch):
    """Scenario 11."""
    m = ml()
    _client, engagement, _assessment = _seed(db)
    created = _create(db, engagement, max_uploads=2)

    monkeypatch.setattr(ev(), "scan_blob", lambda path: False)
    rejected = _post_file(http, created.token, content=_pdf("bad"))
    assert rejected.status_code == 422
    assert SCAN_REJECTED in rejected.text
    monkeypatch.setattr(ev(), "scan_blob", lambda path: True)
    assert _post_file(http, created.token, content=_pdf("ok")).status_code == 200

    exhausted = _post_file(http, created.token, content=_pdf("third"))
    assert exhausted.status_code == 403
    assert "This link has reached its upload limit. Contact your consultant." in exhausted.text
    assert _counts(db)[0] == 2
    db.expire_all()
    assert sorted(e.status for e in db.query(Evidence)) == ["active", "rejected"]

    page = http.get(f"/magic/{created.token}")
    assert page.status_code == 200
    assert "This link has reached its upload limit." in page.text
    assert 'type="file"' not in page.text
    assert m.UPLOAD_LIMIT_MESSAGE == "This link has reached its upload limit. Contact your consultant."


def test_size_limits(db, http, texts, monkeypatch):
    """Scenario 12: request-size guard before parsing, per-file cap, per-link total."""
    m = ml()
    _client, engagement, _assessment = _seed(db)
    created = _create(db, engagement, max_total_mb=1)

    monkeypatch.setattr(m, "MAX_FILE_BYTES", 1000)
    # Guard: an oversized body is refused from Content-Length alone -- this body
    # is not even valid multipart, so reaching the parser would not yield 413.
    oversized = http.post(
        f"/magic/{created.token}",
        content=b"x" * (1000 + m.MULTIPART_OVERHEAD_BYTES + 1),
        headers={"content-type": "multipart/form-data; boundary=nothing"},
    )
    assert oversized.status_code == 413
    assert m.FILE_TOO_LARGE_MESSAGE in oversized.text
    _assert_security_headers(oversized)

    too_big = _post_file(http, created.token, content=_pdf("big", size=1001))
    assert too_big.status_code == 413
    assert m.FILE_TOO_LARGE_MESSAGE in too_big.text
    assert _post_file(http, created.token, content=_pdf("fits", size=1000)).status_code == 200

    monkeypatch.setattr(m, "MAX_FILE_BYTES", 25 * 1024 * 1024)
    assert _post_file(http, created.token, content=_pdf("a", size=700_000)).status_code == 200
    over_total = _post_file(http, created.token, content=_pdf("b", size=400_000))
    assert over_total.status_code == 413
    assert "This upload would exceed the total size limit for this link." in over_total.text
    assert _counts(db)[0] == 2
    assert m.FILE_TOO_LARGE_MESSAGE == "Files must be 25 MB or smaller."
    assert m.MAX_FILE_BYTES == 25 * 1024 * 1024


def test_duplicates_are_scoped_to_the_link_and_leak_nothing(db, http, texts):
    """Scenario 13."""
    ml()
    _client, engagement, _assessment = _seed(db)
    first = _create(db, engagement)
    second = _create(db, engagement)
    content = _pdf("same")

    assert _post_file(http, first.token, content=content, filename="board-minutes.pdf").status_code == 200
    again = _post_file(http, first.token, content=content, filename="renamed.pdf")
    assert again.status_code == 409
    assert "You have already uploaded this file through this link." in again.text

    other = _post_file(http, second.token, content=content, filename="copy.pdf")
    assert other.status_code == 200
    assert "board-minutes.pdf" not in other.text
    assert "board-minutes.pdf" not in http.get(f"/magic/{second.token}").text
    assert _counts(db)[0] == 2


def test_evidence_validation_errors_pass_through_and_write_nothing(db, http, texts, upload_root):
    """Scenario 14."""
    ml()
    _client, engagement, _assessment = _seed(db)
    created = _create(db, engagement)
    before = _counts(db)

    unsupported = _post_file(http, created.token, content=b"MZ\x90\x00", filename="tool.exe")
    assert unsupported.status_code == 400
    assert UNSUPPORTED in unsupported.text
    empty = _post_file(http, created.token, content=b"", filename="empty.pdf")
    assert empty.status_code == 422
    assert "The uploaded file is empty." in empty.text
    texts[_pdf("blank")] = "   "
    blank = _post_file(http, created.token, content=_pdf("blank"))
    assert blank.status_code == 422
    assert "Could not extract text from this document." in blank.text

    assert _counts(db) == before
    assert not (upload_root / "evidence").exists() or not any(
        p.is_file() for p in (upload_root / "evidence").rglob("*")
    )


def test_ingest_engagement_upload_service(db, texts, upload_root):
    """Scenario 14: the P2-1 orchestrator for engagement-level intake."""
    ml()
    e = ev()
    _client, engagement, _assessment = _seed(db)
    result = e.ingest_engagement_upload(
        db, engagement_id=engagement.id, filename="policy.pdf", content=_pdf("svc"),
        category=None, uploaded_by="client_link:test", change_reason="Because",
    )
    assert result.released is True
    assert result.evidence.assessment_id is None
    assert result.evidence.engagement_id == engagement.id
    assert result.version.change_reason == "Because"
    assert result.version.storage_path == f"evidence/{engagement.id}/{result.evidence.id}/v1.pdf"
    with pytest.raises(e.EvidenceNotFound) as info:
        e.ingest_engagement_upload(
            db, engagement_id="missing", filename="p.pdf", content=_pdf("m"),
            category=None, uploaded_by="client_link:test",
        )
    assert info.value.message == "Engagement not found"


# --------------------------------------------------------------------------- #
# 15-17. Revocation, secrecy, reuse guard
# --------------------------------------------------------------------------- #


def test_revocation(db, http, texts):
    """Scenario 15."""
    m = ml()
    _client, engagement, _assessment = _seed(db)
    _c2, other_engagement, _a2 = _seed(db, client_name="Other", engagement_name="Other gap")
    created = _create(db, engagement)
    assert http.get(f"/magic/{created.token}").status_code == 200

    wrong = http.post(f"/engagements/{other_engagement.id}/magic-links/{created.link.id}/revoke")
    assert wrong.status_code == 404
    response = http.post(f"/engagements/{engagement.id}/magic-links/{created.link.id}/revoke")
    assert response.status_code == 200
    assert "Revoked" in response.text
    db.expire_all()
    assert db.get(MagicLink, created.link.id).revoked_at is not None
    actor, action, entity_type, entity_id, meta = _audit(db)[-1]
    assert (actor, action, entity_type, entity_id) == ("consultant", "magic_link.revoked", "magic_link", created.link.id)
    assert set(meta) == {"engagement_id", "revoked_at"}

    assert http.get(f"/magic/{created.token}").status_code == 404
    assert _post_file(http, created.token, content=_pdf("late")).status_code == 404
    again = http.post(f"/engagements/{engagement.id}/magic-links/{created.link.id}/revoke")
    assert again.status_code == 200
    assert "Magic link is already revoked." in again.text
    with pytest.raises(m.MagicLinkConflict):
        m.revoke_link(db, engagement_id=engagement.id, link_id=created.link.id, actor="consultant")
    with pytest.raises(m.MagicLinkNotFound) as info:
        m.revoke_link(db, engagement_id=engagement.id, link_id="missing", actor="consultant")
    assert info.value.message == "Magic link not found"


def test_token_never_logged_and_access_log_redacted(db, http, texts, caplog, db_path):
    """Scenario 16."""
    m = ml()
    import app.main  # noqa: F401 - installs the access-log filter at import

    access_filters = logging.getLogger("uvicorn.access").filters
    assert any(isinstance(f, m.MagicTokenRedactionFilter) for f in access_filters)

    record = logging.LogRecord(
        "uvicorn.access", logging.INFO, __file__, 1, '%s - "%s %s HTTP/%s" %d',
        ("127.0.0.1:5000", "GET", "/magic/AbCdEfGhIjKlMnOpQrStUv?x=1", "1.1", 200), None,
    )
    assert m.MagicTokenRedactionFilter().filter(record) is True
    assert record.getMessage() == '127.0.0.1:5000 - "GET /magic/[redacted]?x=1 HTTP/1.1" 200'
    assert m.redact_magic_tokens("see /magic/abc_-123 and /magic/xyz") == "see /magic/[redacted] and /magic/[redacted]"

    _client, engagement, _assessment = _seed(db)
    with caplog.at_level(logging.DEBUG):
        created = http.post(
            f"/engagements/{engagement.id}/magic-links",
            data={"items": "Policy", "expires_in_days": "7", "max_uploads": "20", "max_total_mb": "100"},
        )
        (token,) = set(TOKEN_RE.findall(created.text))
        http.get(f"/magic/{token}")
        _post_file(http, token, content=_pdf("logged"))
        http.get(f"/magic/{m.generate_token()}")
    app_records = [r for r in caplog.records if not r.name.startswith(("httpx", "httpcore"))]
    assert all(token not in r.getMessage() for r in app_records)

    for _actor, _action, _type, _id, meta in _audit(db):
        assert token not in json.dumps(meta)
        assert m.token_digest(token) not in json.dumps(meta)
    db.close()
    dump = "\n".join(sqlite3.connect(db_path).iterdump())
    assert token not in dump
    assert token[:12] not in dump


def test_magic_code_reuses_the_evidence_pipeline():
    """Scenario 17: no second upload pipeline."""
    ml()
    sources = {
        name: (REPO_ROOT / name).read_text()
        for name in ("app/services/magic_links.py", "app/routers/magic.py")
    }
    assert "ingest_engagement_upload" in sources["app/services/magic_links.py"]
    for name, source in sources.items():
        for forbidden in ("_write_blob", ".write_bytes(", "open(", "receive_evidence(",
                          "release_from_quarantine(", "extract_text("):
            assert forbidden not in source, f"{name} contains {forbidden}"
