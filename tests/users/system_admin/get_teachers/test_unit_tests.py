from sqlalchemy.ext.asyncio import AsyncSession

from src.users.schemas.system_admin import SearchUserAdmin
from src.users.services.system_admin import UserServiceAdmin
from src.utils.enums import OrderBy, UserSortField, UserStatus
from tests.factories import (
    make_director,
    make_student,
    make_system_admin,
    make_teacher,
)


class TestGetTeachers:
    async def test_returns_only_staff_roles(self, session: AsyncSession):
        teacher = await make_teacher(session)
        await make_student(session)
        await make_system_admin(session)
        await make_director(session)

        result = await UserServiceAdmin.get_teachers(
            session,
            skip=0,
            limit=100,
            filters=SearchUserAdmin(),
            sort_by=UserSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        returned_ids = {u.id for u in result.items}

        assert returned_ids == {teacher.id}
        assert result.total == 1

    async def test_has_more_true_when_results_exceed_limit(self, session: AsyncSession):
        for i in range(3):
            await make_teacher(session, username=f"staff_page_{i}")

        result = await UserServiceAdmin.get_teachers(
            session,
            skip=0,
            limit=2,
            filters=SearchUserAdmin(),
            sort_by=UserSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        assert len(result.items) == 2
        assert result.total == 3
        assert result.has_more is True

    async def test_has_more_false_on_final_page(self, session: AsyncSession):
        for i in range(3):
            await make_teacher(session, username=f"staff_last_page_{i}")

        result = await UserServiceAdmin.get_teachers(
            session,
            skip=2,
            limit=2,
            filters=SearchUserAdmin(),
            sort_by=UserSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        assert len(result.items) == 1
        assert result.has_more is False

    async def test_sort_by_lastname_ascending(self, session: AsyncSession):
        z_teacher = await make_teacher(session, lastname="Zephyr")
        a_teacher = await make_teacher(session, lastname="Anders")

        result = await UserServiceAdmin.get_teachers(
            session,
            skip=0,
            limit=100,
            filters=SearchUserAdmin(),
            sort_by=UserSortField.LASTNAME,
            order=OrderBy.ASC,
        )

        ids_in_order = [u.id for u in result.items]

        assert ids_in_order.index(a_teacher.id) < ids_in_order.index(z_teacher.id)

    async def test_sort_by_lastname_descending(self, session: AsyncSession):
        z_teacher = await make_teacher(session, lastname="Zephyr")
        a_teacher = await make_teacher(session, lastname="Anders")

        result = await UserServiceAdmin.get_teachers(
            session,
            skip=0,
            limit=100,
            filters=SearchUserAdmin(),
            sort_by=UserSortField.LASTNAME,
            order=OrderBy.DESC,
        )

        ids_in_order = [u.id for u in result.items]

        assert ids_in_order.index(z_teacher.id) < ids_in_order.index(a_teacher.id)

    async def test_invalid_sort_field_falls_back_to_created_at(
        self, session: AsyncSession
    ):
        await make_teacher(session)
        await make_teacher(session, username="staff_fallback_2")

        result = await UserServiceAdmin.get_teachers(
            session,
            skip=0,
            limit=100,
            filters=SearchUserAdmin(),
            sort_by="not_a_real_field",
            order=OrderBy.DESC,
        )

        assert result.total == 2

    async def test_filter_by_username_substring(self, session: AsyncSession):
        target = await make_teacher(session, username="findable_staff")
        await make_teacher(session, username="unrelated_person")

        result = await UserServiceAdmin.get_teachers(
            session,
            skip=0,
            limit=100,
            filters=SearchUserAdmin(username="findable"),
            sort_by=UserSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        returned_ids = {u.id for u in result.items}

        assert returned_ids == {target.id}

    async def test_filter_by_email_substring(self, session: AsyncSession):
        target = await make_teacher(session, email="findable_email@example.com")
        await make_teacher(session, email="unrelated@example.com")

        result = await UserServiceAdmin.get_teachers(
            session,
            skip=0,
            limit=100,
            filters=SearchUserAdmin(email="findable_email"),
            sort_by=UserSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        returned_ids = {u.id for u in result.items}

        assert returned_ids == {target.id}

    async def test_filter_by_phone_number_substring(self, session: AsyncSession):
        target = await make_teacher(session, phone_number="+15559998888")
        await make_teacher(session, phone_number="+15551112222")

        result = await UserServiceAdmin.get_teachers(
            session,
            skip=0,
            limit=100,
            filters=SearchUserAdmin(phone_number="9998888"),
            sort_by=UserSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        returned_ids = {u.id for u in result.items}

        assert returned_ids == {target.id}

    async def test_filter_by_firstname_substring(self, session: AsyncSession):
        target = await make_teacher(session, firstname="Jonathan")
        await make_teacher(session, firstname="Zack")

        result = await UserServiceAdmin.get_teachers(
            session,
            skip=0,
            limit=100,
            filters=SearchUserAdmin(firstname="Jonathan"),
            sort_by=UserSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        returned_ids = {u.id for u in result.items}

        assert returned_ids == {target.id}

    async def test_filter_by_lastname_substring(self, session: AsyncSession):
        target = await make_teacher(session, lastname="Smithers")
        await make_teacher(session, lastname="Zephyr")

        result = await UserServiceAdmin.get_teachers(
            session,
            skip=0,
            limit=100,
            filters=SearchUserAdmin(lastname="Smithers"),
            sort_by=UserSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        returned_ids = {u.id for u in result.items}

        assert returned_ids == {target.id}

    async def test_filter_by_middlename_substring(self, session: AsyncSession):
        target = await make_teacher(session, middlename="Andrew")
        await make_teacher(session, middlename="Zane")

        result = await UserServiceAdmin.get_teachers(
            session,
            skip=0,
            limit=100,
            filters=SearchUserAdmin(middlename="Andrew"),
            sort_by=UserSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        returned_ids = {u.id for u in result.items}

        assert returned_ids == {target.id}

    async def test_filter_by_status(self, session: AsyncSession):
        deactivated = await make_teacher(
            session, status=UserStatus.DEACTIVATED, is_active=False
        )
        await make_teacher(session, status=UserStatus.ACTIVE)

        result = await UserServiceAdmin.get_teachers(
            session,
            skip=0,
            limit=100,
            filters=SearchUserAdmin(status=UserStatus.DEACTIVATED),
            sort_by=UserSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        returned_ids = {u.id for u in result.items}

        assert returned_ids == {deactivated.id}

    async def test_filters_object_is_not_mutated_by_get_teachers(
        self, session: AsyncSession
    ):
        filters = SearchUserAdmin()

        await UserServiceAdmin.get_teachers(
            session,
            skip=0,
            limit=10,
            filters=filters,
            sort_by=UserSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        assert not hasattr(filters, "allowed_roles")
