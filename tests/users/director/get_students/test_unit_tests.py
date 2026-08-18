from sqlalchemy.ext.asyncio import AsyncSession

from src.users.services.director import UserServiceDirector
from src.users.utils.shared_schemas import SearchUserBase
from src.utils.enums import OrderBy, UserSortField, UserStatus
from tests.factories import (
    make_director,
    make_group,
    make_student,
    make_system_admin,
    make_teacher,
)


class TestGetStudents:
    async def test_returns_only_student_role(self, session: AsyncSession):
        student = await make_student(session)
        await make_teacher(session)
        await make_system_admin(session)
        await make_director(session)

        result = await UserServiceDirector.get_students(
            session,
            skip=0,
            limit=100,
            group_id=None,
            filters=SearchUserBase(),
            sort_by=UserSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        returned_ids = {u.id for u in result.items}

        assert returned_ids == {student.id}
        assert result.total == 1

        result = await UserServiceDirector.get_student_by_id(session, student.id)
        assert not hasattr(result, "email")

    async def test_has_more_true_when_results_exceed_limit(self, session: AsyncSession):
        for i in range(3):
            await make_student(session, username=f"student_page_{i}")

        result = await UserServiceDirector.get_students(
            session,
            skip=0,
            limit=2,
            group_id=None,
            filters=SearchUserBase(),
            sort_by=UserSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        assert len(result.items) == 2
        assert result.total == 3
        assert result.has_more is True

    async def test_has_more_false_on_final_page(self, session: AsyncSession):
        for i in range(3):
            await make_student(session, username=f"student_last_{i}")

        result = await UserServiceDirector.get_students(
            session,
            skip=2,
            limit=2,
            group_id=None,
            filters=SearchUserBase(),
            sort_by=UserSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        assert len(result.items) == 1
        assert result.has_more is False

    async def test_filter_by_group_id(self, session: AsyncSession):
        group = await make_group(session)
        in_group = await make_student(
            session, username="in_group_student", group_id=group.id
        )
        await make_student(session, username="no_group_student")

        result = await UserServiceDirector.get_students(
            session,
            skip=0,
            limit=100,
            group_id=group.id,
            filters=SearchUserBase(),
            sort_by=UserSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        returned_ids = {u.id for u in result.items}

        assert returned_ids == {in_group.id}

    async def test_group_none_when_student_has_no_group(self, session: AsyncSession):
        await make_student(session, username="ungrouped_student")

        result = await UserServiceDirector.get_students(
            session,
            skip=0,
            limit=100,
            group_id=None,
            filters=SearchUserBase(),
            sort_by=UserSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        assert result.items[0].group is None

    async def test_group_populated_when_student_has_group(self, session: AsyncSession):
        group = await make_group(session, name="Group B")
        await make_student(session, username="grouped_student", group_id=group.id)

        result = await UserServiceDirector.get_students(
            session,
            skip=0,
            limit=100,
            group_id=None,
            filters=SearchUserBase(),
            sort_by=UserSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        assert result.items[0].group is not None
        assert result.items[0].group.id == group.id

    async def test_sort_by_lastname_ascending(self, session: AsyncSession):
        z_student = await make_student(session, lastname="Zephyr")
        a_student = await make_student(session, lastname="Anders")

        result = await UserServiceDirector.get_students(
            session,
            skip=0,
            limit=100,
            group_id=None,
            filters=SearchUserBase(),
            sort_by=UserSortField.LASTNAME,
            order=OrderBy.ASC,
        )

        ids_in_order = [u.id for u in result.items]

        assert ids_in_order.index(a_student.id) < ids_in_order.index(z_student.id)

    async def test_filter_by_firstname_substring(self, session: AsyncSession):
        target = await make_student(session, firstname="Unique")
        await make_student(session, firstname="Other")

        result = await UserServiceDirector.get_students(
            session,
            skip=0,
            limit=100,
            group_id=None,
            filters=SearchUserBase(firstname="Unique"),
            sort_by=UserSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        returned_ids = {u.id for u in result.items}

        assert returned_ids == {target.id}

    async def test_filter_by_status(self, session: AsyncSession):
        deactivated = await make_student(
            session,
            username="deactivated_student",
            status=UserStatus.DEACTIVATED,
            is_active=False,
        )
        await make_student(session, username="active_student")

        result = await UserServiceDirector.get_students(
            session,
            skip=0,
            limit=100,
            group_id=None,
            filters=SearchUserBase(status=UserStatus.DEACTIVATED),
            sort_by=UserSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        returned_ids = {u.id for u in result.items}

        assert returned_ids == {deactivated.id}

    async def test_invalid_sort_field_falls_back_to_created_at(
        self, session: AsyncSession
    ):
        await make_student(session, username="student_fallback_1")
        await make_student(session, username="student_fallback_2")

        result = await UserServiceDirector.get_students(
            session,
            skip=0,
            limit=100,
            group_id=None,
            filters=SearchUserBase(),
            sort_by="not_a_real_field",
            order=OrderBy.DESC,
        )

        assert result.total == 2
