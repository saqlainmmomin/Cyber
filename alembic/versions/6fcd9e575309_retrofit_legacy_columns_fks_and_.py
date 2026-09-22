"""retrofit legacy columns, questionnaire answer constraint, and foreign keys

On a fresh database (created by the previous revision from the current ORM
models) every check in app.legacy_migrations is already satisfied, so this
revision is a no-op. On a genuine legacy database it adds the columns,
rebuilds the answer check constraint, and retrofits foreign keys exactly
as the old app/main.py DIY migration path did.

Ordering is deliberate: the FK orphan preflight runs first, fully
read-only, and raises before `run_column_migrations` (which can normalize
or delete questionnaire rows and backfill gap_items) ever touches the
database. That keeps an aborted upgrade recoverable — nothing is written,
so nothing needs to be rolled back, and re-running `alembic upgrade head`
after fixing the orphan is a plain retry, not a repair.

Revision ID: 6fcd9e575309
Revises: 6fc718bb9f09
Create Date: 2026-09-22 10:53:57.489890

"""
from typing import Sequence, Union

from alembic import op

from app.legacy_migrations import (
    apply_fk_rebuild,
    compute_fk_tables_to_rebuild,
    preflight_fk_orphans,
    run_column_migrations,
)
from app.legacy_migrations_schema import FROZEN_TABLES

# revision identifiers, used by Alembic.
revision: str = '6fcd9e575309'
down_revision: Union[str, None] = '6fc718bb9f09'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # These helpers each open their own connection against the same engine
    # (mirroring the pre-Alembic startup path exactly), rather than sharing
    # Alembic's migration connection — sqlite DDL here is non-transactional
    # either way.
    engine = op.get_bind().engine

    # 1. Read-only: figure out which tables need an FK rebuild, and abort
    #    now if ANY FK_SPEC-covered table has an orphaned row — not only
    #    the ones slated for rebuild — before any write below. A table
    #    that already has its FK declared can still carry a non-SET-NULL
    #    orphan, and that must block the migration even though it isn't
    #    the table this run would rebuild.
    tables_to_rebuild = compute_fk_tables_to_rebuild(engine)
    preflight_fk_orphans(engine)

    # 2. Only after the preflight passes: column adds, questionnaire
    #    constraint rebuild, and gap_items backfill.
    run_column_migrations(engine)

    # 3. The actual FK rebuild, followed by an unconditional
    #    PRAGMA foreign_key_check (even when tables_to_rebuild is empty)
    #    so a retry can never record head while an orphan remains.
    #    FROZEN_TABLES is hand-written, revision-owned DDL
    #    (app/legacy_migrations_schema.py) -- not a live lookup of
    #    Base.metadata -- so this historical revision's output can never
    #    drift with, or collide with, later model/schema changes.
    apply_fk_rebuild(engine, tables_to_rebuild, FROZEN_TABLES)


def downgrade() -> None:
    # Lossy-safe: this revision only adds columns/constraints/FKs to
    # existing tables. A full column-level downgrade would require rebuilding
    # every retrofitted table again; since the previous revision's downgrade
    # already drops all tables, this is a no-op so the pair round-trips
    # cleanly on an empty/fresh DB.
    pass
