from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool
from tests.factories import (
    make_director,
    make_parent,
    make_student,
    make_system_admin,
    make_teacher,
    make_vice_director,
)

import src.core.caching as cache_module
from src.auth.schemas import CreateAccessToken
from src.core.config import settings
from src.core.dependencies import get_db
from src.core.security import create_access_token
from src.database import Base
from src.main import app
from src.users.models import User
from src.users.repositories.users_admin import UserRepositoryBase

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
    await cache_module.redis_client.flushdb()

    yield

    await cache_module.redis_client.flushdb()


@pytest.fixture
def mock_response():
    return MagicMock()


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
async def parent(test_db):
    return await make_parent(test_db)


@pytest.fixture
def mock_delete_cache(mocker):
    return mocker.patch("src.users.service.delete_cache")


@pytest.fixture
def mock_set_cache(mocker):
    return mocker.patch("src.users.service.set_cache")
