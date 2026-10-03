"""Contract tests for P6-8 V3-A: consultant-entered data for the v3 board deck.

Handoff: tasks/handoffs/2026-10-01-board-report-v3-deck.md (D-P6-8-V3-A..F, K).
Decision doc: docs/product/2026-10-01-board-report-format.md (F4, F5, F10, section 7).
Written before the implementation; on `main` they fail only because the code does not
exist yet. V3-A captures data only: it never changes the board-report document, the
schema version, the report template or the exporters (those are V3-B). No network, no LLM.
"""

from __future__ import annotations

import hashlib
import importlib
import inspect
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest
from alembic import command
from alembic.script import ScriptDirectory
from pydantic import ValidationError
from sqlalchemy import MetaData, create_engine, inspect as sa_inspect, text

from app.main import app
from app.models.action import Action
from app.models.assessment import Assessment
from app.models.audit_event import AuditEvent
from app.models.conclusion import Conclusion, ConclusionRevision
from app.models.finding import Finding
from tests.p6_8_v3_support import (  # noqa: F401 - fixtures are used by name
    DEFAULT_THEME,
    DISPLAY_FONT_SHA256,
    DISPLAY_LICENSE_FILES,
    PREVIOUS_REVISION,
    REPO_ROOT,
    REVIEWER,
    V3A_REVISION,
    _alembic_config,
    _document,
    _no_llm,
    _register_frameworks,
    db,
    db_path,
    engine,
    events,
    findings_and_actions,
    fixture_assessment,
    gate,
    git,
    http,
    metadata,
    roadmap_groups,
    upload_root,
)
from tests.p6_8_v3a_paths import V3A_APP_PATHS
from tests.yozora_backend_paths import YOZORA_BACKEND_APP_PATHS, YOZORA_BACKEND_EXCLUDES, YOZORA_BACKEND_FILES  # Yozora backend per-PR allowance
from tests.yozora_paths import YOZORA_EXCLUDES, YOZORA_S1_PATHS  # Yozora S1 per-PR allowance
from tests.test_p6_8_board_report_v2 import _require_renderer

YOZORA_REVISION = "b7d41c9e2a63"  # Yozora backend features (tasks/handoffs/2026-10-03-yozora-backend-features.md)

ACTOR = f"consultant:{REVIEWER}"
FONT_DIR = REPO_ROOT / "app" / "assets" / "fonts" / "noto"
NOTO_FILES = {
    "NotoSans-Regular.ttf", "NotoSans-Bold.ttf",
    "NotoSansDevanagari-Regular.ttf", "NotoSansDevanagari-Bold.ttf",
}


def _bi():
    return importlib.import_module("app.services.board_inputs")


# ---------------------------------------------------------------------------
# 1. Migration: columns, table, data kept, reversible, refuses to lose data
# ---------------------------------------------------------------------------


def _insert_minimal(connection, table_name: str, **values) -> None:
    """Insert one row, filling every other NOT NULL column with a type-appropriate dummy."""
    metadata_ = MetaData()
    metadata_.reflect(bind=connection, only=[table_name])
    table = metadata_.tables[table_name]
    row = dict(values)
    for column in table.columns:
        if column.name in row or column.nullable:
            continue
        kind = str(column.type).upper()
        if "INT" in kind or "BOOL" in kind:
            row[column.name] = 1
        elif "DATETIME" in kind or "TIMESTAMP" in kind:
            row[column.name] = datetime.now(timezone.utc)
        elif "FLOAT" in kind or "NUMERIC" in kind:
            row[column.name] = 1.0
        else:
            row[column.name] = "x"
    connection.execute(table.insert().values(**row))


def _columns(path: Path, table: str) -> dict[str, tuple[str, bool]]:
    with sqlite3.connect(path) as connection:
        return {
            row[1]: (row[2].upper(), not row[3])
            for row in connection.execute(f"PRAGMA table_info({table})")
        }


def _tables(path: Path) -> set[str]:
    with sqlite3.connect(path) as connection:
        return {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def test_scenario_1_migration_adds_the_columns_and_table_keeps_data_and_is_reversible(tmp_path):
    """D-P6-8-V3-B: one new revision on 8b2d5f7e1c34; nullable columns, one new table, data kept."""
    path = tmp_path / "v3a.sqlite3"
    config = _alembic_config(path)
    scripts = ScriptDirectory.from_config(config)
    assert scripts.get_current_head() == YOZORA_REVISION  # Yozora backend features sits on V3-A
    assert scripts.get_revision(YOZORA_REVISION).down_revision == V3A_REVISION
    assert scripts.get_revision(V3A_REVISION).down_revision == PREVIOUS_REVISION

    command.upgrade(config, PREVIOUS_REVISION)
    assert "initiative_metadata" not in _tables(path)
    engine = create_engine(f"sqlite:///{path}")
    with engine.begin() as connection:  # foreign keys are off on a raw connection: fixture rows only
        _insert_minimal(connection, "assessments", id="a1", company_name="Acme")
        _insert_minimal(connection, "findings", id="f1", assessment_id="a1", title="Kept finding")
        _insert_minimal(connection, "actions", id="x1", finding_id="f1", title="Kept action", owner="Anita")
    engine.dispose()

    command.upgrade(config, "head")
    assert _columns(path, "findings")["business_impact"] == ("TEXT", True)
    assert _columns(path, "findings")["recommendation"] == ("TEXT", True)
    responsibility = _columns(path, "actions")["responsibility"]
    assert responsibility[0].startswith("VARCHAR") and responsibility[1] is True
    assert _columns(path, "assessments")["board_asks_json"] == ("TEXT", True)
    initiative = _columns(path, "initiative_metadata")
    assert set(initiative) == {
        "id", "assessment_id", "group_id", "title", "complexity", "benefit", "created_at", "updated_at",
    }
    assert initiative["title"][1] and initiative["complexity"][1] and initiative["benefit"][1]  # nullable
    assert not initiative["assessment_id"][1] and not initiative["group_id"][1]  # NOT NULL
    with sqlite3.connect(path) as connection:
        assert connection.execute(
            "SELECT title, business_impact, recommendation FROM findings WHERE id='f1'"
        ).fetchone() == ("Kept finding", None, None)
        assert connection.execute(
            "SELECT title, owner, responsibility FROM actions WHERE id='x1'"
        ).fetchone() == ("Kept action", "Anita", None)
        assert connection.execute("SELECT board_asks_json FROM assessments WHERE id='a1'").fetchone() == (None,)
        assert connection.execute("SELECT version_num FROM alembic_version").fetchone() == (YOZORA_REVISION,)
        # One metadata row per (assessment, group): a second insert with the same pair is refused.
        connection.execute(
            "INSERT INTO initiative_metadata (id, assessment_id, group_id, created_at, updated_at) "
            "VALUES ('i1', 'a1', 'G1', '2026-10-01', '2026-10-01')"
        )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO initiative_metadata (id, assessment_id, group_id, created_at, updated_at) "
                "VALUES ('i2', 'a1', 'G1', '2026-10-01', '2026-10-01')"
            )
        connection.rollback()

    command.downgrade(config, PREVIOUS_REVISION)  # nothing consultant-entered yet: reversible
    assert "initiative_metadata" not in _tables(path)
    assert "business_impact" not in _columns(path, "findings")
    assert "recommendation" not in _columns(path, "findings")
    assert "responsibility" not in _columns(path, "actions")
    assert "board_asks_json" not in _columns(path, "assessments")
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT title FROM findings WHERE id='f1'").fetchone() == ("Kept finding",)
        assert connection.execute("SELECT owner FROM actions WHERE id='x1'").fetchone() == ("Anita",)
    command.upgrade(config, "head")  # and upgradable again
    assert "initiative_metadata" in _tables(path)


