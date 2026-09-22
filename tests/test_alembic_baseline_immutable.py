"""Adversarial-review fix (PR #16, finding 1): the baseline revision must be
frozen, revision-owned DDL — not `Base.metadata.create_all()` — so it can
never drift with future ORM model changes or collide with a later revision
on a fresh database.
"""
import shutil
import textwrap
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

REPO_ROOT = Path(__file__).resolve().parent.parent

_LATER_REVISION_TEMPLATE = textwrap.dedent(
    '''
    """representative later schema revision, added on top of the frozen baseline + retrofit"""
    from alembic import op
    import sqlalchemy as sa

    revision = "zzzz_review_probe"
    down_revision = "6fcd9e575309"
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
