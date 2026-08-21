from sqlalchemy.ext.asyncio import AsyncSession

from src.groups.schemas import SearchGroupBase
from src.groups.services.director import GroupServiceDirector
from src.utils.enums import GroupSortField, OrderBy
from tests.factories import make_group


class TestDirectorGetGroups:
    async def test_returns_only_non_archived(self, session: AsyncSession):
        active = await make_group(session, name="DIR ACT GG", academic_year=2025)
        await make_group(
            session,
            name="DIR ARCH GG",
            academic_year=2025,
            is_archived=True,
        )

        result = await GroupServiceDirector.get_groups(
            session,
            skip=0,
            limit=100,
            filters=SearchGroupBase(),
            sort_by=GroupSortField.ACADEMIC_YEAR,
            order=OrderBy.DESC,
        )

        returned_ids = {g.id for g in result.items}

        assert active.id in returned_ids
        assert result.total == 1

    async def test_filter_by_name_substring(self, session: AsyncSession):
        target = await make_group(session, name="DIR FIND", academic_year=2025)
        await make_group(session, name="DIR OTHER", academic_year=2025)

        result = await GroupServiceDirector.get_groups(
            session,
            skip=0,
            limit=100,
            filters=SearchGroupBase(name="FIND"),
            sort_by=GroupSortField.ACADEMIC_YEAR,
            order=OrderBy.DESC,
        )

        returned_ids = {g.id for g in result.items}

        assert returned_ids == {target.id}

    async def test_filter_by_academic_year(self, session: AsyncSession):
        target = await make_group(session, name="DIR YR GG", academic_year=2022)
        await make_group(session, name="DIR OTH YR", academic_year=2023)

        result = await GroupServiceDirector.get_groups(
            session,
            skip=0,
            limit=100,
            filters=SearchGroupBase(academic_year=2022),
            sort_by=GroupSortField.ACADEMIC_YEAR,
            order=OrderBy.DESC,
        )

        returned_ids = {g.id for g in result.items}

        assert returned_ids == {target.id}

    async def test_sort_by_academic_year_descending(self, session: AsyncSession):
        older = await make_group(session, name="DIR OLDER", academic_year=2021)
        newer = await make_group(session, name="DIR NEWER", academic_year=2027)

        result = await GroupServiceDirector.get_groups(
            session,
            skip=0,
            limit=100,
            filters=SearchGroupBase(),
            sort_by=GroupSortField.ACADEMIC_YEAR,
            order=OrderBy.DESC,
        )

        ids_in_order = [g.id for g in result.items]

        assert ids_in_order.index(newer.id) < ids_in_order.index(older.id)

    async def test_has_more_true_when_results_exceed_limit(self, session: AsyncSession):
        for i in range(3):
            await make_group(session, name=f"DIR PG GG{i}", academic_year=2050 + i)

        result = await GroupServiceDirector.get_groups(
            session,
            skip=0,
            limit=2,
            filters=SearchGroupBase(),
            sort_by=GroupSortField.ACADEMIC_YEAR,
            order=OrderBy.DESC,
        )

        assert len(result.items) == 2
        assert result.total == 3
        assert result.has_more is True

    async def test_has_more_false_on_final_page(self, session: AsyncSession):
        for i in range(3):
            await make_group(session, name=f"DIR FIN GG{i}", academic_year=2060 + i)

        result = await GroupServiceDirector.get_groups(
            session,
            skip=2,
            limit=2,
            filters=SearchGroupBase(),
            sort_by=GroupSortField.ACADEMIC_YEAR,
            order=OrderBy.DESC,
        )

        assert len(result.items) == 1
        assert result.has_more is False

    async def test_cannot_include_archived(self, session: AsyncSession):
        await make_group(session, name="DIR ONLY ACT", academic_year=2025)
        await make_group(
            session,
            name="DIR ONLY ARCH",
            academic_year=2025,
            is_archived=True,
        )

        result = await GroupServiceDirector.get_groups(
            session,
            skip=0,
            limit=100,
            filters=SearchGroupBase(),
            sort_by=GroupSortField.ACADEMIC_YEAR,
            order=OrderBy.DESC,
        )

        assert result.total == 1
