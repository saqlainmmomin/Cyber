"""Contract tests for the P1-2 target schema."""

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.models.assessment import Assessment
from app.models.client import Client
from app.models.conclusion import Conclusion
from app.models.engagement import Engagement


REPO_ROOT = Path(__file__).resolve().parents[1]
NEW_TABLES = {
    "clients",
    "engagements",
    "assessment_packs",
    "evidence",
    "evidence_versions",
    "evidence_uses",
    "citations",
    "analysis_runs",
    "conclusions",
    "conclusion_revisions",
    "findings",
    "actions",
    "report_snapshots",
    "magic_links",
    "audit_events",
}


def _alembic_config(db_path: Path) -> Config:
    config = Config(str(REPO_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return config


def _fresh_engine(db_path: Path):
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


@pytest.fixture()
def migrated_db(tmp_path):
    db_path = tmp_path / "target-schema.sqlite3"
    config = _alembic_config(db_path)
    command.upgrade(config, "head")
    engine = _fresh_engine(db_path)
    session = sessionmaker(bind=engine)()
    try:
        yield session, engine, config
    finally:
        session.close()
        engine.dispose()


def test_upgrade_creates_target_tables_and_assessment_columns(migrated_db):
    _session, engine, _config = migrated_db

    table_names = set(inspect(engine).get_table_names()) - {"alembic_version"}
    assert NEW_TABLES <= table_names

    assessment_columns = {
        column["name"] for column in inspect(engine).get_columns("assessments")
    }
    assert {"engagement_id", "version"} <= assessment_columns


@pytest.mark.parametrize(
    ("table", "column", "referred_table"),
    [
        ("engagements", "client_id", "clients"),
        ("assessment_packs", "assessment_id", "assessments"),
        ("evidence", "engagement_id", "engagements"),
        ("evidence_versions", "evidence_id", "evidence"),
        ("evidence_uses", "evidence_id", "evidence"),
        ("evidence_uses", "assessment_id", "assessments"),
        ("citations", "evidence_version_id", "evidence_versions"),
        ("analysis_runs", "assessment_id", "assessments"),
        ("conclusions", "assessment_id", "assessments"),
        ("conclusion_revisions", "conclusion_id", "conclusions"),
        ("findings", "assessment_id", "assessments"),
        ("findings", "conclusion_id", "conclusions"),
        ("actions", "finding_id", "findings"),
        ("report_snapshots", "assessment_id", "assessments"),
        ("report_snapshots", "engagement_id", "engagements"),
        ("magic_links", "engagement_id", "engagements"),
    ],
)
def test_target_foreign_keys_exist(migrated_db, table, column, referred_table):
    _session, engine, _config = migrated_db

    with engine.connect() as connection:
        foreign_keys = connection.execute(text(f"PRAGMA foreign_key_list({table})")).fetchall()

    assert any(
        foreign_key[2] == referred_table and foreign_key[3] == column
        for foreign_key in foreign_keys
    ), f"missing {table}.{column} -> {referred_table} foreign key"


def test_engagement_client_fk_is_restrict(migrated_db):
    _session, engine, _config = migrated_db

    with engine.connect() as connection:
        foreign_keys = connection.execute(text("PRAGMA foreign_key_list(engagements)"))
        client_fk = next(row for row in foreign_keys if row[3] == "client_id")

    assert client_fk[6] == "RESTRICT"


def test_invalid_engagement_client_is_rejected(migrated_db):
    session, _engine, _config = migrated_db

    session.add(
        Engagement(
            client_id="missing-client",
            name="Broken engagement",
            status="draft",
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_client_name_is_unique(migrated_db):
    session, _engine, _config = migrated_db

    session.add_all(
        [
            Client(name="Acme", industry="Technology", size="small"),
            Client(name="Acme", industry="Technology", size="small"),
        ]
    )
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_assessment_engagement_is_nullable_and_versions_default_to_one(migrated_db):
    session, _engine, _config = migrated_db

    assessment = Assessment(
        company_name="LegacyCo",
        industry="Technology",
        company_size="small",
    )
    session.add(assessment)
    session.flush()

    conclusion = Conclusion(
        assessment_id=assessment.id,
        requirement_id="REQ-1",
        framework_id="dpdpa",
        outcome="insufficient_evidence",
        rationale="No evidence supplied",
        evidence_summary="None",
        gaps_identified="Evidence is missing",
        risk_level="medium",
        recommended_action="Provide evidence",
        ai_proposed=False,
    )
    session.add(conclusion)
    session.commit()

    assert assessment.engagement_id is None
    assert assessment.version == 1
    assert conclusion.version == 1


def test_downgrade_removes_only_p1_2_schema_and_upgrade_restores_it(migrated_db):
    _session, engine, config = migrated_db

    command.downgrade(config, "-1")
    with engine.connect() as connection:
        tables = set(inspect(engine).get_table_names()) - {"alembic_version"}
        assessment_columns = {
            row[1]
            for row in connection.execute(text("PRAGMA table_info(assessments)"))
        }

    assert NEW_TABLES.isdisjoint(tables)
    assert {"engagement_id", "version"}.isdisjoint(assessment_columns)
    assert {"assessments", "questionnaire_responses", "gap_reports"} <= tables

    command.upgrade(config, "head")
    restored_tables = set(inspect(engine).get_table_names()) - {"alembic_version"}
    restored_columns = {
        column["name"] for column in inspect(engine).get_columns("assessments")
    }
    assert NEW_TABLES <= restored_tables
    assert {"engagement_id", "version"} <= restored_columns
