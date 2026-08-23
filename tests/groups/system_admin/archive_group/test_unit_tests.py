import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.groups.repository import GroupRepository
from src.groups.services.system_admin import GroupServiceAdmin
from src.users.models.user import User
from src.utils.exceptions import (
    GroupAlreadyArchivedError,
    GroupNotFoundError,
)
from tests.factories import make_group


class TestArchiveGroup:
    async def test_archives_group_successfully(
        self, session: AsyncSession, system_admin: User
    ):
        group = await make_group(session, name="ARCH GRP", academic_year=2025)

        await GroupServiceAdmin.archive_group(session, system_admin.id, group.id)

        updated = await GroupRepository.get_group_by_id(session, group.id)

        assert updated.is_archived is True
        assert updated.archived_at is not None

    async def test_not_found_raises(self, session: AsyncSession, system_admin: User):
        with pytest.raises(GroupNotFoundError):
            await GroupServiceAdmin.archive_group(session, system_admin.id, 999_999)

    async def test_already_archived_raises(
        self, session: AsyncSession, system_admin: User
    ):
        group = await make_group(
            session,
            name="ALREADY ARCH",
            academic_year=2025,
            is_archived=True,
        )

        with pytest.raises(GroupAlreadyArchivedError):
            await GroupServiceAdmin.archive_group(session, system_admin.id, group.id)

    async def test_cache_invalidated_after_archive(
        self, session: AsyncSession, system_admin: User, mocker
    ):
        group = await make_group(session, name="CACHE ARCH", academic_year=2025)
        calls = []

        async def capture(*args):
            calls.extend(args)

        mocker.patch(
            "src.groups.services.system_admin.delete_cache", side_effect=capture
        )

        await GroupServiceAdmin.archive_group(session, system_admin.id, group.id)

        from src.utils.cache_keys import GroupCacheKey

        assert GroupCacheKey.group_detail_key_admin(group.id) in calls
