import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.groups.exceptions.exceptions import GroupIsNotArchivedError, GroupNotFoundError
from src.groups.repository import GroupRepository
from src.groups.services.system_admin import GroupServiceAdmin
from src.users.models.user import User
from tests.factories import make_group


class TestRestoreGroup:
    async def test_restores_group_successfully(
        self, session: AsyncSession, system_admin: User
    ):
        group = await make_group(
            session,
            name="RSTO GRP",
            academic_year=2025,
            is_archived=True,
        )

        await GroupServiceAdmin.restore_group(session, system_admin.id, group.id)

        updated = await GroupRepository.get_group_by_id(session, group.id)

        assert updated.is_archived is False
        assert updated.archived_at is None

    async def test_not_found_raises(self, session: AsyncSession, system_admin: User):
        with pytest.raises(GroupNotFoundError):
            await GroupServiceAdmin.restore_group(session, system_admin.id, 999_999)

    async def test_not_archived_raises(self, session: AsyncSession, system_admin: User):
        group = await make_group(session, name="ACTIVE RSTO", academic_year=2025)

        with pytest.raises(GroupIsNotArchivedError):
            await GroupServiceAdmin.restore_group(session, system_admin.id, group.id)

    async def test_cache_invalidated_after_restore(
        self, session: AsyncSession, system_admin: User, mocker
    ):
        group = await make_group(
            session,
            name="CACHE RSTO",
            academic_year=2025,
            is_archived=True,
        )
        calls = []

        async def capture(*args):
            calls.extend(args)

        mocker.patch(
            "src.groups.services.system_admin.delete_cache", side_effect=capture
        )

        await GroupServiceAdmin.restore_group(session, system_admin.id, group.id)

        from src.utils.cache_keys import GroupCacheKey

        assert GroupCacheKey.group_detail_key_admin(group.id) in calls