@pytest.mark.parametrize(
    "statement",
    [
        "UPDATE findings SET business_impact = 'Why it matters' WHERE id = 'f1'",
        "UPDATE findings SET recommendation = 'Do this' WHERE id = 'f1'",
        "UPDATE actions SET responsibility = 'client' WHERE id = 'x1'",
        "UPDATE assessments SET board_asks_json = '{\"asks\": [\"Approve\"]}' WHERE id = 'a1'",
        "INSERT INTO initiative_metadata (id, assessment_id, group_id, title, created_at, updated_at) "
        "VALUES ('i1', 'a1', 'G1', 'Title', '2026-10-01', '2026-10-01')",
    ],
    ids=["business_impact", "recommendation", "responsibility", "board_asks", "initiative_metadata"],
)
def test_scenario_1b_downgrade_refuses_to_drop_consultant_entered_data(tmp_path, statement):
    """D-P6-8-V3-B: like P5-3, a downgrade that would lose consultant-entered text refuses and changes nothing."""
    path = tmp_path / "v3a-data.sqlite3"
    config = _alembic_config(path)
    command.upgrade(config, "head")
    engine = create_engine(f"sqlite:///{path}")
    with engine.begin() as connection:
        _insert_minimal(connection, "assessments", id="a1", company_name="Acme")
        _insert_minimal(connection, "findings", id="f1", assessment_id="a1", title="Finding")
        _insert_minimal(connection, "actions", id="x1", finding_id="f1", title="Action")
        connection.execute(text(statement))
    engine.dispose()

    command.downgrade(config, V3A_REVISION)  # the Yozora revision above holds no consultant data here
    with pytest.raises(RuntimeError, match="Refusing to downgrade past"):
        command.downgrade(config, PREVIOUS_REVISION)
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT version_num FROM alembic_version").fetchone() == (V3A_REVISION,)
    assert "initiative_metadata" in _tables(path)
    assert "business_impact" in _columns(path, "findings")


# ---------------------------------------------------------------------------
# 2. Models
# ---------------------------------------------------------------------------


def test_scenario_2_models_expose_the_new_fields():
    """D-P6-8-V3-B: nullable model fields and the InitiativeMetadata model, registered with the others."""
    import app.models as models
    from app.database import Base

    assert models.InitiativeMetadata.__tablename__ == "initiative_metadata"
    assert "InitiativeMetadata" in models.__all__
    assert models.InitiativeMetadata.__table__ is Base.metadata.tables["initiative_metadata"]
    for model, name in (
        (Finding, "business_impact"), (Finding, "recommendation"),
        (Action, "responsibility"), (Assessment, "board_asks_json"),
    ):
        column = sa_inspect(model).columns[name]
        assert column.nullable, (model, name)
    assert sa_inspect(Finding).columns["business_impact"].type.__class__.__name__ == "Text"
    assert sa_inspect(Finding).columns["recommendation"].type.__class__.__name__ == "Text"
    assert sa_inspect(Action).columns["responsibility"].type.length == 20
    table = models.InitiativeMetadata.__table__
    assert {column.name for column in table.columns} == {
        "id", "assessment_id", "group_id", "title", "complexity", "benefit", "created_at", "updated_at",
    }
    assert {fk.target_fullname for fk in table.columns["assessment_id"].foreign_keys} == {"assessments.id"}
    uniques = [
        tuple(column.name for column in constraint.columns)
        for constraint in table.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    ] + [tuple(column.name for column in index.columns) for index in table.indexes if index.unique]
    assert ("assessment_id", "group_id") in uniques


# ---------------------------------------------------------------------------
# 3. Service contract
# ---------------------------------------------------------------------------


