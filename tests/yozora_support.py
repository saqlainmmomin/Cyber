"""Shared fixtures for the Yozora backend tests (tasks/handoffs/2026-10-03-yozora-backend-features.md).

An Alembic-built SQLite database per test (so the seeded firm_settings row exists), a session on it,
and a TestClient whose get_db yields that session. Nothing here calls a model.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401 - register all ORM tables
from app.config import settings
from app.database import get_db
from app.main import app
from app.models.assessment import Assessment
from app.models.client import Client
from app.models.engagement import Engagement

REPO_ROOT = Path(__file__).resolve().parents[1]
YOZORA_REVISION = "b7d41c9e2a63"
PREVIOUS_REVISION = "5e9a2c7d4b18"


def alembic_config(db_path: Path) -> Config:
    config = Config(str(REPO_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return config


@pytest.fixture(scope="module", autouse=True)
def _register_frameworks():
    from app.main import _register_frameworks as register

    register()


@pytest.fixture()
def db_path(tmp_path):
    path = tmp_path / "yozora.sqlite3"
    command.upgrade(alembic_config(path), "head")
    return path


@pytest.fixture()
def engine(db_path):
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})

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


@pytest.fixture(autouse=True)
def upload_root(tmp_path, monkeypatch) -> Path:
    root = tmp_path / "uploads"
    root.mkdir()
    monkeypatch.setattr(settings, "upload_dir", str(root))
    return root


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


def seed_engagement(
    db,
    *,
    client_name: str = "Acme Corp",
    name: str = "Acme gap",
    status: str = "active",
    frameworks: tuple[str, ...] = ("dpdpa",),
    client: Client | None = None,
):
    """A client, an engagement and one assessment in it."""
    if client is None:
        client = Client(name=client_name, industry="Technology", size="medium")
        db.add(client)
        db.flush()
    engagement = Engagement(client_id=client.id, name=name, status=status)
    db.add(engagement)
    db.flush()
    assessment = Assessment(
        company_name=client.name,
        industry=client.industry,
        company_size=client.size,
        selected_frameworks=json.dumps(list(frameworks)),
        engagement_id=engagement.id,
    )
    db.add(assessment)
    db.commit()
    return client, engagement, assessment
