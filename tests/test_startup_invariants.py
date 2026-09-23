import asyncio
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.legacy_migrations import run_column_migrations
from app.main import (
    _assert_framework_catalog_complete,
    _register_frameworks,
    lifespan,
)


def test_framework_catalog_matches_registered_frameworks(monkeypatch):
    _register_frameworks()
    _assert_framework_catalog_complete()

    monkeypatch.setattr(
        "app.routers.web.ROADMAP_FRAMEWORKS",
        ("gdpr", "hipaa"),
    )

    with pytest.raises(RuntimeError, match="pci_dss"):
        _assert_framework_catalog_complete()


@pytest.mark.parametrize(
    ("catalog_name", "catalog_ids", "error_field", "duplicate_id"),
    [
        (
            "ENABLED_ASSESSMENT_FRAMEWORKS",
            ("dpdpa", "dpdpa", "iso27001", "nist_csf"),
            "duplicates_in_enabled",
            "dpdpa",
        ),
        (
            "ROADMAP_FRAMEWORKS",
            ("gdpr", "hipaa", "pci_dss", "pci_dss"),
            "duplicates_in_roadmap",
            "pci_dss",
        ),
        (
            "ROADMAP_FRAMEWORKS",
            ("gdpr", "hipaa", "pci_dss", "dpdpa"),
            "enabled_roadmap_overlap",
            "dpdpa",
        ),
    ],
)
def test_framework_catalog_rejects_duplicate_or_overlapping_entries(
    monkeypatch, catalog_name, catalog_ids, error_field, duplicate_id
):
    _register_frameworks()
    monkeypatch.setattr(f"app.routers.web.{catalog_name}", catalog_ids)

    with pytest.raises(RuntimeError, match=rf"{error_field}=.*{duplicate_id}"):
        _assert_framework_catalog_complete()


def test_lifespan_validates_catalog_before_running_migrations(monkeypatch):
    startup_events = []

    monkeypatch.setattr(
        "app.main._run_alembic_upgrade",
        lambda: startup_events.append("alembic_upgrade"),
    )
    monkeypatch.setattr(
        "app.main._register_frameworks",
        lambda: startup_events.append("register_frameworks"),
    )

    def reject_catalog():
        startup_events.append("validate_catalog")
        raise RuntimeError("invalid catalog")

    monkeypatch.setattr("app.main._assert_framework_catalog_complete", reject_catalog)

    async def start_app():
        async with lifespan(None):
            pass

    with pytest.raises(RuntimeError, match="invalid catalog"):
        asyncio.run(start_app())

    assert startup_events == ["alembic_upgrade", "register_frameworks", "validate_catalog"]


def test_lifespan_creates_missing_data_directory_for_default_sqlite_url(monkeypatch, tmp_path):
    """A clean checkout has no `data/` directory. Startup must create the
    parent directory for a file-backed SQLite URL (the default is
    sqlite:///data/dpdpa.db) rather than failing to open the DB file."""
    from app import main

    nested_db_path = tmp_path / "nested" / "does_not_exist_yet" / "app.db"
    assert not nested_db_path.parent.exists()

    monkeypatch.setattr(main.settings, "database_url", f"sqlite:///{nested_db_path}")

    async def start_app():
        async with main.lifespan(None):
            pass

    asyncio.run(start_app())

    assert nested_db_path.exists()


def test_migration_backfills_legacy_gap_item_framework_ids():
    migration_engine = create_engine("sqlite://")
    with migration_engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE gap_items (
                    id TEXT PRIMARY KEY,
                    compliance_status TEXT,
                    gap_description TEXT,
                    risk_level TEXT,
                    ai_compliance_status TEXT,
                    ai_gap_description TEXT,
                    ai_risk_level TEXT,
                    framework_id TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                "INSERT INTO gap_items (id, framework_id) "
                "VALUES ('legacy', NULL), ('iso', 'iso27001')"
            )
        )

    run_column_migrations(migration_engine)

    with migration_engine.connect() as conn:
        rows = dict(
            conn.execute(
                text("SELECT id, framework_id FROM gap_items ORDER BY id")
            ).all()
        )

    assert rows == {"iso": "iso27001", "legacy": "dpdpa"}
    migration_engine.dispose()


