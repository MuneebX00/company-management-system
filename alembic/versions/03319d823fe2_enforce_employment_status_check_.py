"""enforce employment status check constraint

Revision ID: 03319d823fe2
Revises: ba4e58651ce0
Create Date: 2026-08-12 01:02:04.278512

"""

from collections.abc import Sequence

from alembic import op

revision: str = "03319d823fe2"
down_revision: str | None = "ba4e58651ce0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_employees_employment_status",
        "employees",
        "employment_status IN ('ACTIVE', 'ON_LEAVE', 'SUSPENDED', 'TERMINATED')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_employees_employment_status", "employees", type_="check")
