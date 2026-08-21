from sqlalchemy.ext.asyncio import AsyncSession

from src.groups.schemas import SearchGroupAdmin
from src.groups.services.system_admin import GroupServiceAdmin
from src.utils.enums import GroupSortField, OrderBy
from tests.factories import make_group


class TestGetGroups:
    async def test_returns_only_non_archived_by_default(self, session: AsyncSession):
        active = await make_group(session, name="ACTIVE GG", academic_year=2025)
        await make_group(
            session,
            name="ARCHIVED GG",
            academic_year=2025,
            is_archived=True,
        )

        result = await GroupServiceAdmin.get_groups(
            session,
            skip=0,
            limit=100,
            filters=SearchGroupAdmin(),
            sort_by=GroupSortField.ACADEMIC_YEAR,
            order=OrderBy.DESC,
        )

        returned_ids = {g.id for g in result.items}

        assert active.id in returned_ids
        assert result.total == 1

    async def test_include_archived_returns_all(self, session: AsyncSession):
        await make_group(session, name="ACTIVE GG2", academic_year=2025)
        await make_group(
            session,
            name="ARCHIVED GG2",
            academic_year=2025,
            is_archived=True,
        )

        result = await GroupServiceAdmin.get_groups(
            session,
            skip=0,
            limit=100,
            filters=SearchGroupAdmin(include_archived=True),
            sort_by=GroupSortField.ACADEMIC_YEAR,
            order=OrderBy.DESC,
        )

        assert result.total == 2

    async def test_filter_by_name_substring(self, session: AsyncSession):
        target = await make_group(session, name="FIND GG", academic_year=2025)
        await make_group(session, name="OTHER GG", academic_year=2025)

        result = await GroupServiceAdmin.get_groups(
            session,
            skip=0,
            limit=100,
            filters=SearchGroupAdmin(name="FIND"),
            sort_by=GroupSortField.ACADEMIC_YEAR,
            order=OrderBy.DESC,
        )

        returned_ids = {g.id for g in result.items}

        assert returned_ids == {target.id}

    async def test_filter_by_academic_year(self, session: AsyncSession):
        target = await make_group(session, name="YEAR GG", academic_year=2024)
        await make_group(session, name="OTHER YR GG", academic_year=2025)

        result = await GroupServiceAdmin.get_groups(
            session,
            skip=0,
            limit=100,
            filters=SearchGroupAdmin(academic_year=2024),
            sort_by=GroupSortField.ACADEMIC_YEAR,
            order=OrderBy.DESC,
        )

        returned_ids = {g.id for g in result.items}

        assert returned_ids == {target.id}

    async def test_sort_by_academic_year_descending(self, session: AsyncSession):
        older = await make_group(session, name="OLDER GG", academic_year=2023)
        newer = await make_group(session, name="NEWER GG", academic_year=2026)

        result = await GroupServiceAdmin.get_groups(
            session,
            skip=0,
            limit=100,
            filters=SearchGroupAdmin(),
            sort_by=GroupSortField.ACADEMIC_YEAR,
            order=OrderBy.DESC,
        )

        ids_in_order = [g.id for g in result.items]

        assert ids_in_order.index(newer.id) < ids_in_order.index(older.id)

    async def test_sort_by_academic_year_ascending(self, session: AsyncSession):
        older = await make_group(session, name="OLDER GG2", academic_year=2023)
        newer = await make_group(session, name="NEWER GG2", academic_year=2026)

        result = await GroupServiceAdmin.get_groups(
            session,
            skip=0,
            limit=100,
            filters=SearchGroupAdmin(),
            sort_by=GroupSortField.ACADEMIC_YEAR,
            order=OrderBy.ASC,
        )

        ids_in_order = [g.id for g in result.items]

        assert ids_in_order.index(older.id) < ids_in_order.index(newer.id)

    async def test_has_more_true_when_results_exceed_limit(self, session: AsyncSession):
        for i in range(3):
            await make_group(session, name=f"PAGE GG{i}", academic_year=2020 + i)

        result = await GroupServiceAdmin.get_groups(
            session,
            skip=0,
            limit=2,
            filters=SearchGroupAdmin(),
            sort_by=GroupSortField.ACADEMIC_YEAR,
            order=OrderBy.DESC,
        )

        assert len(result.items) == 2
        assert result.total == 3
        assert result.has_more is True

    async def test_has_more_false_on_final_page(self, session: AsyncSession):
        for i in range(3):
            await make_group(session, name=f"FINAL GG{i}", academic_year=2030 + i)

        result = await GroupServiceAdmin.get_groups(
            session,
            skip=2,
            limit=2,
            filters=SearchGroupAdmin(),
            sort_by=GroupSortField.ACADEMIC_YEAR,
            order=OrderBy.DESC,
        )

        assert len(result.items) == 1
        assert result.has_more is False

    async def test_invalid_sort_field_falls_back_to_created_at(
        self, session: AsyncSession
    ):
        await make_group(session, name="FALL GG1", academic_year=2025)
        await make_group(session, name="FALL GG2", academic_year=2025)

        result = await GroupServiceAdmin.get_groups(
            session,
            skip=0,
            limit=100,
            filters=SearchGroupAdmin(),
            sort_by="not_a_real_field",
            order=OrderBy.DESC,
        )

        assert result.total == 2
