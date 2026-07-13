from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Query, Request
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.caching import get_cache, set_cache
from src.core.security import decode_access_token
from src.database import AsyncSessionLocal
from src.users.repositories.users import UserRepositoryBase
from src.utils.cache_keys import SessionCacheKey
from src.utils.constants import HTTP401, HTTP403
from src.utils.enums import UserRole
from src.utils.exceptions import (
    AccessDeniedError,
    AccountInactiveError,
    InvalidAccessTokenError,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async_db_dependency = Annotated[AsyncSession, Depends(get_db)]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@dataclass
class CurrentUser:
    id: int
    role: UserRole


async def get_current_user(
    request: Request, db: async_db_dependency, token: str = Depends(oauth2_scheme)
) -> CurrentUser:
    try:
        payload = decode_access_token(token)

        user_id = int(payload.get("sub"))
        token_version = int(payload.get("version"))

    except (ValueError, TypeError) as err:
        raise InvalidAccessTokenError(HTTP401.INVALID_ACCESS_TOKEN) from err

    user_access_token_version_key = SessionCacheKey.access_token_version_key(user_id)

    cached_version = await get_cache(user_access_token_version_key)
    if cached_version is not None:
        if int(cached_version) != token_version:
            raise InvalidAccessTokenError(HTTP401.INVALID_ACCESS_TOKEN)

        return CurrentUser(
            id=user_id,
            role=UserRole(payload.get("role")),
        )

    user = await UserRepositoryBase.get_user_by_id(db, user_id, load_session=True)

    if user is None:
        raise InvalidAccessTokenError(HTTP401.INVALID_ACCESS_TOKEN)

    if user.session.access_token_version != token_version:
        raise InvalidAccessTokenError(HTTP401.INVALID_ACCESS_TOKEN)

    if not user.is_active:
        raise AccountInactiveError(HTTP403.ACCOUNT_DEACTIVATED)

    await set_cache(
        user_access_token_version_key,
        user.session.access_token_version,
        ttl_seconds=300,
    )

    current_user = CurrentUser(
        id=user_id,
        role=UserRole(payload.get("role")),
    )

    request.state.user = current_user

    return current_user


current_user_dependency = Annotated[CurrentUser, Depends(get_current_user)]


def require_roles(*roles: UserRole):
    def guard(current_user: current_user_dependency) -> CurrentUser:
        if current_user.role not in roles:
            raise AccessDeniedError(HTTP403.ACCESS_DENIED)

        return current_user

    return guard


require_system_admin = require_roles(UserRole.SYSTEM_ADMIN)
require_directors = require_roles(UserRole.DIRECTOR, UserRole.VICE_DIRECTOR)
require_system_admin_and_guardian = require_roles(
    UserRole.SYSTEM_ADMIN, UserRole.GUARDIAN
)
require_guardian = require_roles(UserRole.GUARDIAN)


class PaginationParams(BaseModel):
    skip: int = Query(ge=0, default=0)
    limit: int = Query(ge=1, le=100, default=10)


pagination_dependency = Annotated[PaginationParams, Depends(PaginationParams)]
