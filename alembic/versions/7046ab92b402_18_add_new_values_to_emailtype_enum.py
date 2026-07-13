"""18_add_new_values_to_emailtype_enum

Revision ID: 7046ab92b402
Revises: 341b175f51e5
Create Date: 2026-07-13 19:01:00.644929

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7046ab92b402"
down_revision: str | Sequence[str] | None = "341b175f51e5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE emailtype ADD VALUE 'PASSWORD_CHANGED'")
    op.execute("ALTER TYPE emailtype ADD VALUE 'EMAIL_CHANGE_CODE'")


def downgrade() -> None:
    """Downgrade schema."""
    pass