def test_scenario_3_service_contract_constants_and_signatures():
    """D-P6-8-V3-C: names, limits, messages and signatures are fixed by the handoff."""
    service = _bi()
    assert service.RESPONSIBILITIES == ("client", "consultant", "shared")
    assert service.LEVELS == ("high", "medium", "low")
    assert service.MAX_BUSINESS_IMPACT == 1200
    assert service.MAX_RECOMMENDATION == 1500
    assert service.MAX_INITIATIVE_TITLE == 120
    assert service.MAX_ASKS == 3
    assert service.MAX_ASK_CHARS == 400
    assert service.FINDING_NOT_FOUND == "Finding not found"
    assert service.ACTION_NOT_FOUND == "Action not found"
    assert service.GROUP_NOT_FOUND == "Remediation group not found"
    assert service.ASSESSMENT_NOT_FOUND == "Assessment not found"
    assert service.INVALID_RESPONSIBILITY == "Responsibility must be client, consultant or shared."
    assert service.INVALID_LEVEL == "Complexity and benefit must be high, medium or low."
    assert service.TOO_MANY_ASKS == "A report can carry at most 3 board decisions."
    assert service.TEXT_TOO_LONG == "{label} must be {limit} characters or fewer."
    assert service.NO_CHANGES == "No changes to save."
    assert service.AUDIT_FINDING == "finding.board_fields_updated"
    assert service.AUDIT_ACTION == "action.responsibility_updated"
    assert service.AUDIT_INITIATIVE == "initiative.metadata_updated"
    assert service.AUDIT_ASKS == "assessment.board_asks_updated"
    assert issubclass(service.BoardInputNotFound, service.BoardInputError)
    assert issubclass(service.InvalidBoardInput, service.BoardInputError)
    assert service.BoardInputNotFound.status_code == 404 and service.InvalidBoardInput.status_code == 400
    expected = {
        "update_finding_fields": ["db", "assessment_id", "finding_id", "business_impact", "recommendation", "actor"],
        "update_action_responsibility": ["db", "assessment_id", "action_id", "responsibility", "actor"],
        "update_initiative": ["db", "assessment_id", "group_id", "title", "complexity", "benefit", "actor"],
        "update_board_asks": ["db", "assessment_id", "asks", "actor"],
    }
    for name, parameters in expected.items():
        assert list(inspect.signature(getattr(service, name)).parameters) == parameters, name
    for name in ("board_asks", "initiative_metadata"):
        assert callable(getattr(service, name)), name
    source = inspect.getsource(service)
    assert ".commit(" not in source, "the routes commit; the service never does"
    for token in ("llm_client", "call_llm", "openai", "anthropic"):
        assert token not in source, token


# ---------------------------------------------------------------------------
# 4-7. Service behaviour
# ---------------------------------------------------------------------------


def test_scenario_4_finding_fields_are_trimmed_validated_cleared_and_audited(db, fixture_assessment):
    """D-P6-8-V3-C: "Why it matters" and "Recommendation" on a Finding (F4)."""
    service = _bi()
    assessment = fixture_assessment
    finding = findings_and_actions(db, assessment)[0][0]
    assert finding.business_impact is None and finding.recommendation is None
    title, description, severity, priority, status = (
        finding.title, finding.description, finding.severity, finding.priority, finding.status,
    )

    service.update_finding_fields(
        db, assessment_id=assessment.id, finding_id=finding.id,
        business_impact="  Consent  is invalid.\r\nSecond line  ", recommendation="Replace the pre-ticked box.", actor=ACTOR,
    )
    assert finding.business_impact == "Consent  is invalid.\nSecond line"  # trimmed, CRLF -> LF, inner spacing kept
    assert finding.recommendation == "Replace the pre-ticked box."
    (event,) = events(db, "finding.board_fields_updated", finding.id)
    assert event.actor == ACTOR and event.entity_type == "finding"
    assert metadata(event) == {
        "assessment_id": assessment.id,
        "changes": {
            "business_impact": {"from": None, "to": "Consent  is invalid.\nSecond line"},
            "recommendation": {"from": None, "to": "Replace the pre-ticked box."},
        },
    }

    # Saving the same values again is a no-op: no new event.
    service.update_finding_fields(
        db, assessment_id=assessment.id, finding_id=finding.id,
        business_impact="Consent  is invalid.\nSecond line", recommendation="Replace the pre-ticked box.", actor=ACTOR,
    )
    assert len(events(db, "finding.board_fields_updated", finding.id)) == 1

    # One field changed, one cleared by blank text: only the changed fields are recorded.
    service.update_finding_fields(
        db, assessment_id=assessment.id, finding_id=finding.id,
        business_impact="   ", recommendation="Replace the pre-ticked box and log consent.", actor=ACTOR,
    )
    assert finding.business_impact is None
    second = events(db, "finding.board_fields_updated", finding.id)[-1]
    assert metadata(second)["changes"] == {
        "business_impact": {"from": "Consent  is invalid.\nSecond line", "to": None},
        "recommendation": {
            "from": "Replace the pre-ticked box.", "to": "Replace the pre-ticked box and log consent.",
        },
    }

    # Limits and unknown ids write nothing.
    before = len(events(db, "finding.board_fields_updated"))
    with pytest.raises(service.InvalidBoardInput) as long_text:
        service.update_finding_fields(
            db, assessment_id=assessment.id, finding_id=finding.id,
            business_impact="x" * (service.MAX_BUSINESS_IMPACT + 1), recommendation=None, actor=ACTOR,
        )
    assert long_text.value.message == service.TEXT_TOO_LONG.format(label="Why it matters", limit=1200)
    with pytest.raises(service.InvalidBoardInput) as long_reco:
        service.update_finding_fields(
            db, assessment_id=assessment.id, finding_id=finding.id,
            business_impact=None, recommendation="x" * (service.MAX_RECOMMENDATION + 1), actor=ACTOR,
        )
    assert long_reco.value.message == service.TEXT_TOO_LONG.format(label="Recommendation", limit=1500)
    for bad_assessment, bad_finding in (
        (assessment.id, "no-such-finding"), ("another-assessment", finding.id),
    ):
        with pytest.raises(service.BoardInputNotFound) as missing:
            service.update_finding_fields(
                db, assessment_id=bad_assessment, finding_id=bad_finding,
                business_impact="x", recommendation="y", actor=ACTOR,
            )
        assert missing.value.message == service.FINDING_NOT_FOUND
    assert len(events(db, "finding.board_fields_updated")) == before
    assert finding.recommendation == "Replace the pre-ticked box and log consent."

    # Nothing else on the Finding moved (it is the approved, write-once part).
    assert (finding.title, finding.description, finding.severity, finding.priority, finding.status) == (
        title, description, severity, priority, status,
    )
    # The service never commits: a rollback discards the edit.
    db.rollback()
    db.refresh(finding)
    assert finding.business_impact is None and finding.recommendation is None


