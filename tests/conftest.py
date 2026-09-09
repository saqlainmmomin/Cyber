"""Shared pytest fixtures, including the canonical DPDPA assessment."""

from __future__ import annotations

import pytest
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401 - register all ORM tables
from app.database import Base

CANONICAL_FIXTURE = Path(__file__).parent / "fixtures" / "canonical_dpdpa"


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
