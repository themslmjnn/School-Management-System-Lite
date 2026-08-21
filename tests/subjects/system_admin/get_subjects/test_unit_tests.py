from sqlalchemy.ext.asyncio import AsyncSession

from src.subjects.schemas import SearchSubjectAdmin
from src.subjects.services.system_admin import SubjectServiceAdmin
from src.utils.enums import OrderBy, SubjectSortField
from tests.factories import make_subject


class TestGetSubjects:
    async def test_returns_all_non_archived_by_default(self, session: AsyncSession):
        active = await make_subject(session, name="Active Subject", code="ACT201")
        await make_subject(
            session,
            name="Archived Subject",
            code="ARCH201",
            is_archived=True,
        )

        result = await SubjectServiceAdmin.get_subjects(
            session,
            skip=0,
            limit=100,
            filters=SearchSubjectAdmin(),
            sort_by=SubjectSortField.NAME,
            order=OrderBy.ASC,
        )

        returned_ids = {s.id for s in result.items}

        assert active.id in returned_ids
        assert result.total == 1

    async def test_include_archived_returns_all(self, session: AsyncSession):
        await make_subject(session, name="Active Two", code="ACT202")
        await make_subject(
            session,
            name="Archived Two",
            code="ARCH202",
            is_archived=True,
        )

        result = await SubjectServiceAdmin.get_subjects(
            session,
            skip=0,
            limit=100,
            filters=SearchSubjectAdmin(include_archived=True),
            sort_by=SubjectSortField.NAME,
            order=OrderBy.ASC,
        )

        assert result.total == 2

    async def test_filter_by_name_substring(self, session: AsyncSession):
        target = await make_subject(session, name="Findable Subject", code="FIND201")
        await make_subject(session, name="Other Subject", code="OTH201")

        result = await SubjectServiceAdmin.get_subjects(
            session,
            skip=0,
            limit=100,
            filters=SearchSubjectAdmin(name="Findable"),
            sort_by=SubjectSortField.NAME,
            order=OrderBy.ASC,
        )

        returned_ids = {s.id for s in result.items}

        assert returned_ids == {target.id}

    async def test_filter_by_code_substring(self, session: AsyncSession):
        target = await make_subject(session, name="Code Subject", code="UNIQUE201")
        await make_subject(session, name="Other Subject", code="OTHER201")

        result = await SubjectServiceAdmin.get_subjects(
            session,
            skip=0,
            limit=100,
            filters=SearchSubjectAdmin(code="UNIQUE"),
            sort_by=SubjectSortField.NAME,
            order=OrderBy.ASC,
        )

        returned_ids = {s.id for s in result.items}

        assert returned_ids == {target.id}

    async def test_sort_by_name_ascending(self, session: AsyncSession):
        z_subject = await make_subject(session, name="Zebra Subject", code="ZEB201")
        a_subject = await make_subject(session, name="Apple Subject", code="APP201")

        result = await SubjectServiceAdmin.get_subjects(
            session,
            skip=0,
            limit=100,
            filters=SearchSubjectAdmin(),
            sort_by=SubjectSortField.NAME,
            order=OrderBy.ASC,
        )

        ids_in_order = [s.id for s in result.items]

        assert ids_in_order.index(a_subject.id) < ids_in_order.index(z_subject.id)

    async def test_sort_by_name_descending(self, session: AsyncSession):
        z_subject = await make_subject(session, name="Zebra Subject Two", code="ZEB202")
        a_subject = await make_subject(session, name="Apple Subject Two", code="APP202")

        result = await SubjectServiceAdmin.get_subjects(
            session,
            skip=0,
            limit=100,
            filters=SearchSubjectAdmin(),
            sort_by=SubjectSortField.NAME,
            order=OrderBy.DESC,
        )

        ids_in_order = [s.id for s in result.items]

        assert ids_in_order.index(z_subject.id) < ids_in_order.index(a_subject.id)

    async def test_has_more_true_when_results_exceed_limit(self, session: AsyncSession):
        for i in range(3):
            await make_subject(
                session,
                name=f"Paginated Subject {i}",
                code=f"PAG20{i}",
            )

        result = await SubjectServiceAdmin.get_subjects(
            session,
            skip=0,
            limit=2,
            filters=SearchSubjectAdmin(),
            sort_by=SubjectSortField.NAME,
            order=OrderBy.ASC,
        )

        assert len(result.items) == 2
        assert result.total == 3
        assert result.has_more is True

    async def test_has_more_false_on_final_page(self, session: AsyncSession):
        for i in range(3):
            await make_subject(
                session,
                name=f"Final Page Subject {i}",
                code=f"FIN20{i}",
            )

        result = await SubjectServiceAdmin.get_subjects(
            session,
            skip=2,
            limit=2,
            filters=SearchSubjectAdmin(),
            sort_by=SubjectSortField.NAME,
            order=OrderBy.ASC,
        )

        assert len(result.items) == 1
        assert result.has_more is False

    async def test_invalid_sort_field_falls_back_to_created_at(
        self, session: AsyncSession
    ):
        await make_subject(session, name="Fallback Subject One", code="FALL201")
        await make_subject(session, name="Fallback Subject Two", code="FALL202")

        result = await SubjectServiceAdmin.get_subjects(
            session,
            skip=0,
            limit=100,
            filters=SearchSubjectAdmin(),
            sort_by="not_a_real_field",
            order=OrderBy.ASC,
        )

        assert result.total == 2
