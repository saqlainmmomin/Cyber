"""Yozora backend features: firm settings (with the firm-level archived-engagement retention) and
assessments.name (display name within an engagement).

Data migration: the firm_settings row is seeded with archived_retention_years taken from the
clients' retention_years. If every client shares one value it is used; otherwise the largest,
because keeping data longer is the safer choice; with no clients (or no valid value) it is 7.
clients.retention_years stays in place but is no longer read for new archives.
"""

import logging
from datetime import datetime, timezone
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7d41c9e2a63"
down_revision: Union[str, None] = "5e9a2c7d4b18"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = logging.getLogger("alembic.runtime.migration")

DEFAULT_RETENTION_YEARS = 7
DEFAULT_ACCENT_THEME = "midnight"


def initial_retention_years(values: list) -> tuple[int, str]:
    """The firm retention seeded from the clients' values, and a sentence saying how it was chosen."""
    valid = [
        value for value in values
        if isinstance(value, int) and not isinstance(value, bool) and 1 <= value <= 50
    ]
    if not values:
        return DEFAULT_RETENTION_YEARS, "no clients, using the default of 7 years"
    if not valid:
        return DEFAULT_RETENTION_YEARS, "no client has a valid retention, using the default of 7 years"
    distinct = sorted(set(valid))
    if len(distinct) == 1 and len(valid) == len(values):
        return distinct[0], f"all {len(values)} clients use {distinct[0]} years"
    ignored = len(values) - len(valid)
    note = f" ({ignored} invalid ignored)" if ignored else ""
    return max(valid), (
        f"clients use {', '.join(str(value) for value in distinct)} years{note}, using the largest, {max(valid)}"
    )


def upgrade() -> None:
    op.create_table(
        "firm_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("contact_email", sa.String(length=254), nullable=True),
        sa.Column("archived_retention_years", sa.Integer(), nullable=False),
        sa.Column("accent_theme", sa.String(length=20), nullable=False),
        sa.Column("accent_custom_hex", sa.String(length=7), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("id = 1", name="ck_firm_settings_singleton"),
        sa.CheckConstraint(
            "archived_retention_years BETWEEN 1 AND 50",
            name="ck_firm_settings_retention_range",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    bind = op.get_bind()
    values = list(bind.execute(sa.text("SELECT retention_years FROM clients")).scalars())
    years, how = initial_retention_years(values)
    bind.execute(
        sa.text(
            "INSERT INTO firm_settings "
            "(id, contact_email, archived_retention_years, accent_theme, accent_custom_hex, updated_at) "
            "VALUES (1, NULL, :years, :accent, NULL, :now)"
        ),
        {"years": years, "accent": DEFAULT_ACCENT_THEME, "now": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")},
    )
    logger.info("Firm retention seeded at %s years: %s.", years, how)

    with op.batch_alter_table("assessments", schema=None) as batch_op:
        batch_op.add_column(sa.Column("name", sa.String(length=255), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    data_counts = {
        "firm_settings": bind.execute(
            sa.text(
                "SELECT COUNT(*) FROM firm_settings "
                "WHERE contact_email IS NOT NULL OR accent_custom_hex IS NOT NULL"
            )
        ).scalar_one(),
        "assessments.name": bind.execute(
            sa.text("SELECT COUNT(*) FROM assessments WHERE name IS NOT NULL")
        ).scalar_one(),
    }
    present = {name: count for name, count in data_counts.items() if count}
    if present:
        details = ", ".join(f"{name}={count}" for name, count in present.items())
        raise RuntimeError(
            "Refusing to downgrade past Yozora backend revision b7d41c9e2a63: "
            f"consultant-entered data would be lost ({details}); restore a verified backup instead."
        )
    with op.batch_alter_table("assessments", schema=None) as batch_op:
        batch_op.drop_column("name")
    op.drop_table("firm_settings")
