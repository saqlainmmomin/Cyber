"""Shared pytest fixtures, including the canonical DPDPA assessment."""

from __future__ import annotations

import hashlib

import pytest
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401 - register all ORM tables
from app.database import Base

CANONICAL_FIXTURE = Path(__file__).parent / "fixtures" / "canonical_dpdpa"

# The real developer database (app.config.settings.database_url's default
# path). Every test must use an isolated per-test database instead of this
# one — the session-scoped guard below fails loudly if any test leaks
# through to it, e.g. via a TestClient(app.main.app) that forgot to
# redirect settings.database_url before entering the lifespan.
_DEV_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "dpdpa.db"


def _sidecar_fingerprint(path: Path) -> tuple[bool, int]:
    return (path.exists(), path.stat().st_size if path.exists() else 0)


def _dev_db_fingerprint() -> tuple[tuple[int, int, str] | None, tuple[bool, int], tuple[bool, int]]:
    database_fingerprint = None
    if _DEV_DB_PATH.exists():
        stat = _DEV_DB_PATH.stat()
        digest = hashlib.sha256(_DEV_DB_PATH.read_bytes()).hexdigest()
        database_fingerprint = (stat.st_mtime_ns, stat.st_size, digest)
    return (
        database_fingerprint,
        _sidecar_fingerprint(Path(f"{_DEV_DB_PATH}-wal")),
        _sidecar_fingerprint(Path(f"{_DEV_DB_PATH}-shm")),
    )


@pytest.fixture(scope="session", autouse=True)
def _guard_dev_database_untouched():
    """Regression guard: the test suite must never create or modify the
    real developer database. A mismatch here means some test's app
    lifespan ran `alembic upgrade head` (or otherwise wrote) against
    settings.database_url's default path instead of an isolated
    per-test database."""
    before = _dev_db_fingerprint()
    yield
    after = _dev_db_fingerprint()
    assert after == before, (
        f"The test suite created or modified the real developer database at "
        f"{_DEV_DB_PATH} — a test is leaking through to settings.database_url's "
        "default path instead of using an isolated per-test database."
    )


@pytest.fixture(scope="session")
def monkeypatch_session():
    monkeypatch = pytest.MonkeyPatch()
    yield monkeypatch
    monkeypatch.undo()


@pytest.fixture(scope="session")
def canonical_dpdpa_assessment(tmp_path_factory):
    """Fully seeded synthetic assessment in an isolated SQLite database."""
    from tests.support.canonical_dpdpa import CanonicalAssessment, seed_assessment

    db_path = tmp_path_factory.mktemp("canonical-dpdpa") / "canonical.sqlite3"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    canonical_session = sessionmaker(bind=engine)()
    assessment = seed_assessment(canonical_session, CANONICAL_FIXTURE)
    fixture = CanonicalAssessment(CANONICAL_FIXTURE, canonical_session, assessment)
    try:
        yield fixture
    finally:
        canonical_session.close()
        engine.dispose()


@pytest.fixture(scope="module")
def session(tmp_path_factory):
    """Compatibility DB for the legacy executable Phase 1 test module."""
    db_path = tmp_path_factory.mktemp("phase1-prefill") / "test.sqlite3"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    test_session = sessionmaker(bind=engine)()
    try:
        yield test_session
    finally:
        test_session.close()
        engine.dispose()


@pytest.fixture(scope="module")
def assessment_bundle(session):
    from tests.test_phase1_prefill import setup_novapay

    return setup_novapay(session)


@pytest.fixture(scope="module")
def assessment_id(assessment_bundle):
    return assessment_bundle[0]


@pytest.fixture(scope="module")
def fixture(assessment_bundle):
    return assessment_bundle[1]


@pytest.fixture(scope="module")
def results():
    from tests.test_phase1_prefill import TestResults

    collected = TestResults()
    yield collected
    assert collected.failed == 0, "\n".join(collected.errors)
