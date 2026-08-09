from sqlalchemy.ext.asyncio import AsyncSession

from users.schemas.system_admin.user import SearchUserAdmin
from src.users.services.system_admin.user import UserServiceAdmin
from src.utils.enums import OrderBy, UserSortField
from tests.factories import (
    make_guardian,
    make_student,
    make_system_admin,
    make_teacher,
)


class TestGetGuardians:
    async def test_returns_only_guardians(self, test_db: AsyncSession):
        guardian = await make_guardian(test_db)
        await make_teacher(test_db)
        await make_student(test_db)
        await make_system_admin(test_db)

        result = await UserServiceAdmin.get_guardians(
            test_db,
            skip=0,
            limit=100,
            filters=SearchUserAdmin(),
            sort_by=UserSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        returned_roles = {u.role for u in result.items}

        assert returned_roles == {guardian.role}
        assert result.total == 1

    async def test_has_more_true_when_results_exceed_limit(self, test_db: AsyncSession):
        for i in range(3):
            await make_guardian(test_db, username=f"guardian_page_{i}")

        result = await UserServiceAdmin.get_guardians(
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
            await make_guardian(test_db, username=f"guardian_last_{i}")

        result = await UserServiceAdmin.get_guardians(
            test_db,
            skip=2,
            limit=2,
            filters=SearchUserAdmin(),
            sort_by=UserSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        assert len(result.items) == 1
        assert result.has_more is False

    async def test_filter_by_username_substring(self, test_db: AsyncSession):
        target = await make_guardian(test_db, username="findable_guardian")
        await make_guardian(test_db, username="unrelated_person")

        result = await UserServiceAdmin.get_guardians(
            test_db,
            skip=0,
            limit=100,
            filters=SearchUserAdmin(username="findable"),
            sort_by=UserSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        returned_roles = {u.role for u in result.items}

        assert returned_roles == {target.role}

    async def test_filter_by_is_active_false(self, test_db: AsyncSession):
        inactive = await make_guardian(test_db, is_active=False)
        await make_guardian(test_db, is_active=True)

        result = await UserServiceAdmin.get_guardians(
            test_db,
            skip=0,
            limit=100,
            filters=SearchUserAdmin(is_active=False),
            sort_by=UserSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        returned_roles = {u.role for u in result.items}

        assert returned_roles == {inactive.role}
