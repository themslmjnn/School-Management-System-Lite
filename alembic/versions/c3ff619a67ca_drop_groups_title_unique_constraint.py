"""drop groups title unique constraint

Revision ID: c3ff619a67ca
Revises: 65ba71ee0d49
Create Date: 2026-03-09 18:06:48.050872

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3ff619a67ca'
down_revision: Union[str, Sequence[str], None] = '65ba71ee0d49'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint(op.f('groups_title_key'), 'groups', type_='unique')
    op.create_unique_constraint('uix_title_language_group', 'groups', ['title', 'language'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(op.f('uix_title_language'), 'groups', type_='unique')
    op.create_unique_constraint('groups_title_key', 'groups', ['title'], postgresql_nulls_not_distinct=False)