def test_scenario_5_action_responsibility_is_a_closed_set_and_audited(db, fixture_assessment):
    """D-P6-8-V3-C: Action.responsibility is client / consultant / shared; blank clears it (F4)."""
    service = _bi()
    assessment = fixture_assessment
    findings, actions = findings_and_actions(db, assessment)
    action = actions[findings[0].id][0]
    history, status, owner, title = action.history_json, action.status, action.owner, action.title
    assert action.responsibility is None

    service.update_action_responsibility(
        db, assessment_id=assessment.id, action_id=action.id, responsibility="  Client ", actor=ACTOR
    )
    assert action.responsibility == "client"  # trimmed and lower-cased
    (event,) = events(db, "action.responsibility_updated", action.id)
    assert event.entity_type == "action" and event.actor == ACTOR
    assert metadata(event) == {
        "assessment_id": assessment.id, "finding_id": findings[0].id, "from": None, "to": "client",
    }
    service.update_action_responsibility(
        db, assessment_id=assessment.id, action_id=action.id, responsibility="client", actor=ACTOR
    )
    assert len(events(db, "action.responsibility_updated", action.id)) == 1  # no-op, no event
    for value in service.RESPONSIBILITIES:
        service.update_action_responsibility(
            db, assessment_id=assessment.id, action_id=action.id, responsibility=value, actor=ACTOR
        )
        assert action.responsibility == value
    service.update_action_responsibility(
        db, assessment_id=assessment.id, action_id=action.id, responsibility="", actor=ACTOR
    )
    assert action.responsibility is None
    assert metadata(events(db, "action.responsibility_updated", action.id)[-1])["to"] is None

    count = len(events(db, "action.responsibility_updated"))
    with pytest.raises(service.InvalidBoardInput) as invalid:
        service.update_action_responsibility(
            db, assessment_id=assessment.id, action_id=action.id, responsibility="auditor", actor=ACTOR
        )
    assert invalid.value.message == service.INVALID_RESPONSIBILITY
    for bad_assessment, bad_action in ((assessment.id, "no-such-action"), ("another-assessment", action.id)):
        with pytest.raises(service.BoardInputNotFound) as missing:
            service.update_action_responsibility(
                db, assessment_id=bad_assessment, action_id=bad_action, responsibility="client", actor=ACTOR
            )
        assert missing.value.message == service.ACTION_NOT_FOUND
    assert len(events(db, "action.responsibility_updated")) == count

    # Responsibility is not workflow: the action's history, status and details are untouched.
    assert (action.history_json, action.status, action.owner, action.title) == (history, status, owner, title)


def test_scenario_6_initiative_metadata_is_keyed_by_assessment_and_roadmap_group(db, fixture_assessment):
    """D-P6-8-V3-C: title, complexity, benefit per roadmap group (F4); priority is never stored (F10)."""
    from app.models import InitiativeMetadata

    service = _bi()
    assessment = fixture_assessment
    groups = roadmap_groups(db, assessment)
    assert groups, "the fixture has approved findings with actions"
    group_id = groups[0]["group_id"]
    assert service.initiative_metadata(db, assessment.id) == {}

    row = service.update_initiative(
        db, assessment_id=assessment.id, group_id=group_id,
        title="  Rebuild consent capture  ", complexity=" High ", benefit="medium", actor=ACTOR,
    )
    assert (row.title, row.complexity, row.benefit) == ("Rebuild consent capture", "high", "medium")
    assert row.assessment_id == assessment.id and row.group_id == group_id
    (event,) = events(db, "initiative.metadata_updated", row.id)
    assert event.entity_type == "initiative_metadata"
    assert metadata(event) == {
        "assessment_id": assessment.id, "group_id": group_id,
        "changes": {
            "title": {"from": None, "to": "Rebuild consent capture"},
            "complexity": {"from": None, "to": "high"},
            "benefit": {"from": None, "to": "medium"},
        },
    }
    assert service.initiative_metadata(db, assessment.id) == {
        group_id: {"title": "Rebuild consent capture", "complexity": "high", "benefit": "medium"}
    }

    again = service.update_initiative(
        db, assessment_id=assessment.id, group_id=group_id,
        title="Rebuild consent capture", complexity="low", benefit="medium", actor=ACTOR,
    )
    assert again.id == row.id and db.query(InitiativeMetadata).count() == 1  # upsert, not a second row
    assert metadata(events(db, "initiative.metadata_updated", row.id)[-1])["changes"] == {
        "complexity": {"from": "high", "to": "low"}
    }
    service.update_initiative(
        db, assessment_id=assessment.id, group_id=group_id,
        title="Rebuild consent capture", complexity="low", benefit="medium", actor=ACTOR,
    )
    assert len(events(db, "initiative.metadata_updated", row.id)) == 2  # no-op, no event

    service.update_initiative(
        db, assessment_id=assessment.id, group_id=group_id, title="", complexity="", benefit="", actor=ACTOR
    )
    assert db.query(InitiativeMetadata).count() == 1  # the row is kept, with NULLs, so history stays simple
    assert (row.title, row.complexity, row.benefit) == (None, None, None)

    count = len(events(db, "initiative.metadata_updated"))
    with pytest.raises(service.InvalidBoardInput) as level:
        service.update_initiative(
            db, assessment_id=assessment.id, group_id=group_id, title="T", complexity="extreme", benefit="low", actor=ACTOR
        )
    assert level.value.message == service.INVALID_LEVEL
    with pytest.raises(service.InvalidBoardInput) as long_title:
        service.update_initiative(
            db, assessment_id=assessment.id, group_id=group_id,
            title="x" * (service.MAX_INITIATIVE_TITLE + 1), complexity="low", benefit="low", actor=ACTOR,
        )
    assert long_title.value.message == service.TEXT_TOO_LONG.format(label="Initiative title", limit=120)
    for bad_assessment, bad_group, message in (
        (assessment.id, "NOT-A-GROUP", service.GROUP_NOT_FOUND),
        ("another-assessment", group_id, service.ASSESSMENT_NOT_FOUND),
    ):
        with pytest.raises(service.BoardInputNotFound) as missing:
            service.update_initiative(
                db, assessment_id=bad_assessment, group_id=bad_group, title="T", complexity="low", benefit="low", actor=ACTOR
            )
        assert missing.value.message == message
    assert len(events(db, "initiative.metadata_updated")) == count
    assert db.query(InitiativeMetadata).count() == 1


