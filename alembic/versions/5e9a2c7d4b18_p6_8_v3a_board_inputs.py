"""P6-8 V3-A: capture consultant-entered board inputs."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "5e9a2c7d4b18"
down_revision: Union[str, None] = "8b2d5f7e1c34"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("findings", schema=None) as batch_op:
        batch_op.add_column(sa.Column("business_impact", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("recommendation", sa.Text(), nullable=True))

    with op.batch_alter_table("actions", schema=None) as batch_op:
        batch_op.add_column(sa.Column("responsibility", sa.String(length=20), nullable=True))

    with op.batch_alter_table("assessments", schema=None) as batch_op:
        batch_op.add_column(sa.Column("board_asks_json", sa.Text(), nullable=True))

    op.create_table(
        "initiative_metadata",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("assessment_id", sa.String(length=36), nullable=False),
        sa.Column("group_id", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("complexity", sa.String(length=10), nullable=True),
        sa.Column("benefit", sa.String(length=10), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["assessment_id"], ["assessments.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "assessment_id", "group_id", name="uq_initiative_metadata_assessment_group"
        ),
    )
    op.create_index(
        "ix_initiative_metadata_assessment_id",
        "initiative_metadata",
        ["assessment_id"],
        unique=False,
    )


def downgrade() -> None:
    bind = op.get_bind()
    data_counts = {
        "business_impact": bind.execute(
            sa.text("SELECT COUNT(*) FROM findings WHERE business_impact IS NOT NULL")
        ).scalar_one(),
        "recommendation": bind.execute(
            sa.text("SELECT COUNT(*) FROM findings WHERE recommendation IS NOT NULL")
        ).scalar_one(),
        "responsibility": bind.execute(
            sa.text("SELECT COUNT(*) FROM actions WHERE responsibility IS NOT NULL")
        ).scalar_one(),
        "board_asks_json": bind.execute(
            sa.text("SELECT COUNT(*) FROM assessments WHERE board_asks_json IS NOT NULL")
        ).scalar_one(),
        "initiative_metadata": bind.execute(
            sa.text("SELECT COUNT(*) FROM initiative_metadata")
        ).scalar_one(),
    }
    present = {name: count for name, count in data_counts.items() if count}
    if present:
        details = ", ".join(f"{name}={count}" for name, count in present.items())
        raise RuntimeError(
            "Refusing to downgrade past P6-8 V3-A revision 5e9a2c7d4b18: "
            f"consultant-entered data would be lost ({details}); restore a verified backup instead."
        )

    op.drop_index("ix_initiative_metadata_assessment_id", table_name="initiative_metadata")
    op.drop_table("initiative_metadata")
    with op.batch_alter_table("assessments", schema=None) as batch_op:
        batch_op.drop_column("board_asks_json")
    with op.batch_alter_table("actions", schema=None) as batch_op:
        batch_op.drop_column("responsibility")
    with op.batch_alter_table("findings", schema=None) as batch_op:
        batch_op.drop_column("recommendation")
        batch_op.drop_column("business_impact")
