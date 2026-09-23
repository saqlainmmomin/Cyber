"""Adversarial-review fix (PR #16, finding 1): the baseline revision must be
frozen, revision-owned DDL — not `Base.metadata.create_all()` — so it can
never drift with future ORM model changes or collide with a later revision
on a fresh database.
"""
import shutil
import textwrap
from datetime import datetime, timezone
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from tests.test_data_integrity import (
    _create_legacy_schema,
    _fresh_engine,
    _insert_legacy_data,
)

REPO_ROOT = Path(__file__).resolve().parent.parent

_LATER_REVISION_TEMPLATE = textwrap.dedent(
    '''
    """representative later schema revision, added on top of the frozen baseline + retrofit"""
    from alembic import op
    import sqlalchemy as sa

    revision = "zzzz_review_probe"
    down_revision = "7a3f1e2b9c80"
    branch_labels = None
    depends_on = None


    def upgrade():
        op.create_table(
            "p1_1_review_probe",
            sa.Column("id", sa.Integer(), primary_key=True),
        )


    def downgrade():
        op.drop_table("p1_1_review_probe")
    '''
)


def test_fresh_db_baseline_plus_later_revision_does_not_collide(tmp_path):
    """Upgrade a brand-new database through the frozen baseline, the
    retrofit revision, and one representative later revision (adding a
    new table) — proving a future migration can be layered on top without
    the baseline re-deriving or re-creating anything.
    """
    work_dir = tmp_path / "alembic"
    shutil.copytree(
        REPO_ROOT / "alembic", work_dir,
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    (work_dir / "versions" / "zzzz_review_probe.py").write_text(_LATER_REVISION_TEMPLATE)

    db_path = tmp_path / "fresh.db"
    cfg = Config(str(REPO_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(work_dir))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")

    command.upgrade(cfg, "head")

    engine = create_engine(f"sqlite:///{db_path}")
    try:
        tables = set(inspect(engine).get_table_names())
        assert "p1_1_review_probe" in tables
        assert "assessments" in tables
        assert "questionnaire_responses" in tables

        with engine.connect() as conn:
            current = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
        assert current == "zzzz_review_probe"
    finally:
        engine.dispose()


_LATER_COLUMN_REVISION_TEMPLATE = textwrap.dedent(
    '''
    """representative later revision adding a column to a table the retrofit
    revision (6fcd9e575309) may have just rebuilt for FK enforcement — must
    not collide with, or be pre-empted by, that historical rebuild."""
    from alembic import op
    import sqlalchemy as sa

    revision = "zzzz_later_column_probe"
    down_revision = "7a3f1e2b9c80"
    branch_labels = None
    depends_on = None


    def upgrade():
        op.add_column(
            "gap_items", sa.Column("later_revision_marker", sa.Text(), nullable=True)
        )


    def downgrade():
        op.drop_column("gap_items", "later_revision_marker")
    '''
)


def test_legacy_fk_rebuild_plus_later_revision_does_not_collide(tmp_path):
    """PR #16 remediation (P1): the retrofit revision (6fcd9e575309) used to
    derive the DDL for its FK-rebuild of tables like gap_items from
    `Base.metadata` — the *live*, current ORM models — at migration run
    time. On a genuine legacy database needing that rebuild, a later
    revision's column could end up pre-created (or collided with) by the
    historical retrofit revision, instead of being added exactly once by
    the later revision that actually owns it.

    This reproduces that exact scenario: a legacy fixture whose gap_items
    table has no FK (forcing 6fcd9e575309 to rebuild it), plus a temporary
    later revision that adds a new column to gap_items. Both revisions must
    complete, and the later revision's column must be added exactly once —
    by the later revision, not by the historical rebuild.
    """
    work_dir = tmp_path / "alembic"
    shutil.copytree(
        REPO_ROOT / "alembic", work_dir,
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    (work_dir / "versions" / "zzzz_later_column_probe.py").write_text(
        _LATER_COLUMN_REVISION_TEMPLATE
    )

    db_path = tmp_path / "legacy.db"
    engine = _fresh_engine(tmp_path, "legacy.db")
    now_str = datetime.now(timezone.utc).isoformat()

    raw = engine.raw_connection()
    cursor = raw.cursor()
    cursor.execute("PRAGMA foreign_keys=OFF")
    _create_legacy_schema(cursor)  # no FK constraints — forces a rebuild
    _insert_legacy_data(cursor, now_str)
    raw.commit()
    cursor.close()
    raw.close()
    engine.dispose()

    cfg = Config(str(REPO_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(work_dir))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")

    command.upgrade(cfg, "head")

    engine = create_engine(f"sqlite:///{db_path}")
    try:
        with engine.connect() as conn:
            current = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
        assert current == "zzzz_later_column_probe"

        insp = inspect(engine)
        columns = insp.get_columns("gap_items")
        marker_cols = [c for c in columns if c["name"] == "later_revision_marker"]
        assert len(marker_cols) == 1, (
            "later_revision_marker must be added exactly once by the later "
            f"revision, found {len(marker_cols)} times: {columns}"
        )

        # The historical rebuild must still have happened — gap_items now
        # has its FK to gap_reports — proving both revisions actually ran,
        # not that the later one silently short-circuited the rebuild.
        fks = insp.get_foreign_keys("gap_items")
        assert any(fk["referred_table"] == "gap_reports" for fk in fks), (
            "legacy gap_items should have been FK-rebuilt by 6fcd9e575309"
        )

        with engine.connect() as conn:
            assert conn.execute(text("SELECT COUNT(*) FROM gap_items")).scalar() == 1, (
                "legacy row must survive both the FK rebuild and the later column add"
            )
    finally:
        engine.dispose()


def test_baseline_migration_source_has_no_metadata_dependency():
    """Guard against the baseline reverting to Base.metadata.create_all():
    a historical migration must not read the live ORM metadata at run
    time, or it would drift with future model changes and could collide
    with whatever a later revision tries to create.
    """
    baseline_source = (
        REPO_ROOT / "alembic" / "versions" / "6fc718bb9f09_baseline_schema.py"
    ).read_text()
    # The module docstring is allowed to mention Base.metadata in prose
    # (explaining what it does NOT do); only the code itself must never
    # call into it.
    assert "Base.metadata.create_all" not in baseline_source
    assert "Base.metadata.drop_all" not in baseline_source
    assert "from app.database import Base" not in baseline_source


def test_retrofit_fk_rebuild_source_has_no_live_metadata_dependency():
    """PR #16 remediation (P1): the FK-rebuild helpers used by the
    retrofit revision must take a frozen schema/table definition as a
    parameter, never resolve `Base.metadata` (live ORM state) themselves
    at migration runtime — see app/legacy_migrations_schema.py for the
    frozen DDL and app/legacy_migrations.py:_rebuild_table_for_fks /
    apply_fk_rebuild for the parameterized helpers."""
    # The module docstrings are allowed to mention Base.metadata in prose
    # (explaining what these modules do NOT do, same convention as
    # test_baseline_migration_source_has_no_metadata_dependency above);
    # only an actual import/live-lookup of it is disallowed.
    legacy_migrations_source = (
        REPO_ROOT / "app" / "legacy_migrations.py"
    ).read_text()
    assert "from app.database import Base" not in legacy_migrations_source
    assert "Base.metadata.tables" not in legacy_migrations_source
    assert "Base.metadata[" not in legacy_migrations_source

    retrofit_source = (
        REPO_ROOT / "alembic" / "versions"
        / "6fcd9e575309_retrofit_legacy_columns_fks_and_.py"
    ).read_text()
    assert "from app.database import Base" not in retrofit_source
    assert "Base.metadata.tables" not in retrofit_source
    assert "Base.metadata[" not in retrofit_source

    frozen_schema_source = (
        REPO_ROOT / "app" / "legacy_migrations_schema.py"
    ).read_text()
    assert "from app.database import Base" not in frozen_schema_source
    assert "Base.metadata.tables" not in frozen_schema_source
    assert "Base.metadata[" not in frozen_schema_source
