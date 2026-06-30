import itertools
from datetime import UTC, date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import generate_invite_token, hash_password
from src.users.models.guardian_link import StudentGuardianLink
from src.users.models.users import User, UserActivation, UserLoginLockout, UserSession
from src.users.repositories.guardian_link import GuardianLinkRepository
from src.users.repositories.users_admin import UserRepositoryBase
from src.utils.enums import GuardianPriority, UserRole, UserStatus

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
        phone_number=phone_number or f"+1555{n:07d}",
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

    raw_invite_token, hashed_invite_token = generate_invite_token()

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


async def make_parent(test_db: AsyncSession, **kwargs) -> User:
    return await make_user(test_db, role=UserRole.PARENT, **kwargs)


async def make_user_pending_activation(
    test_db: AsyncSession, **kwargs
) -> tuple[User, str]:
    kwargs.setdefault("status", UserStatus.PENDING_ACTIVATION)
    kwargs.setdefault("is_active", False)
    kwargs.setdefault("password", None)

    user = await make_user(test_db, **kwargs)

    user_with_activation = await UserRepositoryBase.get_user_by_id(
        test_db, user.id, load_activation=True
    )

    raw_invite_token, hashed_invite_token = generate_invite_token()
    user_with_activation.activation.invite_token_hash = hashed_invite_token
    user_with_activation.activation.invite_token_expires_at = datetime.now(
        UTC
    ) + timedelta(hours=24)

    await test_db.commit()

    return user, raw_invite_token


async def make_locked_out_user(
    test_db: AsyncSession, *, attempts: int = 5, **kwargs
) -> User:
    kwargs.setdefault("locked_until", datetime.now(UTC) + timedelta(minutes=15))
    return await make_user(test_db, failed_login_attempts=attempts, **kwargs)


async def make_deactivated_user(test_db: AsyncSession, **kwargs) -> User:
    kwargs.setdefault("status", UserStatus.DEACTIVATED)
    kwargs.setdefault("is_active", False)
    return await make_user(test_db, **kwargs)


async def make_parent_pending_deletion(test_db: AsyncSession, **kwargs) -> User:
    kwargs.setdefault("status", UserStatus.PENDING_DELETION)
    return await make_parent(test_db, **kwargs)


async def make_guardian_link(
    test_db: AsyncSession,
    *,
    guardian: User,
    student: User,
    priority: GuardianPriority = GuardianPriority.SECONDARY,
) -> StudentGuardianLink:
    link = StudentGuardianLink(
        parent_id=guardian.id,
        student_id=student.id,
        priority=priority,
    )
    GuardianLinkRepository.add_link(test_db, link)
    await test_db.commit()

    return link