def test_scenario_7_board_asks_are_at_most_three_short_consultant_entered_decisions(db, fixture_assessment):
    """D-P6-8-V3-C: assessments.board_asks_json holds up to 3 asks and who entered them (F4)."""
    service = _bi()
    assessment = fixture_assessment
    assert assessment.board_asks_json is None
    assert service.board_asks(assessment) == {"consultant": [], "consultant_by": None}

    result = service.update_board_asks(
        db, assessment_id=assessment.id,
        asks=["  Approve funding for consent tooling ", "", "Confirm the CISO as accountable owner  "], actor=ACTOR,
    )
    assert result == {"consultant": ["Approve funding for consent tooling", "Confirm the CISO as accountable owner"],
                      "consultant_by": REVIEWER}
    assert json.loads(assessment.board_asks_json) == {
        "asks": ["Approve funding for consent tooling", "Confirm the CISO as accountable owner"],
        "by": REVIEWER,
    }
    assert service.board_asks(assessment) == result
    (event,) = events(db, "assessment.board_asks_updated", assessment.id)
    assert event.entity_type == "assessment" and event.actor == ACTOR
    assert metadata(event) == {"from": [], "to": result["consultant"]}

    service.update_board_asks(db, assessment_id=assessment.id, asks=result["consultant"], actor=ACTOR)
    assert len(events(db, "assessment.board_asks_updated", assessment.id)) == 1  # identical: no event

    count = len(events(db, "assessment.board_asks_updated"))
    with pytest.raises(service.InvalidBoardInput) as many:
        service.update_board_asks(db, assessment_id=assessment.id, asks=["a", "b", "c", "d"], actor=ACTOR)
    assert many.value.message == service.TOO_MANY_ASKS
    with pytest.raises(service.InvalidBoardInput) as long_ask:
        service.update_board_asks(
            db, assessment_id=assessment.id, asks=["x" * (service.MAX_ASK_CHARS + 1)], actor=ACTOR
        )
    assert long_ask.value.message == service.TEXT_TOO_LONG.format(label="Board decision", limit=400)
    with pytest.raises(service.BoardInputNotFound) as no_assessment:
        service.update_board_asks(db, assessment_id="no-such-assessment", asks=["a"], actor=ACTOR)
    assert no_assessment.value.message == service.ASSESSMENT_NOT_FOUND
    assert len(events(db, "assessment.board_asks_updated")) == count
    assert service.board_asks(assessment) == result  # refusals changed nothing

    service.update_board_asks(db, assessment_id=assessment.id, asks=["", "  "], actor=ACTOR)
    assert assessment.board_asks_json is None
    assert service.board_asks(assessment) == {"consultant": [], "consultant_by": None}
    assert metadata(events(db, "assessment.board_asks_updated", assessment.id)[-1]) == {
        "from": result["consultant"], "to": [],
    }


# ---------------------------------------------------------------------------
# 8. Routes and the page
# ---------------------------------------------------------------------------

BOARD_ROUTES = {
    ("GET", "/assessments/{assessment_id}/board-inputs"),
    ("POST", "/api/assessments/{assessment_id}/board-inputs/observations/{finding_id}"),
    ("POST", "/api/assessments/{assessment_id}/board-inputs/actions/{action_id}/responsibility"),
    ("POST", "/api/assessments/{assessment_id}/board-inputs/initiatives"),
    ("POST", "/api/assessments/{assessment_id}/board-inputs/asks"),
}


def _post(http, path, **fields):
    return http.post(path, data={"reviewer_name": REVIEWER, **fields})


def test_scenario_8_routes_are_exactly_these_and_guarded_against_archived_engagements():
    """D-P6-8-V3-D: five routes; none contains /findings, /conclusions, /remediation or /snapshots."""
    from app.routers import retention as retention_router

    actual = {
        (method, route.path)
        for route in app.routes
        if "board-inputs" in route.path
        for method in route.methods
        if method in {"GET", "POST", "PUT", "PATCH", "DELETE"}
    }
    assert actual == BOARD_ROUTES
    for path in (route for _, route in BOARD_ROUTES):
        for pinned in ("/findings", "/conclusions", "/remediation", "/snapshots", "/workpaper"):
            assert pinned not in path, (path, pinned)
    for route in app.routes:
        if "board-inputs" in route.path and "POST" in route.methods:
            calls = [dependency.call for dependency in route.dependant.dependencies]
            assert retention_router.archive_write_guard in calls, route.path


