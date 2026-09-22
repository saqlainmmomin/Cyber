"""baseline schema: current schema as of PR #14

Revision ID: 6fc718bb9f09
Revises:
Create Date: 2026-09-22 10:53:57.257026

"""
from typing import Sequence, Union

from alembic import op

import app.models  # noqa: F401 — ensure all models registered on Base.metadata
from app.database import Base

# revision identifiers, used by Alembic.
revision: str = '6fc718bb9f09'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Uses the real ORM metadata (not hand-copied autogenerate DDL) so the
    # baseline can never drift from app/models/*.py. checkfirst=True (the
    # default) makes this a no-op against a legacy DB that already has these
    # tables, which is required so the next revision can retrofit it.
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
