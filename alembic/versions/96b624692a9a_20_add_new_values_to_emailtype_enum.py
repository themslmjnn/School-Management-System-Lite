"""20_add_new_values_to_emailtype_enum

Revision ID: 96b624692a9a
Revises: 9b8e1ca4bb22
Create Date: 2026-07-15 03:02:55.386256

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "96b624692a9a"
down_revision: str | Sequence[str] | None = "9b8e1ca4bb22"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE emailtype ADD VALUE 'EMAIL_CHANGED'")


def downgrade() -> None:
    """Downgrade schema."""
    pass
