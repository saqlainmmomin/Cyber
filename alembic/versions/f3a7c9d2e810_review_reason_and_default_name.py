"""Store conclusion decision reasons and the default reviewer name.

Revision ID: f3a7c9d2e810
Revises: e2c8f6a4d901
"""
from alembic import op
import sqlalchemy as sa

revision = "f3a7c9d2e810"
down_revision = "e2c8f6a4d901"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("conclusion_revisions", sa.Column("reason", sa.Text(), nullable=True))
    op.add_column(
        "firm_settings", sa.Column("default_reviewer_name", sa.String(200), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("firm_settings", "default_reviewer_name")
    op.drop_column("conclusion_revisions", "reason")
