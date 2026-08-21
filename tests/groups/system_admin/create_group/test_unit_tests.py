import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.groups.exceptions.exceptions import GroupNameYearAlreadyExistsError
from src.groups.schemas import CreateGroupAdmin
from src.groups.services.system_admin import GroupServiceAdmin
from src.users.models.user import User
from tests.factories import make_group


class TestCreateGroup:
    async def test_creates_group_successfully(
        self, session: AsyncSession, system_admin: User
    ):
        request = CreateGroupAdmin(name="GRP A", academic_year=2025)

        group = await GroupServiceAdmin.create_group(session, system_admin.id, request)

        assert group.id is not None
        assert group.name == "GRP A"
        assert group.academic_year == 2025
        assert group.is_archived is False

    async def test_grade_level_stored_when_provided(
        self, session: AsyncSession, system_admin: User
    ):
        request = CreateGroupAdmin(name="GRP B", academic_year=2025, grade_level=5)

        group = await GroupServiceAdmin.create_group(session, system_admin.id, request)

        assert group.grade_level == 5

    async def test_capacity_stored_when_provided(
        self, session: AsyncSession, system_admin: User
    ):
        request = CreateGroupAdmin(name="GRP C", academic_year=2025, capacity=25)

        group = await GroupServiceAdmin.create_group(session, system_admin.id, request)

        assert group.capacity == 25

    async def test_grade_level_none_when_not_provided(
        self, session: AsyncSession, system_admin: User
    ):
        request = CreateGroupAdmin(name="GRP D", academic_year=2025)

        group = await GroupServiceAdmin.create_group(session, system_admin.id, request)

        assert group.grade_level is None
        assert group.capacity is None

    async def test_duplicate_name_and_year_raises(
        self, session: AsyncSession, system_admin: User
    ):
        await make_group(session, name="DUP GRP", academic_year=2025)

        request = CreateGroupAdmin(name="DUP GRP", academic_year=2025)

        with pytest.raises(GroupNameYearAlreadyExistsError):
            await GroupServiceAdmin.create_group(session, system_admin.id, request)

    async def test_same_name_different_year_succeeds(
        self, session: AsyncSession, system_admin: User
    ):
        await make_group(session, name="SAME GRP", academic_year=2025)

        request = CreateGroupAdmin(name="SAME GRP", academic_year=2026)

        group = await GroupServiceAdmin.create_group(session, system_admin.id, request)

        assert group.id is not None
        assert group.academic_year == 2026
