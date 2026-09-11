import asyncio

import pytest
from sqlalchemy import create_engine, text

from app.main import (
    _assert_framework_catalog_complete,
    _register_frameworks,
    _run_migrations,
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
        "app.main.Base.metadata.create_all",
        lambda bind: startup_events.append("create_all"),
    )
    monkeypatch.setattr(
        "app.main._register_frameworks",
        lambda: startup_events.append("register_frameworks"),
    )

    def reject_catalog():
        startup_events.append("validate_catalog")
        raise RuntimeError("invalid catalog")

    monkeypatch.setattr("app.main._assert_framework_catalog_complete", reject_catalog)
    monkeypatch.setattr(
        "app.main._run_migrations",
        lambda migration_engine: startup_events.append("run_migrations"),
    )

    async def start_app():
        async with lifespan(None):
            pass

    with pytest.raises(RuntimeError, match="invalid catalog"):
        asyncio.run(start_app())

    assert startup_events == ["create_all", "register_frameworks", "validate_catalog"]


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

    _run_migrations(migration_engine)

    with migration_engine.connect() as conn:
        rows = dict(
            conn.execute(
                text("SELECT id, framework_id FROM gap_items ORDER BY id")
            ).all()
        )

    assert rows == {"iso": "iso27001", "legacy": "dpdpa"}
    migration_engine.dispose()
