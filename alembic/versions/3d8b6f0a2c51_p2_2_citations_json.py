"""P2-2: store citations as validated JSON arrays.

Revision ID: 3d8b6f0a2c51
Revises: 7a3f1e2b9c80
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "3d8b6f0a2c51"
down_revision: Union[str, None] = "7a3f1e2b9c80"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    count = bind.execute(sa.text("SELECT COUNT(*) FROM citations")).scalar_one()
    if count:
        raise RuntimeError(
            "Refusing to drop the citations table: it holds "
            f"{count} rows. P2-2 moves citations to citations_json columns; "
            "migrate or remove those rows first."
        )

    with op.batch_alter_table("citations", schema=None) as batch_op:
        batch_op.drop_index("ix_citations_evidence_version_id")
    op.drop_table("citations")

    with op.batch_alter_table("desk_review_findings", schema=None) as batch_op:
        batch_op.add_column(sa.Column("citations_json", sa.Text(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    count = bind.execute(
        sa.text(
            "SELECT COUNT(*) FROM desk_review_findings "
            "WHERE citations_json IS NOT NULL"
        )
    ).scalar_one()
    if count:
        raise RuntimeError(
            "Refusing to downgrade past P2-2 revision 3d8b6f0a2c51: "
            f"{count} desk_review_findings rows hold citations. Downgrading "
            "would drop them -- restore a verified backup instead."
        )

    with op.batch_alter_table("desk_review_findings", schema=None) as batch_op:
        batch_op.drop_column("citations_json")

    op.create_table(
        "citations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("evidence_version_id", sa.String(length=36), nullable=False),
        sa.Column("location_type", sa.String(length=50), nullable=False),
        sa.Column("location_ref", sa.String(length=255), nullable=False),
        sa.Column("excerpt", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["evidence_version_id"], ["evidence_versions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("citations", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_citations_evidence_version_id"),
            ["evidence_version_id"],
            unique=False,
        )
