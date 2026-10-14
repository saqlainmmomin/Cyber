"""Characterize the explicit-framework migration on isolated legacy data."""
import json

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text

from app.models.assessment import Assessment

REVISION = "e2c8f6a4d901"
PARENT = "b7d41c9e2a63"


def _config(path):
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", f"sqlite:///{path}")
    return config


def _legacy(tmp_path, frameworks=None):
    path = tmp_path / "legacy.sqlite3"
    config = _config(path)
    command.upgrade(config, PARENT)
    engine = create_engine(f"sqlite:///{path}")
    with engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO assessments (id, company_name, industry, company_size, status, "
            "selected_frameworks, created_at, updated_at, version) VALUES "
            "('a', 'Legacy', 'Technology', 'small', 'created', :frameworks, "
            "CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1)"
        ), {"frameworks": frameworks})
        conn.execute(text(
            "INSERT INTO desk_review_findings "
            "(assessment_id, finding_type, content, severity, created_at) "
            "VALUES ('a', 'evidence', 'quote', 'info', CURRENT_TIMESTAMP)"
        ))
        conn.execute(text(
            "INSERT INTO gap_reports (id, assessment_id, overall_score, chapter_scores, "
            "executive_summary, raw_ai_response, generated_at) "
            "VALUES ('r', 'a', 0, '{}', 'summary', '{}', CURRENT_TIMESTAMP)"
        ))
        conn.execute(text(
            "INSERT INTO gap_items (id, report_id, requirement_id, chapter, requirement_title, "
            "compliance_status, current_state, gap_description, risk_level, remediation_action, "
            "remediation_priority, remediation_effort, timeline_weeks) "
            "VALUES ('g', 'r', 'CH2.CONSENT.1', 'ch2', 'Consent', 'non_compliant', "
            "'', '', 'high', '', 1, 'low', 1)"
        ))
    return config, engine


def _migration(config):
    return ScriptDirectory.from_config(config).get_revision(REVISION).module


@pytest.mark.parametrize("stored", [None, '["dpdpa"]', '["iso27001", "dpdpa"]'])
def test_backfill_only_with_dpdpa_provenance(tmp_path, stored):
    config, engine = _legacy(tmp_path, stored)
    try:
        with engine.connect() as conn:
            counts = _migration(config).preflight(conn)
        assert counts["assessments"]["null"] == (stored is None)
        assert counts["desk_review_findings"] == {"null": 1, "ambiguous": 0}
        assert counts["gap_items"] == {"null": 1, "ambiguous": 0}
        command.upgrade(config, REVISION)
        with engine.connect() as conn:
            assert json.loads(conn.scalar(text("SELECT selected_frameworks FROM assessments"))) == (
                json.loads(stored) if stored is not None else ["dpdpa"]
            )
            assert conn.scalar(text("SELECT framework_id FROM desk_review_findings")) == "dpdpa"
            assert conn.scalar(text("SELECT framework_id FROM gap_items")) == "dpdpa"
        command.downgrade(config, PARENT)
        with engine.connect() as conn:
            assert conn.scalar(text("SELECT version_num FROM alembic_version")) == PARENT
            assert json.loads(conn.scalar(text("SELECT selected_frameworks FROM assessments"))) == (
                json.loads(stored) if stored is not None else ["dpdpa"]
            )
            assert conn.scalar(text("SELECT framework_id FROM desk_review_findings")) == "dpdpa"
            assert conn.scalar(text("SELECT framework_id FROM gap_items")) == "dpdpa"
    finally:
        engine.dispose()


@pytest.mark.parametrize("stored, rule", [
    ("not json", "invalid_json"), ('"dpdpa"', "non_list"), ("[]", "empty_list"),
    ('["unknown"]', "unknown_id"), ('[null]', "unknown_id"),
])
def test_invalid_selections_refuse_without_backfill(tmp_path, stored, rule):
    config, engine = _legacy(tmp_path, stored)
    try:
        with engine.connect() as conn:
            counts = _migration(config).preflight(conn)
        assert counts["assessments"][rule] == 1
        with pytest.raises(RuntimeError, match=rule):
            command.upgrade(config, REVISION)
        with engine.connect() as conn:
            assert conn.scalar(text("SELECT selected_frameworks FROM assessments")) == stored
            assert conn.scalar(text("SELECT framework_id FROM desk_review_findings")) is None
            assert conn.scalar(text("SELECT framework_id FROM gap_items")) is None
    finally:
        engine.dispose()


def test_non_dpdpa_null_rows_are_ambiguous(tmp_path):
    config, engine = _legacy(tmp_path, '["iso27001"]')
    try:
        with engine.connect() as conn:
            counts = _migration(config).preflight(conn)
        assert counts["desk_review_findings"] == {"null": 1, "ambiguous": 1}
        assert counts["gap_items"] == {"null": 1, "ambiguous": 1}
        with pytest.raises(RuntimeError, match='"ambiguous": 1'):
            command.upgrade(config, REVISION)
        with engine.connect() as conn:
            assert conn.scalar(text("SELECT framework_id FROM desk_review_findings")) is None
            assert conn.scalar(text("SELECT framework_id FROM gap_items")) is None
    finally:
        engine.dispose()


@pytest.mark.parametrize("stored", [None, "invalid", "[]", '"dpdpa"'])
def test_frameworks_requires_explicit_storage(stored):
    assessment = Assessment()
    assessment.__dict__["selected_frameworks"] = stored
    with pytest.raises(ValueError):
        _ = assessment.frameworks
