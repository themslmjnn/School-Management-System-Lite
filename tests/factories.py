import itertools
from datetime import UTC, date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import generate_invite_token, hash_password
from src.emails.models import PendingEmail
from src.groups.models import Group
from src.subjects.models import Subject
from src.users.models.activation import UserActivation
from src.users.models.login_lockout import UserLoginLockout
from src.users.models.session import UserSession
from src.users.models.user import User
from src.utils.enums import EmailSendingStatus, EmailType, UserRole, UserStatus

_counter = itertools.count(1)


def _next() -> int:
    return next(_counter)


async def make_user(
    session: AsyncSession,
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
    group_id: int | None = None,
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
        group_id=group_id,
    )

    session.add(new_user)
    await session.flush()

    is_pending = status == UserStatus.PENDING_ACTIVATION
    _, hashed_invite_token = generate_invite_token()

    new_activation = UserActivation(
        user_id=new_user.id,
        invite_token_hash=hashed_invite_token if is_pending else None,
        invite_token_expires_at=(
            datetime.now(UTC) + timedelta(hours=24) if is_pending else None
        ),
    )
    new_session = UserSession(user_id=new_user.id)
    new_login_lockout = UserLoginLockout(
        user_id=new_user.id,
        failed_login_attempts=failed_login_attempts,
        locked_until=locked_until,
    )

    session.add(new_activation)
    session.add(new_session)
    session.add(new_login_lockout)

    await session.commit()
    await session.refresh(new_user)

    return new_user


async def make_system_admin(session: AsyncSession, **kwargs) -> User:
    return await make_user(session, role=UserRole.SYSTEM_ADMIN, **kwargs)


async def make_director(session: AsyncSession, **kwargs) -> User:
    return await make_user(session, role=UserRole.DIRECTOR, **kwargs)


async def make_teacher(session: AsyncSession, **kwargs) -> User:
    return await make_user(session, role=UserRole.TEACHER, **kwargs)


async def make_student(session: AsyncSession, **kwargs) -> User:
    kwargs.setdefault("date_of_birth", date(2008, 1, 1))

    return await make_user(session, role=UserRole.STUDENT, **kwargs)


async def make_deactivated_user(session: AsyncSession, **kwargs) -> User:
    kwargs.setdefault("status", UserStatus.DEACTIVATED)
    kwargs.setdefault("is_active", False)

    return await make_user(session, **kwargs)


async def make_email(
    session: AsyncSession,
    *,
    recipient: str = "test@example.com",
    subject: str = "Test Subject",
    html_body: str = "<p>Test</p>",
    text_body: str = "Test",
    email_type: EmailType = EmailType.INVITE,
    status: EmailSendingStatus = EmailSendingStatus.PENDING,
    retry_count: int = 0,
    last_error: str | None = None,
    sent_at=None,
    triggered_by: int | None = None,
    recipient_user_id: int | None = None,
) -> PendingEmail:
    email = PendingEmail(
        recipient=recipient,
        subject=subject,
        html_body=html_body,
        text_body=text_body,
        email_type=email_type,
        status=status,
        retry_count=retry_count,
        last_error=last_error,
        sent_at=sent_at,
        triggered_by=triggered_by,
        recipient_user_id=recipient_user_id,
    )

    session.add(email)
    await session.commit()
    await session.refresh(email)

    return email


async def make_subject(
    session: AsyncSession,
    *,
    name: str = "Mathematics",
    code: str = "MATH101",
    description: str | None = None,
    is_archived: bool = False,
) -> Subject:
    subject = Subject(
        name=name,
        code=code,
        description=description,
        is_archived=is_archived,
        archived_at=datetime.now(UTC) if is_archived else None,
    )

    session.add(subject)
    await session.commit()
    await session.refresh(subject)

    return subject


async def make_group(
    session: AsyncSession,
    *,
    name: str = "Group A",
    academic_year: int = 2025,
    grade_level: int | None = 1,
    capacity: int | None = 30,
) -> Group:
    group = Group(
        name=name,
        academic_year=academic_year,
        grade_level=grade_level,
        capacity=capacity,
    )

    session.add(group)
    await session.commit()
    await session.refresh(group)

    return group