def test_scenario_8b_forms_save_audit_and_report_errors(db, http, fixture_assessment):
    """D-P6-8-V3-D: every form posts to its route; success is a toast, a refusal changes nothing."""
    assessment = fixture_assessment
    findings, actions = findings_and_actions(db, assessment)
    finding, action = findings[0], actions[findings[0].id][0]
    group_id = roadmap_groups(db, assessment)[0]["group_id"]
    base = f"/api/assessments/{assessment.id}/board-inputs"

    saved = _post(
        http, f"{base}/observations/{finding.id}",
        business_impact="Consent is not valid.", recommendation="Use an unticked opt-in.",
    )
    assert saved.status_code == 200, saved.text
    assert saved.json() == {"status": "saved", "changed": True}
    assert saved.headers["X-Toast-Type"] == "success"
    db.expire_all()
    stored = db.get(Finding, finding.id)
    assert (stored.business_impact, stored.recommendation) == ("Consent is not valid.", "Use an unticked opt-in.")
    (event,) = events(db, "finding.board_fields_updated", finding.id)
    assert event.actor == ACTOR

    unchanged = _post(
        http, f"{base}/observations/{finding.id}",
        business_impact="Consent is not valid.", recommendation="Use an unticked opt-in.",
    )
    assert unchanged.status_code == 200 and unchanged.json() == {"status": "saved", "changed": False}
    assert len(events(db, "finding.board_fields_updated", finding.id)) == 1

    shared = _post(http, f"{base}/actions/{action.id}/responsibility", responsibility="shared")
    assert shared.status_code == 200 and shared.json() == {"status": "saved", "changed": True}
    initiative = _post(
        http, f"{base}/initiatives", group_id=group_id, title="Rebuild consent", complexity="high", benefit="high"
    )
    assert initiative.status_code == 200 and initiative.json() == {"status": "saved", "changed": True}
    asks = _post(http, f"{base}/asks", ask_1="Approve funding", ask_2="", ask_3="Confirm the CISO")
    assert asks.status_code == 200 and asks.json() == {"status": "saved", "changed": True}
    db.expire_all()
    assert db.get(Action, action.id).responsibility == "shared"
    assert _bi().initiative_metadata(db, assessment.id)[group_id]["complexity"] == "high"
    assert _bi().board_asks(db.get(Assessment, assessment.id)) == {
        "consultant": ["Approve funding", "Confirm the CISO"], "consultant_by": REVIEWER,
    }

    # Refusals: the right status, an error toast, the {"detail": message} body, nothing saved.
    service = _bi()
    too_long = _post(
        http, f"{base}/observations/{finding.id}", business_impact="x" * 1201, recommendation="r"
    )
    assert too_long.status_code == 400
    assert too_long.json() == {"detail": service.TEXT_TOO_LONG.format(label="Why it matters", limit=1200)}
    assert too_long.headers["X-Toast-Type"] == "error"
    missing = _post(http, f"{base}/observations/no-such-finding", business_impact="a", recommendation="b")
    assert missing.status_code == 404 and missing.json() == {"detail": service.FINDING_NOT_FOUND}
    bad_resp = _post(http, f"{base}/actions/{action.id}/responsibility", responsibility="auditor")
    assert bad_resp.status_code == 400 and bad_resp.json() == {"detail": service.INVALID_RESPONSIBILITY}
    bad_group = _post(http, f"{base}/initiatives", group_id="NOT-A-GROUP", title="T", complexity="low", benefit="low")
    assert bad_group.status_code == 404 and bad_group.json() == {"detail": service.GROUP_NOT_FOUND}
    long_ask = _post(http, f"{base}/asks", ask_1="x" * 401)
    assert long_ask.status_code == 400
    assert long_ask.json() == {"detail": service.TEXT_TOO_LONG.format(label="Board decision", limit=400)}
    db.expire_all()
    assert db.get(Finding, finding.id).business_impact == "Consent is not valid."  # the 400 saved nothing
    assert _bi().board_asks(db.get(Assessment, assessment.id))["consultant"] == ["Approve funding", "Confirm the CISO"]


def test_scenario_8c_the_board_inputs_page_lists_every_input_and_escapes_text(db, http, fixture_assessment):
    """D-P6-8-V3-D: one page with a form per finding, action, roadmap group and the board asks."""
    assessment = fixture_assessment
    findings, actions = findings_and_actions(db, assessment)
    groups = roadmap_groups(db, assessment)
    base = f"/api/assessments/{assessment.id}/board-inputs"
    payload = "<script>alert('x')</script>"
    assert _post(
        http, f"{base}/observations/{findings[0].id}", business_impact=payload, recommendation="Fix it"
    ).status_code == 200

    page = http.get(f"/assessments/{assessment.id}/board-inputs")
    assert page.status_code == 200
    html = page.text
    assert 'id="reviewer-name"' in html
    for finding in findings:
        assert f'data-board-finding="{finding.id}"' in html
    assert 'name="business_impact"' in html and 'name="recommendation"' in html
    for finding in findings:
        for action in actions[finding.id]:
            assert f'data-board-action="{action.id}"' in html
    assert 'name="responsibility"' in html
    for value in ("client", "consultant", "shared"):
        assert f'value="{value}"' in html
    for group in groups:
        assert f'data-board-initiative="{group["group_id"]}"' in html
    for field in ("title", "complexity", "benefit"):
        assert f'name="{field}"' in html
    assert "data-board-asks" in html
    for index in (1, 2, 3):
        assert f'name="ask_{index}"' in html
    assert "ask_4" not in html
    # Saved text is escaped, never rendered as markup; the page never offers a numeric priority input.
    assert payload not in html and "&lt;script&gt;" in html
    assert 'name="priority"' not in html
    template = (REPO_ROOT / "app" / "templates" / "pages" / "board_inputs.html").read_text(encoding="utf-8")
    assert re.search(r"\|\s*safe\b", template) is None

    assert http.get("/assessments/no-such-assessment/board-inputs").status_code == 404
    findings_page = http.get(f"/assessments/{assessment.id}/findings")
    assert findings_page.status_code == 200
    assert f'data-board-inputs-link href="/assessments/{assessment.id}/board-inputs"' in findings_page.text


# ---------------------------------------------------------------------------
# 9. V3-A changes no report output
# ---------------------------------------------------------------------------


