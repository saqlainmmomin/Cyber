from sqlalchemy import create_engine, text

from app.main import (
    _assert_framework_catalog_complete,
    _register_frameworks,
    _run_migrations,
)


def test_framework_catalog_matches_registered_frameworks(monkeypatch):
    _register_frameworks()
    _assert_framework_catalog_complete()

    monkeypatch.setattr(
        "app.routers.web.ROADMAP_FRAMEWORKS",
        ("gdpr", "hipaa"),
    )

    try:
        _assert_framework_catalog_complete()
    except AssertionError as exc:
        assert "pci_dss" in str(exc)
    else:
        raise AssertionError("registry drift should fail the startup assertion")


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
