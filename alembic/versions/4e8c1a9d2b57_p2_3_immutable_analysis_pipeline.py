"""P2-3: link conclusion revisions to immutable analysis runs."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "4e8c1a9d2b57"
down_revision: Union[str, None] = "3d8b6f0a2c51"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_REVISION_FK = "fk_conclusion_revisions_analysis_run_id_analysis_runs"
_REVISION_INDEX = "ix_conclusion_revisions_analysis_run_id"
_CONCLUSION_INDEX = "uq_conclusions_assessment_framework_requirement"


def upgrade() -> None:
    bind = op.get_bind()
    duplicate_groups = bind.execute(
        sa.text(
            "SELECT COUNT(*) FROM ("
            "SELECT 1 FROM conclusions "
            "GROUP BY assessment_id, framework_id, requirement_id "
            "HAVING COUNT(*) > 1"
            ")"
        )
    ).scalar_one()
    if duplicate_groups:
        raise RuntimeError(
            "Refusing to add uq_conclusions_assessment_framework_requirement: "
            f"{duplicate_groups} (assessment_id, framework_id, requirement_id) groups "
            "in conclusions hold more than one row. Resolve them first -- restore a "
            "verified backup or merge the duplicates by hand."
        )

    with op.batch_alter_table("conclusion_revisions", schema=None) as batch_op:
        batch_op.add_column(sa.Column("analysis_run_id", sa.String(length=36), nullable=True))
        batch_op.create_foreign_key(
            _REVISION_FK,
            "analysis_runs",
            ["analysis_run_id"],
            ["id"],
        )
        batch_op.create_index(_REVISION_INDEX, ["analysis_run_id"], unique=False)

    with op.batch_alter_table("conclusions", schema=None) as batch_op:
        batch_op.create_index(
            _CONCLUSION_INDEX,
            ["assessment_id", "framework_id", "requirement_id"],
            unique=True,
        )


def downgrade() -> None:
    bind = op.get_bind()
    linked_revisions = bind.execute(
        sa.text(
            "SELECT COUNT(*) FROM conclusion_revisions "
            "WHERE analysis_run_id IS NOT NULL"
        )
    ).scalar_one()
    if linked_revisions:
        raise RuntimeError(
            "Refusing to downgrade past P2-3 revision 4e8c1a9d2b57: "
            f"{linked_revisions} conclusion_revisions rows are linked to analysis runs. "
            "Downgrading would drop that link -- restore a verified backup instead."
        )

    with op.batch_alter_table("conclusions", schema=None) as batch_op:
        batch_op.drop_index(_CONCLUSION_INDEX)

    with op.batch_alter_table("conclusion_revisions", schema=None) as batch_op:
        batch_op.drop_index(_REVISION_INDEX)
        batch_op.drop_constraint(_REVISION_FK, type_="foreignkey")
        batch_op.drop_column("analysis_run_id")
