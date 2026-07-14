"""21_add_new_values_to_emailtype_enum

Revision ID: 20cca121312a
Revises: 96b624692a9a
Create Date: 2026-07-15 03:55:55.814920

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20cca121312a"
down_revision: str | Sequence[str] | None = "96b624692a9a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE emailtype ADD VALUE 'FORGOT_PASSWORD'")


def downgrade() -> None:
    """Downgrade schema."""
    pass
