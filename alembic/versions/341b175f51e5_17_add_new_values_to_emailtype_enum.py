"""17_add_new_values_to_emailtype_enum

Revision ID: 341b175f51e5
Revises: d39b1ad84cc2
Create Date: 2026-07-13 17:05:30.167398

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '341b175f51e5'
down_revision: str | Sequence[str] | None = 'd39b1ad84cc2'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE emailtype ADD VALUE 'CANCEL_ACCOUNT_DELETION'")


def downgrade() -> None:
    """Downgrade schema."""
    pass
