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
from src.core.dependencies import get_db
from src.core.limiter import ip_limiter
from src.core.security import create_access_token
from src.database import Base
from src.main import app
from src.users.models import User
from src.users.schemas.users import (
    CreateGuardianAdmin,
    CreateStaffAdmin,
    CreateStudentAdmin,
)
from src.utils.enums import UserRole
from tests.factories import (
    make_director,
    make_guardian,
    make_student,
    make_system_admin,
    make_teacher,
    make_vice_director,
)
from users.repositories.users import UserRepositoryBase

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
async def test_db():
    async with test_engine.connect() as conn:
        await conn.begin()

        session = AsyncSession(bind=conn, expire_on_commit=False)

        async def override_get_db():
            yield session

        app.dependency_overrides[get_db] = override_get_db

        try:
            yield session
        finally:
            try:
                await session.close()
                await conn.rollback()
            except Exception as e:
                print(f"Teardown error: {e}")
            finally:
                app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def client(test_db):
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


@pytest.fixture(scope="function", autouse=True)
def reset_rate_limiter():
    ip_limiter._storage.reset()

    yield


async def make_auth_header(test_db: AsyncSession, user: User) -> dict:
    user_with_session = await UserRepositoryBase.get_user_by_id(
        test_db, user.id, load_session=True
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
async def system_admin(test_db):
    return await make_system_admin(test_db)


@pytest_asyncio.fixture
async def director(test_db):
    return await make_director(test_db)


@pytest_asyncio.fixture
async def vice_director(test_db):
    return await make_vice_director(test_db)


@pytest_asyncio.fixture
async def teacher(test_db):
    return await make_teacher(test_db)


@pytest_asyncio.fixture
async def student(test_db):
    return await make_student(test_db)


@pytest_asyncio.fixture
async def guardian(test_db):
    return await make_guardian(test_db)


create_user_request = {
    "username": "new_test_username",
    "firstname": "New",
    "lastname": "User",
    "email": "new_test_email@gmail.com",
    "phone_number": "+992 111 111 101",
}


@pytest.fixture
def valid_create_staff_request():
    return CreateStaffAdmin(
        **create_user_request,
        type="staff",
        role=UserRole.TEACHER,
    )


@pytest.fixture
def valid_create_guardian_request():
    return CreateGuardianAdmin(
        **create_user_request,
        type="guardian",
    )


@pytest.fixture
def valid_create_student_request():
    return CreateStudentAdmin(
        **create_user_request,
        type="student",
        date_of_birth="2008-05-01",
    )


@pytest.fixture
def mock_advisory_lock(mocker):
    return mocker.patch(
        "src.users.services.system_admin.acquire_student_contact_lock",
        return_value=None,
    )


@pytest.fixture
def mock_acquire_student_contact_lock(mocker):
    return mocker.patch(
        "src.users.services.system_admin.acquire_student_contact_lock",
        return_value=None,
    )


@pytest.fixture
def mock_send_account_info_updated_email(mocker):
    return mocker.patch(
        "src.users.services.system_admin.email_sender.send_account_info_updated_email",
        new_callable=AsyncMock,
    )