def test_scenario_9_captured_data_changes_no_conclusion_history_or_report_document(db, fixture_assessment):
    """D-P6-8-V3-A: capture only. The document, Conclusions and Action history are byte-identical."""
    service = _bi()
    assessment = fixture_assessment
    before_document = json.dumps(_document(db, assessment), sort_keys=True)
    findings, actions = findings_and_actions(db, assessment)
    conclusions = db.query(Conclusion).filter_by(assessment_id=assessment.id).count()
    revisions = db.query(ConclusionRevision).count()
    histories = {action.id: action.history_json for rows in actions.values() for action in rows}
    audit_before = db.query(AuditEvent).count()

    group_id = roadmap_groups(db, assessment)[0]["group_id"]
    service.update_finding_fields(
        db, assessment_id=assessment.id, finding_id=findings[0].id, business_impact="Why", recommendation="What", actor=ACTOR
    )
    service.update_action_responsibility(
        db, assessment_id=assessment.id, action_id=actions[findings[0].id][0].id, responsibility="client", actor=ACTOR
    )
    service.update_initiative(
        db, assessment_id=assessment.id, group_id=group_id, title="T", complexity="low", benefit="low", actor=ACTOR
    )
    service.update_board_asks(db, assessment_id=assessment.id, asks=["Approve"], actor=ACTOR)
    db.commit()
    db.expire_all()

    assert db.query(AuditEvent).count() == audit_before + 4  # exactly one event per edit, nothing else
    assert db.query(Conclusion).filter_by(assessment_id=assessment.id).count() == conclusions
    assert db.query(ConclusionRevision).count() == revisions
    assert {a.id: a.history_json for rows in findings_and_actions(db, assessment)[1].values() for a in rows} == histories
    assert json.dumps(_document(db, assessment), sort_keys=True) == before_document

    board_report = (REPO_ROOT / "app" / "services" / "board_report.py").read_text(encoding="utf-8")
    for token in ("business_impact", "board_asks", "responsibility", "initiative_metadata", "InitiativeMetadata"):
        assert token not in board_report, f"V3-A must not touch build_document ({token})"


# ---------------------------------------------------------------------------
# 10. Firm theme settings
# ---------------------------------------------------------------------------


def test_scenario_10_firm_theme_settings_are_validated_hex_with_the_deck_defaults():
    """D-P6-8-V3-E: F5. Primary, secondary and accent colours; the logo path is unchanged."""
    from app.config import Settings

    settings = Settings(_env_file=None)
    assert (settings.firm_color_primary, settings.firm_color_secondary, settings.firm_color_accent) == (
        DEFAULT_THEME["primary"], DEFAULT_THEME["secondary"], DEFAULT_THEME["accent"],
    )
    assert settings.firm_primary_hex == "#2563eb"  # the legacy fpdf2 / navigation colour is untouched
    for field in ("firm_color_primary", "firm_color_secondary", "firm_color_accent"):
        for bad in ("red", "#12345", "#GGGGGG", "161A5C", "#161A5C0", "", "#161A5C; x", "#161A5C\n"):
            with pytest.raises(ValidationError):
                Settings(_env_file=None, **{field: bad})
        assert getattr(Settings(_env_file=None, **{field: "#abcdef"}), field) == "#abcdef"
        assert getattr(Settings(_env_file=None, **{field: "#ABCDEF"}), field) == "#ABCDEF"

    theme_module = importlib.import_module("app.services.firm_theme")
    custom = Settings(
        _env_file=None, firm_name="Acme Advisory", firm_logo_path="/srv/logo.png",
        firm_color_primary="#112233", firm_color_secondary="#445566", firm_color_accent="#778899",
    )
    assert theme_module.resolve_theme(custom) == {
        "firm_name": "Acme Advisory", "logo_path": "/srv/logo.png",
        "primary": "#112233", "secondary": "#445566", "accent": "#778899",
    }
    assert theme_module.resolve_theme(settings) == {
        "firm_name": settings.firm_name, "logo_path": settings.firm_logo_path, **DEFAULT_THEME,
    }
    source = inspect.getsource(theme_module)
    assert "open(" not in source and "read_bytes" not in source, "V3-B freezes the logo; V3-A only resolves settings"


# ---------------------------------------------------------------------------
# 11. Display font
# ---------------------------------------------------------------------------


def test_scenario_11_display_font_is_vendored_pinned_licensed_and_offline():
    """D-P6-8-V3-F: Barlow Condensed Bold and SemiBold next to the Noto fonts, pinned by hash."""
    from app.utils import html_pdf

    assert html_pdf.DISPLAY_FONT_FILES == DISPLAY_FONT_SHA256
    assert tuple(html_pdf.DISPLAY_LICENSE_FILES) == DISPLAY_LICENSE_FILES
    for name, digest in DISPLAY_FONT_SHA256.items():
        assert hashlib.sha256((FONT_DIR / name).read_bytes()).hexdigest() == digest, name
    for name in DISPLAY_LICENSE_FILES:
        text_ = (FONT_DIR / name).read_text(encoding="utf-8")
        assert "SIL OPEN FONT LICENSE Version 1.1" in text_
        assert "Copyright 2017 The Barlow Project Authors" in text_
    # The existing Noto pins and CSS are untouched (B1's test pins them).
    assert set(html_pdf.FONT_FILES) == NOTO_FILES
    assert "Barlow" not in html_pdf.font_face_css() and "'Display'" not in html_pdf.font_face_css()
    css = html_pdf.display_font_face_css()
    assert css.count("@font-face") == 2 and css.count("font-family: 'Display'") == 2
    assert "BarlowCondensed-Bold.ttf" in css and "BarlowCondensed-SemiBold.ttf" in css
    assert "font-weight: 700" in css and "font-weight: 600" in css


def test_scenario_11b_display_font_renders_offline_in_weasyprint():
    """D-P6-8-V3-F: the offline renderer loads the display font from the vendored directory only."""
    import io

    import pdfplumber

    _require_renderer()
    from app.utils import html_pdf

    markup = (
        f"<style>{html_pdf.font_face_css()}\n{html_pdf.display_font_face_css()}</style>"
        "<p style=\"font-family: 'Display'; font-weight: 700\">Board report</p>"
        "<p style=\"font-family: 'Display'; font-weight: 600\">Executive summary</p>"
    )
    pdf = html_pdf.render_pdf(markup)
    assert pdf.startswith(b"%PDF")
    with pdfplumber.open(io.BytesIO(pdf)) as document:
        fonts = {char["fontname"] for page in document.pages for char in page.chars}
    # WeasyPrint names the subset after the CSS family ("Display") plus the face's style.
    assert any(name.endswith("Display-Bold-Condensed") for name in fonts), fonts
    assert any(name.endswith("Display-Semi-Bold-Condensed") for name in fonts), fonts
    refused = "<style>@font-face { font-family: 'X'; src: url('Other.ttf'); }</style><p style=\"font-family: X\">x</p>"
    with pytest.raises(html_pdf.OfflineRenderError):
        html_pdf.render_pdf(refused)


