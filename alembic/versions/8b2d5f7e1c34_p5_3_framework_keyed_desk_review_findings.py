"""P5-3: key desk review findings by framework, flag type and signal group.

Revision ID: 8b2d5f7e1c34
Revises: 4e8c1a9d2b57
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8b2d5f7e1c34"
down_revision: Union[str, None] = "4e8c1a9d2b57"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("desk_review_findings", schema=None) as batch_op:
        batch_op.add_column(sa.Column("framework_id", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("flag_type", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("signal_group_id", sa.String(length=36), nullable=True))

    # Every finding written before P5-3 came from the DPDPA-only desk review.
    op.execute(sa.text("UPDATE desk_review_findings SET framework_id = 'dpdpa' WHERE framework_id IS NULL"))


def downgrade() -> None:
    bind = op.get_bind()
    count = bind.execute(
        sa.text(
            "SELECT COUNT(*) FROM desk_review_findings "
            "WHERE flag_type IS NOT NULL OR signal_group_id IS NOT NULL "
            "OR (framework_id IS NOT NULL AND framework_id != 'dpdpa')"
        )
    ).scalar_one()
    if count:
        raise RuntimeError(
            "Refusing to downgrade past P5-3 revision 8b2d5f7e1c34: "
            f"{count} desk_review_findings rows hold framework-keyed data (a non-DPDPA "
            "framework_id, a flag_type or a signal_group_id). Downgrading would drop it "
            "and make non-DPDPA findings read as DPDPA -- restore a verified backup instead."
        )

    with op.batch_alter_table("desk_review_findings", schema=None) as batch_op:
        batch_op.drop_column("signal_group_id")
        batch_op.drop_column("flag_type")
        batch_op.drop_column("framework_id")
