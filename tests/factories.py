import itertools
from datetime import UTC, date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import generate_invite_token, hash_password
from src.users.models.users import User, UserActivation, UserLoginLockout, UserSession
from src.utils.enums import UserRole, UserStatus
from users.repositories.users import UserRepositoryBase

_counter = itertools.count(1)


def _next() -> int:
    return next(_counter)


async def make_user(
    test_db: AsyncSession,
    *,
    role: UserRole = UserRole.STUDENT,
    status: UserStatus = UserStatus.ACTIVE,
    is_active: bool = True,
    username: str | None = None,
    firstname: str | None = None,
    lastname: str | None = None,
    middlename: str | None = None,
    email: str | None = None,
    phone_number: str | None = None,
    date_of_birth: date | None = None,
    address: str | None = None,
    password: str | None = "TestPassword123!",
    created_by: int | None = None,
    failed_login_attempts: int = 0,
    locked_until: datetime | None = None,
) -> User:
    n = _next()

    new_user = User(
        username=username or f"user_{n}",
        firstname=firstname or "Test",
        lastname=lastname or "User",
        middlename=middlename,
        email=email or f"user_{n}@example.com",
        phone_number=phone_number or f"+992917{n:06d}",
        date_of_birth=date_of_birth
        if date_of_birth is not None
        else (date(2008, 1, 1) if role == UserRole.STUDENT else None),
        address=address,
        password_hash=await hash_password(password) if password else None,
        role=role,
        status=status,
        is_active=is_active,
        created_by=created_by,
    )

    UserRepositoryBase.add_entity(test_db, user=new_user)
    await test_db.flush()

    _, hashed_invite_token = generate_invite_token()

    new_activation = UserActivation(
        user_id=new_user.id,
        invite_token_hash=hashed_invite_token
        if status == UserStatus.PENDING_ACTIVATION
        else None,
        invite_token_expires_at=(
            datetime.now(UTC) + timedelta(hours=24)
            if status == UserStatus.PENDING_ACTIVATION
            else None
        ),
    )
    new_session = UserSession(user_id=new_user.id)
    new_login_lockout = UserLoginLockout(
        user_id=new_user.id,
        failed_login_attempts=failed_login_attempts,
        locked_until=locked_until,
    )

    UserRepositoryBase.add_entity(
        test_db,
        user_activation=new_activation,
        user_session=new_session,
        user_login_lockout=new_login_lockout,
    )

    await test_db.commit()
    await test_db.refresh(new_user)

    return new_user


async def make_system_admin(test_db: AsyncSession, **kwargs) -> User:
    return await make_user(test_db, role=UserRole.SYSTEM_ADMIN, **kwargs)


async def make_director(test_db: AsyncSession, **kwargs) -> User:
    return await make_user(test_db, role=UserRole.DIRECTOR, **kwargs)


async def make_vice_director(test_db: AsyncSession, **kwargs) -> User:
    return await make_user(test_db, role=UserRole.VICE_DIRECTOR, **kwargs)


async def make_teacher(test_db: AsyncSession, **kwargs) -> User:
    return await make_user(test_db, role=UserRole.TEACHER, **kwargs)


async def make_student(test_db: AsyncSession, **kwargs) -> User:
    kwargs.setdefault("date_of_birth", date(2008, 1, 1))

    return await make_user(test_db, role=UserRole.STUDENT, **kwargs)


async def make_guardian(test_db: AsyncSession, **kwargs) -> User:
    return await make_user(test_db, role=UserRole.GUARDIAN, **kwargs)
