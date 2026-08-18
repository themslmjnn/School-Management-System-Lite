import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models.user import User
from src.users.repositories.user import UserRepositoryBase
from src.users.services.director import UserServiceDirector
from src.users.utils.exceptions import UserNotFoundError
from src.utils.cache_keys import UserCacheKey
from src.utils.enums import UserRole
from tests.factories import (
    make_director,
    make_group,
    make_student,
    make_system_admin,
    make_teacher,
)


class TestGetStudentById:
    async def test_returns_correct_data(self, session: AsyncSession, student: User):
        result = await UserServiceDirector.get_student_by_id(session, student.id)

        assert result.id == student.id
        assert result.role == UserRole.STUDENT

    async def test_returns_404_when_not_found(self, session: AsyncSession):
        with pytest.raises(UserNotFoundError):
            await UserServiceDirector.get_student_by_id(session, 999_999)

    @pytest.mark.parametrize(
        "factory",
        [make_teacher, make_director, make_system_admin],
    )
    async def test_returns_404_for_non_student_role(
        self, session: AsyncSession, factory
    ):
        non_student = await factory(session)

        with pytest.raises(UserNotFoundError):
            await UserServiceDirector.get_student_by_id(session, non_student.id)

    async def test_group_is_none_when_student_has_no_group(
        self, session: AsyncSession, student: User
    ):
        result = await UserServiceDirector.get_student_by_id(session, student.id)

        assert result.group is None

    async def test_group_is_populated_when_student_has_group(
        self, session: AsyncSession
    ):
        group = await make_group(session)
        student = await make_student(
            session, username="grouped_student", group_id=group.id
        )

        result = await UserServiceDirector.get_student_by_id(session, student.id)

        assert result.group is not None
        assert result.group.name == group.name

    async def test_populates_cache_after_db_hit(
        self,
        session: AsyncSession,
        student: User,
        mock_set_cache_user_director,
        mocker,
    ):
        await UserServiceDirector.get_student_by_id(session, student.id)

        mock_set_cache_user_director.assert_called_once_with(
            UserCacheKey.user_detail_key_staff(student.id),
            mocker.ANY,
            900,
        )

    async def test_does_not_hit_db_on_cache_hit(
        self, session: AsyncSession, student: User, mocker
    ):
        await UserServiceDirector.get_student_by_id(session, student.id)

        mock_repo = mocker.patch.object(UserRepositoryBase, "get_user_by_id")

        await UserServiceDirector.get_student_by_id(session, student.id)

        mock_repo.assert_not_called()

    async def test_returns_same_data_on_cache_hit(
        self, session: AsyncSession, student: User
    ):
        first = await UserServiceDirector.get_student_by_id(session, student.id)
        second = await UserServiceDirector.get_student_by_id(session, student.id)

        assert second.id == first.id
        assert second.date_of_birth == first.date_of_birth