# ---------------------------------------------------------------------------
# 12. File set
# ---------------------------------------------------------------------------

V3A_ALLOWED_PATHS = V3A_APP_PATHS  # the same tuple the older guards allow (tests/p6_8_v3a_paths.py)
V3A_FORBIDDEN_PATHS = (
    # V3-B and P6-10 own these: the document, its schema, the template, the exporters, the golden.
    "app/services/board_report.py", "app/services/board_exports.py", "app/services/board_view.py",
    "app/services/board_derive.py", "app/templates/reports", "tests/golden",
    "app/services/report_snapshots.py", "app/routers/snapshots.py", "app/services/report_content.py",
    "app/templates/pages/report_snapshots.html",
    # Frozen reports, readers, analysis, LLM.
    "app/utils/pdf_export.py", "app/utils/rfi_export.py", "app/services/findings.py",
    "app/routers/findings.py", "app/schemas", "app/services/conclusion_review.py",
    "app/services/approved_report.py", "app/services/report_basis.py", "app/services/remediation_groups.py",
    "app/services/llm_client.py", "app/services/grounding", "app/services/claude_analyzer.py",
    "app/services/narrative.py", "app/services/remediation_draft.py", "app/routers/drafting.py",
    "requirements.txt", "scripts", "validation",
    # Yozora backend features (tasks/handoffs/2026-10-03-yozora-backend-features.md).
    *YOZORA_BACKEND_EXCLUDES,
    *YOZORA_EXCLUDES,  # Yozora S1
)
# Existing tests the designer or Codex edits: the "Alembic head" pins (D-P6-8-V3-S) ...
V3A_EXISTING_TEST_EDITS = {
    "tests/test_p6_6_report_foundations.py", "tests/test_retention.py", "tests/test_p5_6_rfi_rebuild.py",
    "tests/test_startup_invariants.py", "tests/test_p5_3_framework_desk_review.py",
    "tests/test_p5_4_adaptive_ucc_questionnaire.py", "tests/test_alembic_baseline_immutable.py",
    "tests/test_data_integrity.py", "tests/test_correctness_bundle.py", "tests/test_p5_2_reader_migration.py",
}
# ... the per-PR guard allowances (one scoped entry per existing guard file; never deleted) ...
GUARD_TEST_FILES = {
    "tests/test_p6_2b_dpdpa_criteria.py", "tests/test_p6_4_whats_missing.py", "tests/test_p6_7_requirement_card.py",
    "tests/test_p6_7b_add_to_rfi.py", "tests/test_p6_8_board_report_v2.py", "tests/test_p6_8_b2_docx_xlsx.py",
    "tests/test_p6_9_file_set.py", "tests/test_p6_3a_grounding.py", "tests/test_p6_4_cap_upload_limit.py",
    "tests/test_p6_4_v2_judge.py", "tests/test_p6_nist_csf2_alignment.py",
    "tests/p6_10_support.py",  # P6-10 guard helper: V3-A per-PR allowance
}
# ... and the v3 contract tests themselves (V3-B's two files ride along on its own branch).
V3_TEST_FILES = {
    "tests/test_p6_8_v3a_data_capture.py", "tests/p6_8_v3_support.py", "tests/p6_8_v3a_paths.py",
    "tests/test_p6_8_v3a_purge.py", "tests/test_p6_8_v3b_deck.py", "tests/test_p6_8_v3b_document.py",
    "tests/test_p6_8_v3a_extra.py",  # review fix: responsibility form submits on change
}


def test_scenario_12_v3a_touches_only_its_files_and_calls_no_llm():
    """D-P6-8-V3-A: capture only; the guard lists below are the complete file set."""
    committed = git("diff", "--name-only", "main...HEAD", "--", *V3A_FORBIDDEN_PATHS).split()
    working = git("diff", "--name-only", "HEAD", "--", *V3A_FORBIDDEN_PATHS).split()
    assert committed == [] and working == [], committed + working

    changed = set(git("diff", "--name-only", "main...HEAD", "--", "app", "alembic").split())
    changed |= set(git("diff", "--name-only", "HEAD", "--", "app", "alembic").split())
    changed |= set(git("ls-files", "--others", "--exclude-standard", "app", "alembic").split())
    outside = sorted(path for path in changed if path not in V3A_ALLOWED_PATHS and path not in YOZORA_BACKEND_APP_PATHS and path not in YOZORA_S1_PATHS)  # Yozora allowances (backend, S1)
    assert outside == [], outside
    migrations = sorted(
        path.name for path in (REPO_ROOT / "alembic" / "versions").glob("*.py")
        if path.name.startswith("5e9a2c7d4b18")
    )
    assert migrations in ([], ["5e9a2c7d4b18_p6_8_v3a_board_inputs.py"])

    changed_tests = set(git("diff", "--name-only", "main...HEAD", "--", "tests").split())
    changed_tests |= set(git("diff", "--name-only", "HEAD", "--", "tests").split())
    changed_tests |= set(git("ls-files", "--others", "--exclude-standard", "tests").split())
    unexpected = sorted(changed_tests - V3A_EXISTING_TEST_EDITS - GUARD_TEST_FILES - V3_TEST_FILES - set(YOZORA_BACKEND_FILES) - set(YOZORA_S1_PATHS))  # Yozora allowances (backend, S1)
    assert unexpected == [], unexpected

    for relative in ("app/services/board_inputs.py", "app/routers/board_inputs.py", "app/services/firm_theme.py"):
        path = REPO_ROOT / relative
        if path.exists():
            source = path.read_text(encoding="utf-8")
            for token in ("llm_client", "call_llm", "services.grounding", "claude_analyzer", "openai"):
                assert token not in source, (relative, token)

