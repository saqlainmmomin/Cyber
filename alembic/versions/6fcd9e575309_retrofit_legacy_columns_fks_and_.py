"""retrofit legacy columns, questionnaire answer constraint, and foreign keys

On a fresh database (created by the previous revision from the current ORM
models) every check in app.legacy_migrations is already satisfied, so this
revision is a no-op. On a genuine legacy database it adds the columns,
rebuilds the answer check constraint, and retrofits foreign keys exactly
as the old app/main.py DIY migration path did, including the orphan
preflight that aborts the migration (raising, before any write) rather
than silently dropping rows.

Revision ID: 6fcd9e575309
Revises: 6fc718bb9f09
Create Date: 2026-09-22 10:53:57.489890

"""
from typing import Sequence, Union

from alembic import op

from app.legacy_migrations import run_column_migrations, run_fk_retrofit

# revision identifiers, used by Alembic.
revision: str = '6fcd9e575309'
down_revision: Union[str, None] = '6fc718bb9f09'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # These helpers each open their own connection against the same engine
    # (mirroring the pre-Alembic startup path exactly), rather than sharing
    # Alembic's migration connection — sqlite DDL here is non-transactional
    # either way, and the orphan preflight in run_fk_retrofit always runs
    # fully read-only before any write, so an abort leaves the DB untouched
    # regardless of connection boundaries.
    engine = op.get_bind().engine
    run_column_migrations(engine)
    run_fk_retrofit(engine)


def downgrade() -> None:
    # Lossy-safe: this revision only adds columns/constraints/FKs to
    # existing tables. A full column-level downgrade would require rebuilding
    # every retrofitted table again; since the previous revision's downgrade
    # already drops all tables, this is a no-op so the pair round-trips
    # cleanly on an empty/fresh DB.
    pass
