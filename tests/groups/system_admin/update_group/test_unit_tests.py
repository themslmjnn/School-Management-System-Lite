import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.groups.repository import GroupRepository
from src.groups.schemas import UpdateGroupAdmin
from src.groups.services.system_admin import GroupServiceAdmin
from src.users.models.user import User
from src.utils.exceptions import (
    GroupNameYearAlreadyExistsError,
    GroupNotFoundError,
    NoChangesDetectedError,
)
from tests.factories import make_group


class TestUpdateGroup:
    async def test_updates_name_successfully(
        self, session: AsyncSession, system_admin: User
    ):
        group = await make_group(session, name="OLD GRP", academic_year=2025)

        await GroupServiceAdmin.update_group(
            session,
            system_admin.id,
            group.id,
            UpdateGroupAdmin(name="NEW GRP"),
        )

        updated = await GroupRepository.get_group_by_id(session, group.id)

        assert updated.name == "NEW GRP"

    async def test_updates_capacity_successfully(
        self, session: AsyncSession, system_admin: User
    ):
        group = await make_group(
            session, name="CAP GRP", academic_year=2025, capacity=20
        )

        await GroupServiceAdmin.update_group(
            session,
            system_admin.id,
            group.id,
            UpdateGroupAdmin(name="CAP GRP", capacity=35),
        )

        updated = await GroupRepository.get_group_by_id(session, group.id)

        assert updated.capacity == 35

    async def test_updates_grade_level_successfully(
        self, session: AsyncSession, system_admin: User
    ):
        group = await make_group(
            session, name="GRD GRP", academic_year=2025, grade_level=3
        )

        await GroupServiceAdmin.update_group(
            session,
            system_admin.id,
            group.id,
            UpdateGroupAdmin(name="GRD GRP", grade_level=5),
        )

        updated = await GroupRepository.get_group_by_id(session, group.id)

        assert updated.grade_level == 5

    async def test_not_found_raises(self, session: AsyncSession, system_admin: User):
        with pytest.raises(GroupNotFoundError):
            await GroupServiceAdmin.update_group(
                session,
                system_admin.id,
                999_999,
                UpdateGroupAdmin(name="JUSTNAME"),
            )

    async def test_no_changes_raises(self, session: AsyncSession, system_admin: User):
        group = await make_group(session, name="NOCH GRP", academic_year=2025)

        with pytest.raises(NoChangesDetectedError):
            await GroupServiceAdmin.update_group(
                session,
                system_admin.id,
                group.id,
                UpdateGroupAdmin(name=group.name),
            )

    async def test_duplicate_name_same_year_raises(
        self, session: AsyncSession, system_admin: User
    ):
        await make_group(session, name="TAKEN GRP", academic_year=2025)
        target = await make_group(session, name="TARGET GRP", academic_year=2025)

        with pytest.raises(GroupNameYearAlreadyExistsError):
            await GroupServiceAdmin.update_group(
                session,
                system_admin.id,
                target.id,
                UpdateGroupAdmin(name="TAKEN GRP"),
            )

    async def test_cache_invalidated_after_update(
        self, session: AsyncSession, system_admin: User, mocker
    ):
        group = await make_group(session, name="CACHE GRP", academic_year=2025)
        calls = []

        async def capture(*args):
            calls.extend(args)

        mocker.patch(
            "src.groups.services.system_admin.delete_cache", side_effect=capture
        )

        await GroupServiceAdmin.update_group(
            session,
            system_admin.id,
            group.id,
            UpdateGroupAdmin(name="CACHE"),
        )

        from src.utils.cache_keys import GroupCacheKey

        assert GroupCacheKey.group_detail_key_admin(group.id) in calls
        assert GroupCacheKey.group_detail_key_staff(group.id) in calls
