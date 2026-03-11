"""empty

Revision ID: dcfa8e77c4f9
Revises: 2cfc87ab938b
Create Date: 2026-03-11 21:52:08.477012

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dcfa8e77c4f9'
down_revision: Union[str, Sequence[str], None] = '2cfc87ab938b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_unique_constraint('uix_teacher_group', 'teacher_group', ['teacher_id', 'group_id', 'status'])
    op.create_unique_constraint('uix_teacher_subject', 'teacher_subject', ['teacher_id', 'subject_id', 'status'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uix_teacher_group', 'teacher_group', type_='unique')
    op.drop_constraint('uix_teacher_subject', 'teacher_subject', type_='unique')
