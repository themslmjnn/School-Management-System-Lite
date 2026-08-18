from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
import redis.asyncio as aioredis
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

import src.core.caching as cache_module
from src.auth.schemas import CreateAccessToken
from src.core.config import settings
from src.core.dependencies import get_session
from src.core.security import create_access_token
from src.database.connection import Base
from src.main import app
from src.users.models.user import User
from src.users.repositories.user import UserRepositoryBase
from src.users.schemas.system_admin import (
    CreateStudentAdmin,
    CreateTeacherAdmin,
)
from tests.factories import (
    make_director,
    make_student,
    make_system_admin,
    make_teacher,
)

ASYNC_DB_URL = (
    f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PSSW}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)

SYNC_DB_URL = (
    f"postgresql+psycopg2://{settings.DB_USER}:{settings.DB_PSSW}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)

test_engine = create_async_engine(url=ASYNC_DB_URL, poolclass=NullPool)


@pytest.fixture(scope="session", autouse=True)
def _guard_test_environment():
    if settings.ENVIRONMENT != "test":
        pytest.exit(
            f"Refusing to run tests: ENVIRONMENT is '{settings.ENVIRONMENT}', "
            "expected 'test'. This guard exists because the test suite "
            "creates and drops the full schema — running it against a "
            "non-test database would destroy real data."
        )


@pytest.fixture(scope="session", autouse=True)
def create_tables(_guard_test_environment):
    sync_engine = create_engine(SYNC_DB_URL)
    Base.metadata.create_all(sync_engine)

    yield

    Base.metadata.drop_all(sync_engine)
    sync_engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def session():
    async with test_engine.connect() as conn:
        await conn.begin()

        test_session = AsyncSession(bind=conn, expire_on_commit=False)

        async def override_get_session():
            yield test_session

        app.dependency_overrides[get_session] = override_get_session

        try:
            yield test_session

        finally:
            try:
                await test_session.close()
                await conn.rollback()

            except Exception as e:
                print(f"Teardown error: {e}")

            finally:
                app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def client(session):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as async_client:
        yield async_client


@pytest_asyncio.fixture(scope="function", autouse=True)
async def flush_cache():
    fresh_client = aioredis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD or None,
        db=settings.REDIS_DB,
        decode_responses=True,
    )

    cache_module.redis_client = fresh_client

    await fresh_client.flushdb()

    yield

    await fresh_client.flushdb()
    await fresh_client.aclose()


@pytest.fixture
def mock_response():
    return MagicMock()


async def make_auth_header(session: AsyncSession, user: User) -> dict:
    user_with_session = await UserRepositoryBase.get_user_by_id(
        session, user.id, load_session=True
    )

    token = create_access_token(
        CreateAccessToken(
            user_id=user.id,
            role=user.role,
            access_token_version=user_with_session.session.access_token_version,
        )
    )

    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def system_admin(session):
    return await make_system_admin(session)


@pytest_asyncio.fixture
async def director(session):
    return await make_director(session)


@pytest_asyncio.fixture
async def teacher(session):
    return await make_teacher(session)


@pytest_asyncio.fixture
async def student(session):
    return await make_student(session)


create_user_request = {
    "username": "new_test_username",
    "firstname": "New",
    "lastname": "User",
    "email": "new_test_email@gmail.com",
    "phone_number": "+992 111 111 101",
}


@pytest.fixture
def valid_create_teacher_request():
    return CreateTeacherAdmin(
        **create_user_request,
        type="teacher",
    )


@pytest.fixture
def valid_create_student_request():
    return CreateStudentAdmin(
        **create_user_request,
        type="student",
        date_of_birth="2008-05-01",
    )


@pytest.fixture
def mock_delete_cache_users_system_admin(mocker):
    return mocker.patch("src.users.services.system_admin.delete_cache")


@pytest.fixture
def mock_set_cache(mocker):
    return mocker.patch("src.users.services.system_admin.set_cache")


@pytest.fixture
def mock_advisory_lock(mocker):
    return mocker.patch(
        "src.users.services.system_admin.acquire_student_contact_lock",
        return_value=None,
    )


@pytest.fixture
def mock_check_contact_limit(mocker):
    return mocker.patch(
        "src.users.services.system_admin.check_contact_limit",
        return_value=None,
    )


@pytest.fixture
def mock_send_account_info_updated_email(mocker):
    return mocker.patch(
        "src.users.services.system_admin.email_sender.send_account_info_updated_email",
        new_callable=AsyncMock,
    )


@pytest.fixture
def mock_send_account_deactivation_email(mocker):
    return mocker.patch(
        "src.users.services.system_admin.email_sender.send_account_deactivation_email",
        new_callable=AsyncMock,
    )


@pytest.fixture
def mock_send_account_activation_email(mocker):
    return mocker.patch(
        "src.users.services.system_admin.email_sender.send_account_activation_email",
        new_callable=AsyncMock,
    )
