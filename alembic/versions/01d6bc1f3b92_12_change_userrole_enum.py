"""12_change_userrole_enum

Revision ID: 01d6bc1f3b92
Revises: 7b5f823fdbb2
Create Date: 2026-07-01 12:43:01.588850

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "01d6bc1f3b92"
down_revision: str | Sequence[str] | None = "7b5f823fdbb2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE userrole RENAME VALUE 'PARENT' TO 'GUARDIAN'")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TYPE userrole RENAME VALUE 'GUARDIAN' TO 'PARENT'")
