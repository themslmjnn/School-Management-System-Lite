"""empty

Revision ID: b77299ddc86c
Revises: b19f2f70c04e
Create Date: 2026-03-10 08:21:29.772453

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b77299ddc86c'
down_revision: Union[str, Sequence[str], None] = 'b19f2f70c04e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('student_group', sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False))
    op.add_column('teacher_subject', sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False))
    op.add_column('teacher_group', sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False))
    
    op.add_column('student_group', sa.Column('status', sa.Enum('moved', 'dropped', 'studying', name='studentgroupstatus'), nullable=False))
    op.add_column('teacher_subject', sa.Column('status', sa.Enum('finished', 'withdrawn', 'teaching', name='teachersubjectstatus'), nullable=False))
    op.add_column('teacher_group', sa.Column('status', sa.Boolean(), nullable=False))

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('student_group', 'updated_at')
    op.drop_column('student_group', 'status')

    op.drop_column('teacher_group', 'updated_at')
    op.drop_column('teacher_group', 'status')

    op.drop_column('teacher_subject', 'updated_at')
    op.drop_column('teacher_subject', 'status')