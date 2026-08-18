from sqlalchemy.ext.asyncio import AsyncSession

from src.users.services.director import UserServiceDirector
from src.users.utils.shared_schemas import SearchUserBase
from src.utils.enums import OrderBy, UserSortField, UserStatus
from tests.factories import (
    make_director,
    make_student,
    make_system_admin,
    make_teacher,
)


class TestGetTeachers:
    async def test_returns_only_teacher_role(self, session: AsyncSession):
        teacher = await make_teacher(session)
        await make_student(session)
        await make_system_admin(session)
        await make_director(session)

        result = await UserServiceDirector.get_teachers(
            session,
            skip=0,
            limit=100,
            filters=SearchUserBase(),
            sort_by=UserSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        returned_ids = {u.id for u in result.items}

        assert returned_ids == {teacher.id}
        assert result.total == 1

    async def test_has_more_true_when_results_exceed_limit(self, session: AsyncSession):
        for i in range(3):
            await make_teacher(session, username=f"teacher_page_{i}")

        result = await UserServiceDirector.get_teachers(
            session,
            skip=0,
            limit=2,
            filters=SearchUserBase(),
            sort_by=UserSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        assert len(result.items) == 2
        assert result.total == 3
        assert result.has_more is True

    async def test_has_more_false_on_final_page(self, session: AsyncSession):
        for i in range(3):
            await make_teacher(session, username=f"teacher_last_{i}")

        result = await UserServiceDirector.get_teachers(
            session,
            skip=2,
            limit=2,
            filters=SearchUserBase(),
            sort_by=UserSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        assert len(result.items) == 1
        assert result.has_more is False

    async def test_filter_by_firstname_substring(self, session: AsyncSession):
        target = await make_teacher(session, firstname="Uniquename")
        await make_teacher(session, firstname="Other")

        result = await UserServiceDirector.get_teachers(
            session,
            skip=0,
            limit=100,
            filters=SearchUserBase(firstname="Uniquename"),
            sort_by=UserSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        returned_ids = {u.id for u in result.items}

        assert returned_ids == {target.id}

    async def test_filter_by_status(self, session: AsyncSession):
        deactivated = await make_teacher(
            session,
            username="deactivated_teacher",
            status=UserStatus.DEACTIVATED,
            is_active=False,
        )
        await make_teacher(session, username="active_teacher")

        result = await UserServiceDirector.get_teachers(
            session,
            skip=0,
            limit=100,
            filters=SearchUserBase(status=UserStatus.DEACTIVATED),
            sort_by=UserSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        returned_ids = {u.id for u in result.items}

        assert returned_ids == {deactivated.id}

    async def test_sort_by_lastname_ascending(self, session: AsyncSession):
        z_teacher = await make_teacher(session, lastname="Zephyr")
        a_teacher = await make_teacher(session, lastname="Anders")

        result = await UserServiceDirector.get_teachers(
            session,
            skip=0,
            limit=100,
            filters=SearchUserBase(),
            sort_by=UserSortField.LASTNAME,
            order=OrderBy.ASC,
        )

        ids_in_order = [u.id for u in result.items]

        assert ids_in_order.index(a_teacher.id) < ids_in_order.index(z_teacher.id)
