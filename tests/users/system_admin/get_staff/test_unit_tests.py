from sqlalchemy.ext.asyncio import AsyncSession

from users.schemas.system_admin import SearchUserAdmin
from users.services.system_admin import UserServiceAdmin
from src.utils.enums import OrderBy, UserSortField, UserStatus
from tests.factories import (
    make_director,
    make_guardian,
    make_student,
    make_system_admin,
    make_teacher,
    make_vice_director,
)


class TestGetStaff:
    async def test_returns_only_staff_roles(self, test_db: AsyncSession):
        teacher = await make_teacher(test_db)
        vice_director = await make_vice_director(test_db)
        await make_student(test_db)
        await make_guardian(test_db)
        await make_system_admin(test_db)
        await make_director(test_db)

        result = await UserServiceAdmin.get_staff(
            test_db,
            skip=0,
            limit=100,
            filters=SearchUserAdmin(),
            sort_by=UserSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        returned_ids = {u.id for u in result.items}

        assert returned_ids == {teacher.id, vice_director.id}
        assert result.total == 2

    async def test_has_more_true_when_results_exceed_limit(self, test_db: AsyncSession):
        for i in range(3):
            await make_teacher(test_db, username=f"staff_page_{i}")

        result = await UserServiceAdmin.get_staff(
            test_db,
            skip=0,
            limit=2,
            filters=SearchUserAdmin(),
            sort_by=UserSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        assert len(result.items) == 2
        assert result.total == 3
        assert result.has_more is True

    async def test_has_more_false_on_final_page(self, test_db: AsyncSession):
        for i in range(3):
            await make_teacher(test_db, username=f"staff_last_page_{i}")

        result = await UserServiceAdmin.get_staff(
            test_db,
            skip=2,
            limit=2,
            filters=SearchUserAdmin(),
            sort_by=UserSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        assert len(result.items) == 1
        assert result.has_more is False

    async def test_sort_by_lastname_ascending(self, test_db: AsyncSession):
        z_teacher = await make_teacher(test_db, lastname="Zephyr")
        a_teacher = await make_teacher(test_db, lastname="Anders")

        result = await UserServiceAdmin.get_staff(
            test_db,
            skip=0,
            limit=100,
            filters=SearchUserAdmin(),
            sort_by=UserSortField.LASTNAME,
            order=OrderBy.ASC,
        )

        ids_in_order = [u.id for u in result.items]

        assert ids_in_order.index(a_teacher.id) < ids_in_order.index(z_teacher.id)

    async def test_sort_by_lastname_descending(self, test_db: AsyncSession):
        z_teacher = await make_teacher(test_db, lastname="Zephyr")
        a_teacher = await make_teacher(test_db, lastname="Anders")

        result = await UserServiceAdmin.get_staff(
            test_db,
            skip=0,
            limit=100,
            filters=SearchUserAdmin(),
            sort_by=UserSortField.LASTNAME,
            order=OrderBy.DESC,
        )

        ids_in_order = [u.id for u in result.items]

        assert ids_in_order.index(z_teacher.id) < ids_in_order.index(a_teacher.id)

    async def test_invalid_sort_field_falls_back_to_created_at(
        self, test_db: AsyncSession
    ):
        await make_teacher(test_db)
        await make_teacher(test_db, username="staff_fallback_2")

        result = await UserServiceAdmin.get_staff(
            test_db,
            skip=0,
            limit=100,
            filters=SearchUserAdmin(),
            sort_by="not_a_real_field",
            order=OrderBy.DESC,
        )

        assert result.total == 2

    async def test_filter_by_username_substring(self, test_db: AsyncSession):
        target = await make_teacher(test_db, username="findable_staff")
        await make_teacher(test_db, username="unrelated_person")

        result = await UserServiceAdmin.get_staff(
            test_db,
            skip=0,
            limit=100,
            filters=SearchUserAdmin(username="findable"),
            sort_by=UserSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        returned_ids = {u.id for u in result.items}

        assert returned_ids == {target.id}

    async def test_filter_by_email_substring(self, test_db: AsyncSession):
        target = await make_teacher(test_db, email="findable_email@example.com")
        await make_teacher(test_db, email="unrelated@example.com")

        result = await UserServiceAdmin.get_staff(
            test_db,
            skip=0,
            limit=100,
            filters=SearchUserAdmin(email="findable_email"),
            sort_by=UserSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        returned_ids = {u.id for u in result.items}

        assert returned_ids == {target.id}

    async def test_filter_by_phone_number_substring(self, test_db: AsyncSession):
        target = await make_teacher(test_db, phone_number="+15559998888")
        await make_teacher(test_db, phone_number="+15551112222")

        result = await UserServiceAdmin.get_staff(
            test_db,
            skip=0,
            limit=100,
            filters=SearchUserAdmin(phone_number="9998888"),
            sort_by=UserSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        returned_ids = {u.id for u in result.items}

        assert returned_ids == {target.id}

    async def test_filter_by_firstname_substring(self, test_db: AsyncSession):
        target = await make_teacher(test_db, firstname="Jonathan")
        await make_teacher(test_db, firstname="Zack")

        result = await UserServiceAdmin.get_staff(
            test_db,
            skip=0,
            limit=100,
            filters=SearchUserAdmin(firstname="Jonathan"),
            sort_by=UserSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        returned_ids = {u.id for u in result.items}

        assert returned_ids == {target.id}

    async def test_filter_by_lastname_substring(self, test_db: AsyncSession):
        target = await make_teacher(test_db, lastname="Smithers")
        await make_teacher(test_db, lastname="Zephyr")

        result = await UserServiceAdmin.get_staff(
            test_db,
            skip=0,
            limit=100,
            filters=SearchUserAdmin(lastname="Smithers"),
            sort_by=UserSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        returned_ids = {u.id for u in result.items}

        assert returned_ids == {target.id}

    async def test_filter_by_middlename_substring(self, test_db: AsyncSession):
        target = await make_teacher(test_db, middlename="Andrew")
        await make_teacher(test_db, middlename="Zane")

        result = await UserServiceAdmin.get_staff(
            test_db,
            skip=0,
            limit=100,
            filters=SearchUserAdmin(middlename="Andrew"),
            sort_by=UserSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        returned_ids = {u.id for u in result.items}

        assert returned_ids == {target.id}

    async def test_filter_by_status(self, test_db: AsyncSession):
        deactivated = await make_teacher(
            test_db, status=UserStatus.DEACTIVATED, is_active=False
        )
        await make_teacher(test_db, status=UserStatus.ACTIVE)

        result = await UserServiceAdmin.get_staff(
            test_db,
            skip=0,
            limit=100,
            filters=SearchUserAdmin(status=UserStatus.DEACTIVATED),
            sort_by=UserSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        returned_ids = {u.id for u in result.items}

        assert returned_ids == {deactivated.id}

    async def test_filters_object_is_not_mutated_by_get_staff(
        self, test_db: AsyncSession
    ):
        filters = SearchUserAdmin()

        await UserServiceAdmin.get_staff(
            test_db,
            skip=0,
            limit=10,
            filters=filters,
            sort_by=UserSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        assert not hasattr(filters, "allowed_roles")
