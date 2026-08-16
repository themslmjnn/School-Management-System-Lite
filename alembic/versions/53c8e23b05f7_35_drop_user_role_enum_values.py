"""35_drop_user_role_enum_values

Revision ID: 53c8e23b05f7
Revises: 0cde98387259
Create Date: 2026-08-16 09:51:22.679473

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "53c8e23b05f7"
down_revision: str | Sequence[str] | None = "0cde98387259"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("DROP INDEX uix_non_student_unique_phone")
    op.execute("DROP INDEX uix_non_student_unique_email")
    op.execute("ALTER TABLE users ALTER COLUMN role DROP DEFAULT")
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE text USING role::text")
    op.execute("UPDATE users SET role = 'DIRECTOR' WHERE role = 'VICE_DIRECTOR'")
    op.execute("UPDATE users SET role = 'DIRECTOR' WHERE role = 'GUARDIAN'")
    op.execute("DROP TYPE userrole")
    op.execute("""
        CREATE TYPE userrole AS ENUM ('SYSTEM_ADMIN', 'DIRECTOR', 'TEACHER', 'STUDENT')
    """)
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE userrole USING role::userrole")
    op.execute("ALTER TABLE users ALTER COLUMN role SET DEFAULT 'STUDENT'::userrole")
    op.execute("""
        CREATE UNIQUE INDEX uix_non_student_unique_phone
        ON users (phone_number)
        WHERE role <> 'STUDENT'::userrole
    """)
    op.execute("""
        CREATE UNIQUE INDEX uix_non_student_unique_email
        ON users (email)
        WHERE role <> 'STUDENT'::userrole
    """)


def downgrade() -> None:
    op.execute("DROP INDEX uix_non_student_unique_phone")
    op.execute("DROP INDEX uix_non_student_unique_email")
    op.execute("ALTER TABLE users ALTER COLUMN role DROP DEFAULT")
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE text USING role::text")
    op.execute("DROP TYPE userrole")
    op.execute("""
        CREATE TYPE userrole AS ENUM (
            'SYSTEM_ADMIN', 'DIRECTOR', 'VICE_DIRECTOR', 'TEACHER', 'STUDENT', 'GUARDIAN'
        )
    """)
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE userrole USING role::userrole")
    op.execute("ALTER TABLE users ALTER COLUMN role SET DEFAULT 'STUDENT'::userrole")
    op.execute("""
        CREATE UNIQUE INDEX uix_non_student_unique_phone
        ON users (phone_number)
        WHERE role <> 'STUDENT'::userrole
    """)
    op.execute("""
        CREATE UNIQUE INDEX uix_non_student_unique_email
        ON users (email)
        WHERE role <> 'STUDENT'::userrole
    """)
