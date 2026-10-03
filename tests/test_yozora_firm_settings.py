"""Yozora backend items 1 and 2: firm settings, and retention as a firm setting.

Handoff: tasks/handoffs/2026-10-03-yozora-backend-features.md. The retention rules themselves
(snapshot at archive, the floor for engagements archived before, the retired client route) are
covered in tests/test_retention.py scenario 5; here: the settings page, validation, the contrast
maths, the migration and its data migration.
"""

from __future__ import annotations

import importlib.util
import json
import sqlite3

import pytest
from alembic import command
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.assessment import Assessment
from app.models.firm_settings import FirmSettings
from app.services import firm_settings, retention
from tests.yozora_support import (  # noqa: F401 - fixtures are used by name
    PREVIOUS_REVISION,
    REPO_ROOT,
    YOZORA_REVISION,
    _register_frameworks,
    alembic_config,
    db,
    db_path,
    engine,
    http,
    seed_engagement,
    upload_root,
)

MIGRATION_PATH = REPO_ROOT / "alembic" / "versions" / f"{YOZORA_REVISION}_yozora_backend_features.py"


def _migration_module():
    spec = importlib.util.spec_from_file_location("yozora_migration", MIGRATION_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _save(http, **fields):
    data = {"archived_retention_years": "7", "accent_theme": "midnight", "reviewer_name": "Priya"}
    data.update(fields)
    return http.post("/settings", data=data, follow_redirects=False)


# --- Contrast maths (pure) ---------------------------------------------------


def test_contrast_ratio_matches_wcag_reference_values():
    assert firm_settings.contrast_ratio("#FFFFFF", "#000000") == pytest.approx(21.0)
    assert firm_settings.contrast_ratio("#000000", "#FFFFFF") == pytest.approx(21.0)
    assert firm_settings.contrast_ratio("#777777", "#777777") == pytest.approx(1.0)
    # The design system's measured values for Midnight (docs/product/yozora-design-system.md).
    assert round(firm_settings.contrast_ratio("#FFFFFF", "#1C3A72"), 1) == 11.1
    assert round(firm_settings.contrast_ratio("#1C3A72", "#F0F1F6"), 1) == 9.8
    assert firm_settings.relative_luminance("#ffffff") == pytest.approx(1.0)
    with pytest.raises(ValueError):
        firm_settings.relative_luminance("blue")


def test_every_preset_accent_passes_both_checks():
    for name, hex_colour in firm_settings.ACCENT_PRESETS.items():
        assert firm_settings.accent_contrast_problem(hex_colour) is None, name
    assert set(firm_settings.ACCENT_PRESETS) == {
        "graphite", "azure", "cobalt", "midnight", "slate", "teal", "violet", "plum",
    }
    tokens = (REPO_ROOT / "design" / "yozora-tokens.css").read_text(encoding="utf-8")
    for name, hex_colour in firm_settings.ACCENT_PRESETS.items():
        assert f"[data-accent={name}]{{--accent:{hex_colour};" in tokens, name


def test_accent_contrast_problem_names_the_failing_ratio():
    assert firm_settings.accent_contrast_problem("#12B3A6") == "White text on this colour is 2.6:1; it needs 4.5:1."
    # Passes white-on-accent (4.54) but fails as text on the light panel (4.02).
    assert firm_settings.accent_contrast_problem("#767676") == (
        "This colour as text on the light panel is 4.0:1; it needs 4.5:1."
    )
    # 4.48:1 is rounded down so the message never claims the 4.5 it misses.
    assert firm_settings.accent_contrast_problem("#777777") == "White text on this colour is 4.4:1; it needs 4.5:1."
    assert firm_settings.format_ratio(4.4999) == "4.4:1"
    assert firm_settings.format_ratio(21.0) == "21.0:1"


def test_normalize_hex_and_email_check():
    assert firm_settings.normalize_hex("1c3a72") == "#1C3A72"
    assert firm_settings.normalize_hex(" #1C3A72 ") == "#1C3A72"
    for bad in ("", "#12345", "#1234567", "#GGGGGG", "red"):
        assert firm_settings.normalize_hex(bad) is None
    assert firm_settings.valid_email("partner@northgate.example")
    for bad in ("", "partner", "partner@", "partner@northgate", "a b@c.de", "a@b@c.de", "x" * 250 + "@a.com"):
        assert not firm_settings.valid_email(bad), bad


def test_validate_reports_every_field_at_once():
    with pytest.raises(firm_settings.FirmSettingsValidationError) as excinfo:
        firm_settings.validate(
            contact_email="not-an-email",
            archived_retention_years="51",
            accent_theme="neon",
            accent_custom_hex=None,
        )
    assert excinfo.value.errors == {
        "contact_email": firm_settings.EMAIL_INVALID,
        "archived_retention_years": firm_settings.RETENTION_INVALID,
        "accent_theme": firm_settings.ACCENT_INVALID,
    }
    with pytest.raises(firm_settings.FirmSettingsValidationError) as excinfo:
        firm_settings.validate(
            contact_email="", archived_retention_years=7, accent_theme="custom", accent_custom_hex="#12"
        )
    assert excinfo.value.errors == {"accent_custom_hex": firm_settings.HEX_INVALID}
    for years in (1, "1", "50", " 7 "):
        assert firm_settings.validate(
            contact_email=None, archived_retention_years=years, accent_theme="teal", accent_custom_hex=None
        )["archived_retention_years"] == int(str(years).strip())
    for years in (0, 51, "7.5", "-1", "", None, True):
        with pytest.raises(firm_settings.FirmSettingsValidationError):
            firm_settings.validate(
                contact_email=None, archived_retention_years=years, accent_theme="teal", accent_custom_hex=None
            )


# --- Service ---------------------------------------------------------------------


def test_get_falls_back_to_defaults_without_a_row(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'orm.sqlite3'}")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        view = firm_settings.get(session)
        assert view.contact_email is None
        assert view.archived_retention_years == firm_settings.DEFAULT_RETENTION_YEARS == 7
        assert view.accent_theme == firm_settings.DEFAULT_ACCENT_THEME == "midnight"
        assert view.accent_custom_hex is None and view.accent_hex == "#1C3A72"
        assert view.updated_at is None

        stored, changes = firm_settings.update(
            session,
            contact_email="partner@northgate.example",
            archived_retention_years="10",
            accent_theme="custom",
            accent_custom_hex="#1f4fd1",
            actor="consultant:Priya",
        )
        session.commit()
        assert stored.contact_email == "partner@northgate.example"
        assert stored.archived_retention_years == 10
        assert stored.accent_custom_hex == "#1F4FD1" and stored.accent_choice == "custom"
        assert stored.accent_theme == "midnight"  # the preset underneath the custom colour is kept
        assert set(changes) == {"contact_email", "archived_retention_years", "accent_custom_hex"}
        assert session.query(FirmSettings).count() == 1

        again, changes = firm_settings.update(
            session,
            contact_email="partner@northgate.example",
            archived_retention_years=10,
            accent_theme="teal",
            actor="consultant:Priya",
        )
        assert changes == {
            "accent_theme": {"from": "midnight", "to": "teal"},
            "accent_custom_hex": {"from": "#1F4FD1", "to": None},
        }
        assert again.accent_hex == "#0B6E7F"
    finally:
        session.close()
        engine.dispose()


def test_a_corrupt_stored_row_reads_as_defaults(db):
    db.execute(text("UPDATE firm_settings SET accent_theme = 'neon', accent_custom_hex = 'zzz'"))
    db.commit()
    view = firm_settings.get(db)
    assert view.accent_theme == "midnight" and view.accent_custom_hex is None


# --- Routes and pages ---------------------------------------------------------------


def test_settings_page_shows_branding_retention_and_unmigrated_assessments(db, http):
    legacy = Assessment(company_name="Harbour and Finch Logistics", industry="logistics", company_size="small")
    db.add(legacy)
    db.commit()
    page = http.get("/settings")
    assert page.status_code == 200
    body = page.text
    assert "Contact email for clients" in body
    assert "Clients with an expired or revoked link are offered this address." in body
    assert "Keep archived engagements for" in body
    assert (
        "Archived engagements become eligible for permanent deletion after this period. "
        "Applies to engagements archived from now on."
    ) in body
    assert 'id="retention-years"' in body and "data-retention-form" in body
    assert 'value="7"' in body
    for name in firm_settings.ACCENT_PRESETS:
        assert f'value="{name}"' in body
    assert 'value="midnight" checked' in body
    assert "data-unmigrated-assessments" in body
    assert "Harbour and Finch Logistics" in body and f"/assessments/{legacy.id}" in body
    # The list moved off the dashboard; the nav links to Settings.
    dashboard = http.get("/").text
    assert "Unmigrated assessments" not in dashboard
    assert 'href="/settings"' in dashboard


def test_settings_page_without_unmigrated_assessments(http):
    assert "Every assessment is filed under a client." in http.get("/settings").text


def test_save_contact_email_and_accent(db, http):
    response = _save(http, contact_email="partner@northgate.example", accent_theme="teal")
    assert response.status_code == 303 and response.headers["location"] == "/settings?saved=1"
    view = firm_settings.get(db)
    assert view.contact_email == "partner@northgate.example" and view.accent_theme == "teal"
    page = http.get("/settings?saved=1").text
    assert "Settings saved" in page and 'value="partner@northgate.example"' in page
    assert 'value="teal" checked' in page
    assert _save(http, contact_email="partner@northgate.example", accent_theme="teal").headers["location"] == (
        "/settings?saved=0"
    )
    assert "Nothing changed" in http.get("/settings?saved=0").text
    # Clearing the email stores no address.
    _save(http, contact_email="", accent_theme="teal")
    db.expire_all()
    assert firm_settings.get(db).contact_email is None


def test_invalid_email_is_refused_and_nothing_is_stored(db, http):
    response = _save(http, contact_email="partner-at-northgate")
    assert response.status_code == 422
    assert firm_settings.EMAIL_INVALID in response.text
    assert 'value="partner-at-northgate"' in response.text  # the form keeps what was typed
    db.expire_all()
    assert firm_settings.get(db).contact_email is None


def test_custom_accent_failing_contrast_shows_the_ratio(db, http):
    response = _save(http, accent_theme="custom", accent_custom_hex="#12B3A6")
    assert response.status_code == 422
    assert "White text on this colour is 2.6:1; it needs 4.5:1." in response.text
    response = _save(http, accent_theme="custom", accent_custom_hex="#767676")
    assert response.status_code == 422
    assert "This colour as text on the light panel is 4.0:1; it needs 4.5:1." in response.text
    db.expire_all()
    assert firm_settings.get(db).accent_custom_hex is None
    response = _save(http, accent_theme="custom", accent_custom_hex="2563eb")
    assert response.status_code == 303
    db.expire_all()
    assert firm_settings.get(db).accent_custom_hex == "#2563EB"
    assert 'value="custom" checked' in http.get("/settings").text


def test_settings_change_is_audited(db, http):
    _save(http, contact_email="partner@northgate.example", archived_retention_years="12")
    row = db.execute(
        text(
            "SELECT actor, entity_type, entity_id, metadata_json FROM audit_events "
            "WHERE action = 'firm_settings.updated' ORDER BY rowid DESC LIMIT 1"
        )
    ).one()
    assert row[:3] == ("consultant:Priya", "firm_settings", "1")
    assert json.loads(row[3]) == {
        "changes": {
            "archived_retention_years": {"from": 7, "to": 12},
            "contact_email": {"from": None, "to": "partner@northgate.example"},
        }
    }


def test_engagement_page_reads_the_firm_retention(db, http):
    _client, engagement, _assessment = seed_engagement(db)
    assert "Retention: 7 years after archive (firm setting" in http.get(f"/engagements/{engagement.id}").text
    _save(http, archived_retention_years="15")
    page = http.get(f"/engagements/{engagement.id}").text
    assert "Retention: 15 years after archive (firm setting" in page
    assert "client setting" not in page
    assert "data-archive-control" in page


def test_new_archive_snapshots_the_firm_value(db, http):
    _client, engagement, _assessment = seed_engagement(db)
    _save(http, archived_retention_years="9")
    response = http.post(f"/api/engagements/{engagement.id}/archive", data={"reviewer_name": "Priya"})
    assert response.status_code == 200
    record = retention.archive_record(db, engagement.id)
    assert record.retention_years_at_archive == 9 and record.retention_source == "firm"


# --- Migration ------------------------------------------------------------------------------


def _columns(path, table):
    with sqlite3.connect(path) as connection:
        return {row[1]: (row[2].upper(), not row[3]) for row in connection.execute(f"PRAGMA table_info({table})")}


def _insert_client(path, client_id, years):
    with sqlite3.connect(path) as connection:
        connection.execute(
            "INSERT INTO clients (id, name, industry, size, retention_years, created_at, updated_at) "
            "VALUES (?, ?, 'Technology', 'small', ?, '2026-01-01', '2026-01-01')",
            (client_id, f"Client {client_id}", years),
        )


def _firm_row(path):
    with sqlite3.connect(path) as connection:
        return connection.execute(
            "SELECT id, contact_email, archived_retention_years, accent_theme, accent_custom_hex FROM firm_settings"
        ).fetchall()


def test_revision_is_the_head_on_top_of_v3a(tmp_path):
    scripts = ScriptDirectory.from_config(alembic_config(tmp_path / "x.sqlite3"))
    assert scripts.get_current_head() == YOZORA_REVISION
    assert scripts.get_revision(YOZORA_REVISION).down_revision == PREVIOUS_REVISION


@pytest.mark.parametrize(
    ("values", "expected"),
    [([], 7), ([5, 5, 5], 5), ([3, 10, 7], 10), ([12], 12)],
    ids=["no-clients", "shared", "largest", "single"],
)
def test_data_migration_seeds_the_firm_retention(tmp_path, values, expected):
    path = tmp_path / "seed.sqlite3"
    config = alembic_config(path)
    command.upgrade(config, PREVIOUS_REVISION)
    for index, years in enumerate(values):
        _insert_client(path, f"c{index}", years)
    command.upgrade(config, "head")
    assert _firm_row(path) == [(1, None, expected, "midnight", None)]
    with sqlite3.connect(path) as connection:  # the client column is kept, untouched
        assert sorted(row[0] for row in connection.execute("SELECT retention_years FROM clients")) == sorted(values)


def test_initial_retention_rule_and_its_log_sentence():
    module = _migration_module()
    assert module.initial_retention_years([]) == (7, "no clients, using the default of 7 years")
    assert module.initial_retention_years([5, 5]) == (5, "all 2 clients use 5 years")
    assert module.initial_retention_years([3, 10]) == (10, "clients use 3, 10 years, using the largest, 10")
    assert module.initial_retention_years([0, 99]) == (7, "no client has a valid retention, using the default of 7 years")
    assert module.initial_retention_years([7, 0]) == (7, "clients use 7 years (1 invalid ignored), using the largest, 7")


def test_migration_schema_is_reversible_and_keeps_data(tmp_path):
    path = tmp_path / "round.sqlite3"
    config = alembic_config(path)
    command.upgrade(config, "head")
    columns = _columns(path, "firm_settings")
    assert set(columns) == {
        "id", "contact_email", "archived_retention_years", "accent_theme", "accent_custom_hex", "updated_at",
    }
    assert columns["contact_email"][1] and columns["accent_custom_hex"][1]  # nullable
    assert not columns["archived_retention_years"][1] and not columns["accent_theme"][1]
    with sqlite3.connect(path) as connection:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO firm_settings (id, archived_retention_years, accent_theme, updated_at) "
                "VALUES (2, 7, 'midnight', '2026-10-03')"
            )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("UPDATE firm_settings SET archived_retention_years = 51")
    command.downgrade(config, "-1")
    with sqlite3.connect(path) as connection:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "firm_settings" not in tables
    command.upgrade(config, "head")
    assert _firm_row(path) == [(1, None, 7, "midnight", None)]


def test_downgrade_refuses_to_drop_a_stored_contact_email(tmp_path):
    path = tmp_path / "refuse.sqlite3"
    config = alembic_config(path)
    command.upgrade(config, "head")
    with sqlite3.connect(path) as connection:
        connection.execute("UPDATE firm_settings SET contact_email = 'partner@northgate.example'")
    with pytest.raises(RuntimeError, match="Refusing to downgrade past Yozora backend revision"):
        command.downgrade(config, "-1")
    assert _firm_row(path)[0][1] == "partner@northgate.example"
