"""P2-1: add Evidence service columns and constraints.

Revision ID: 7a3f1e2b9c80
Revises: 5c7c75960f43
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "7a3f1e2b9c80"
down_revision: Union[str, None] = "5c7c75960f43"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("evidence", schema=None) as batch_op:
        batch_op.add_column(sa.Column("assessment_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("document_category", sa.String(length=50), nullable=True))
        batch_op.create_foreign_key(
            "fk_evidence_assessment_id_assessments",
            "assessments",
            ["assessment_id"],
            ["id"],
        )
        batch_op.create_index("ix_evidence_assessment_id", ["assessment_id"], unique=False)

    with op.batch_alter_table("evidence_versions", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("status", sa.String(length=20), server_default="quarantined", nullable=False)
        )
        batch_op.add_column(sa.Column("original_filename", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("mime_type", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("extracted_text", sa.Text(), nullable=True))
        batch_op.create_index(
            "ix_evidence_versions_file_hash_sha256",
            ["file_hash_sha256"],
            unique=False,
        )

    bind = op.get_bind()
    bind.execute(
        sa.text(
            "UPDATE evidence_versions "
            "SET original_filename = (SELECT original_filename FROM evidence "
            "WHERE evidence.id = evidence_versions.evidence_id), "
            "mime_type = (SELECT mime_type FROM evidence "
            "WHERE evidence.id = evidence_versions.evidence_id)"
        )
    )

    with op.batch_alter_table("evidence_versions", schema=None) as batch_op:
        batch_op.alter_column("original_filename", nullable=False)
        batch_op.alter_column("mime_type", nullable=False)
        batch_op.create_unique_constraint(
            "uq_evidence_versions_evidence_id_version_number",
            ["evidence_id", "version_number"],
        )

    with op.batch_alter_table("evidence_uses", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            "uq_evidence_uses_mapping",
            ["evidence_id", "assessment_id", "framework_id", "requirement_id"],
        )


def _refuse_downgrade_if_any_data(bind) -> None:
    existing_tables = set(inspect(bind).get_table_names())
    non_empty = []
    for table in ("evidence", "evidence_versions", "evidence_uses"):
        if table not in existing_tables:
            continue
        count = bind.execute(sa.text(f"SELECT COUNT(*) FROM {table}")).scalar()
        if count:
            non_empty.append(f"{table} ({count} rows)")
    if non_empty:
        raise RuntimeError(
            "Refusing to downgrade past P2-1 revision 7a3f1e2b9c80: "
            f"these tables still hold data: {', '.join(non_empty)}. "
            "Downgrading would permanently drop evidence columns -- restore a verified backup instead."
        )


def downgrade() -> None:
    _refuse_downgrade_if_any_data(op.get_bind())

    with op.batch_alter_table("evidence_uses", schema=None) as batch_op:
        batch_op.drop_constraint("uq_evidence_uses_mapping", type_="unique")

    with op.batch_alter_table("evidence_versions", schema=None) as batch_op:
        batch_op.drop_constraint(
            "uq_evidence_versions_evidence_id_version_number", type_="unique"
        )
        batch_op.drop_index("ix_evidence_versions_file_hash_sha256")
        batch_op.drop_column("extracted_text")
        batch_op.drop_column("mime_type")
        batch_op.drop_column("original_filename")
        batch_op.drop_column("status")

    with op.batch_alter_table("evidence", schema=None) as batch_op:
        batch_op.drop_constraint("fk_evidence_assessment_id_assessments", type_="foreignkey")
        batch_op.drop_index("ix_evidence_assessment_id")
        batch_op.drop_column("document_category")
        batch_op.drop_column("assessment_id")
