"""13_change_emailtype_enum_values

Revision ID: 552b2f6fc5e7
Revises: 01d6bc1f3b92
Create Date: 2026-07-01 17:16:39.136476

"""

from collections.abc import Sequence
from typing import Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "552b2f6fc5e7"
down_revision: Union[str, Sequence[str], None] = "01d6bc1f3b92"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE emailtype ADD VALUE 'ADMIN_CREDENTIALS_OVERRIDE'")
    op.execute("ALTER TYPE emailtype ADD VALUE 'UPDATING_ACCOUNT'")
    op.execute("ALTER TYPE emailtype ADD VALUE 'ACCOUNT_DELETION'")


def downgrade() -> None:
    """Downgrade schema."""
    pass