# ---------------------------------------------------------------------------
# PR #16 final remediation, matrix item 8: the real FastAPI lifespan (which
# runs `alembic upgrade head`) plus `/health`, against a fresh DB, a valid
# legacy-copy DB, and an invalid mixed-orphan DB that must fail to start.
# ---------------------------------------------------------------------------


def test_lifespan_and_health_against_fresh_database(monkeypatch, tmp_path):
    from app import main

    db_path = tmp_path / "startup_fresh.db"
    monkeypatch.setattr(main.settings, "database_url", f"sqlite:///{db_path}")

    with TestClient(main.app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    engine = create_engine(f"sqlite:///{db_path}")
    try:
        with engine.connect() as conn:
            version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
        assert version == "4e8c1a9d2b57"
    finally:
        engine.dispose()


def test_lifespan_and_health_against_valid_legacy_copy_database(monkeypatch, tmp_path):
    from app import main
    from tests.test_data_integrity import (
        _create_legacy_schema,
        _fresh_engine,
        _insert_legacy_data,
    )

    db_path = tmp_path / "startup_legacy.db"
    seed_engine = _fresh_engine(tmp_path, "startup_legacy.db")
    now_str = datetime.now(timezone.utc).isoformat()

    raw = seed_engine.raw_connection()
    cursor = raw.cursor()
    cursor.execute("PRAGMA foreign_keys=OFF")
    _create_legacy_schema(cursor)
    _insert_legacy_data(cursor, now_str)
    raw.commit()
    cursor.close()
    raw.close()
    seed_engine.dispose()

    monkeypatch.setattr(main.settings, "database_url", f"sqlite:///{db_path}")

    with TestClient(main.app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    engine = create_engine(f"sqlite:///{db_path}")
    try:
        with engine.connect() as conn:
            version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
            assert version == "4e8c1a9d2b57"
            assert conn.execute(text("SELECT COUNT(*) FROM assessments")).scalar() == 1
            fks = conn.execute(text("PRAGMA foreign_key_list(gap_items)")).fetchall()
            assert len(fks) == 1, "legacy gap_items should have been FK-rebuilt on startup"
    finally:
        engine.dispose()


def test_lifespan_fails_startup_on_invalid_mixed_orphan_database(monkeypatch, tmp_path):
    """An invalid legacy database (a non-SET-NULL orphan on a table that
    won't be rebuilt this run) must abort the FastAPI lifespan itself --
    the app must never finish starting, let alone report /health."""
    from app import main
    from tests.test_data_integrity import (
        _create_legacy_schema,
        _fresh_engine,
        _insert_legacy_data,
        _make_fk_declared_gap_reports,
    )

    db_path = tmp_path / "startup_mixed_orphan.db"
    seed_engine = _fresh_engine(tmp_path, "startup_mixed_orphan.db")
    now_str = datetime.now(timezone.utc).isoformat()

    raw = seed_engine.raw_connection()
    cursor = raw.cursor()
    cursor.execute("PRAGMA foreign_keys=OFF")
    _create_legacy_schema(cursor)
    _make_fk_declared_gap_reports(cursor)
    _insert_legacy_data(cursor, now_str)
    cursor.execute(
        "INSERT INTO gap_reports VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("orphan-r", "nonexistent-a", 0.0, "{}", "", "{}", None, None, now_str),
    )
    raw.commit()
    cursor.close()
    raw.close()
    seed_engine.dispose()

    monkeypatch.setattr(main.settings, "database_url", f"sqlite:///{db_path}")

    with pytest.raises(RuntimeError, match="FK migration blocked"):
        with TestClient(main.app):
            pytest.fail("TestClient startup should have raised before yielding control")

    engine = create_engine(f"sqlite:///{db_path}")
    try:
        with engine.connect() as conn:
            tables = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'")
            ).fetchone()
            if tables is not None:
                version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
                assert version != "6fcd9e575309"
    finally:
        engine.dispose()
