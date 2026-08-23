import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.groups.repository import GroupRepository
from src.groups.services.director import GroupServiceDirector
from src.utils.cache_keys import GroupCacheKey
from src.utils.exceptions import GroupNotFoundError
from tests.factories import make_group


class TestDirectorGetGroupById:
    async def test_returns_correct_data(self, session: AsyncSession):
        group = await make_group(session, name="DIR DET GG", academic_year=2025)

        result = await GroupServiceDirector.get_group_by_id(session, group.id)

        assert result.id == group.id
        assert result.name == group.name
        assert result.academic_year == group.academic_year

    async def test_not_found_raises(self, session: AsyncSession):
        with pytest.raises(GroupNotFoundError):
            await GroupServiceDirector.get_group_by_id(session, 999_999)

    async def test_archived_group_is_returned(self, session: AsyncSession):
        group = await make_group(
            session,
            name="DIR ARCH DET",
            academic_year=2025,
            is_archived=True,
        )

        result = await GroupServiceDirector.get_group_by_id(session, group.id)

        assert result.id == group.id
        assert result.is_archived is True

    async def test_response_excludes_archived_at(self, session: AsyncSession):
        group = await make_group(session, name="DIR SCH DET", academic_year=2025)

        result = await GroupServiceDirector.get_group_by_id(session, group.id)

        assert not hasattr(result, "archived_at")

    async def test_populates_cache_after_db_hit(
        self, session: AsyncSession, mocker, mock_set_cache_group_director
    ):
        group = await make_group(session, name="DIR CACHE DET", academic_year=2025)

        await GroupServiceDirector.get_group_by_id(session, group.id)

        mock_set_cache_group_director.assert_called_once_with(
            GroupCacheKey.group_detail_key_staff(group.id),
            mocker.ANY,
            900,
        )

    async def test_does_not_hit_db_on_cache_hit(self, session: AsyncSession, mocker):
        group = await make_group(session, name="DIR CHIT DET", academic_year=2025)

        await GroupServiceDirector.get_group_by_id(session, group.id)

        mock_repo = mocker.patch.object(GroupRepository, "get_group_by_id")

        await GroupServiceDirector.get_group_by_id(session, group.id)

        mock_repo.assert_not_called()

    async def test_returns_same_data_on_cache_hit(self, session: AsyncSession):
        group = await make_group(session, name="DIR SAME DET", academic_year=2025)

        first = await GroupServiceDirector.get_group_by_id(session, group.id)
        second = await GroupServiceDirector.get_group_by_id(session, group.id)

        assert second.id == first.id
        assert second.name == first.name
