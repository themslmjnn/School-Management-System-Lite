"""34_drop_user_status_enum_values

Revision ID: 0cde98387259
Revises: 7028c00cfe11
Create Date: 2026-08-16 09:32:45.320824

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0cde98387259"
down_revision: str | Sequence[str] | None = "7028c00cfe11"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE userstatus RENAME TO userstatus_old")
    op.execute(
        "CREATE TYPE userstatus AS ENUM ('ACTIVE', 'DEACTIVATED', 'PENDING_ACTIVATION', 'GRADUATED', 'EXPELLED', 'WITHDRAWN')"
    )
    op.execute(
        "ALTER TABLE users ALTER COLUMN status TYPE userstatus USING status::text::userstatus"
    )
    op.execute("DROP TYPE userstatus_old")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TYPE userstatus RENAME TO userstatus_old")
    op.execute(
        "CREATE TYPE userstatus AS ENUM ('ACTIVE', 'DEACTIVATED', 'DELETION', 'PENDING_ACTIVATION', 'PENDING_DELETION', 'GRADUATED', 'EXPELLED', 'WITHDRAWN')"
    )
    op.execute(
        "ALTER TABLE users ALTER COLUMN status TYPE userstatus USING status::text::userstatus"
    )
    op.execute("DROP TYPE userstatus_old")
