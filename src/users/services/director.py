from sqlalchemy.ext.asyncio import AsyncSession

from src.core.caching import get_cache, set_cache
from src.core.logging import get_logger
from src.core.pagination import PaginatedResponse
from src.users.repositories.user import UserRepositoryBase
from src.users.schemas.director import (
    StudentResponseDirectorCache,
    StudentResponseDirectorDetailed,
    UserResponseDirectorCache,
    UserResponseDirectorDetailed,
)
from src.users.utils.constants import HTTP404, STUDENT_ROLE, TEACHER_ROLE
from src.users.utils.exceptions import UserNotFoundError
from src.users.utils.shared_schemas import SearchUserBase
from src.utils.cache_keys import UserCacheKey
from src.utils.helpers import ensure_exists

logger = get_logger(__name__)


class UserServiceDirector:
    @staticmethod
    async def get_teachers(
        session: AsyncSession,
        skip: int,
        limit: int,
        filters: SearchUserBase,
        sort_by: str,
        order: str,
    ) -> PaginatedResponse:
        teachers, total = await UserRepositoryBase.get_users(
            session,
            skip=skip,
            limit=limit,
            filters=filters,
            sort_by=sort_by,
            order=order,
            allowed_roles=TEACHER_ROLE,
        )

        return PaginatedResponse(
            items=teachers,
            total=total,
            skip=skip,
            limit=limit,
            has_more=skip + limit < total,
        )

    @staticmethod
    async def get_teacher_by_id(
        session: AsyncSession, target_teacher_id: int
    ) -> UserResponseDirectorDetailed:
        cache_key = UserCacheKey.user_detail_key_staff(target_teacher_id)
        cached = await get_cache(cache_key)

        if cached is not None:
            raw = UserResponseDirectorCache.model_validate(cached)

            return UserResponseDirectorDetailed.model_validate(raw.model_dump())

        teacher = await UserRepositoryBase.get_user_by_id(
            session, target_teacher_id, allowed_roles=TEACHER_ROLE
        )
        ensure_exists(teacher, UserNotFoundError(HTTP404.USER))

        raw = UserResponseDirectorCache.model_validate(teacher)
        await set_cache(cache_key, raw.model_dump(mode="json"), 900)

        return UserResponseDirectorDetailed.model_validate(teacher)

    @staticmethod
    async def get_students(
        session: AsyncSession,
        skip: int,
        limit: int,
        group_id: int | None,
        filters: SearchUserBase,
        sort_by: str,
        order: str,
    ) -> PaginatedResponse:
        students, total = await UserRepositoryBase.get_users(
            session,
            skip=skip,
            limit=limit,
            filters=filters,
            sort_by=sort_by,
            order=order,
            allowed_roles=STUDENT_ROLE,
            group_id=group_id,
            load_group=True,
        )

        return PaginatedResponse(
            items=students,
            total=total,
            skip=skip,
            limit=limit,
            has_more=skip + limit < total,
        )

    @staticmethod
    async def get_student_by_id(
        session: AsyncSession, target_student_id: int
    ) -> StudentResponseDirectorDetailed:
        cache_key = UserCacheKey.user_detail_key_staff(target_student_id)
        cached = await get_cache(cache_key)

        if cached is not None:
            raw = StudentResponseDirectorCache.model_validate(cached)

            return StudentResponseDirectorDetailed.model_validate(raw.model_dump())

        student = await UserRepositoryBase.get_user_by_id(
            session,
            target_student_id,
            allowed_roles=STUDENT_ROLE,
            load_group=True,
        )
        ensure_exists(student, UserNotFoundError(HTTP404.USER))

        raw = StudentResponseDirectorCache.model_validate(student)
        await set_cache(cache_key, raw.model_dump(mode="json"), 900)

        return StudentResponseDirectorDetailed.model_validate(student)
