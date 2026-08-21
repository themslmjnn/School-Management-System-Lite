from sqlalchemy.ext.asyncio import AsyncSession

from src.subjects.schemas import SearchSubjectBase
from src.subjects.services.director import SubjectServiceDirector
from src.utils.enums import OrderBy, SubjectSortField
from tests.factories import make_subject


class TestDirectorGetSubjects:
    async def test_returns_only_non_archived(self, session: AsyncSession):
        active = await make_subject(
            session, name="Active Dir Subject", code="ACTDIR201"
        )
        await make_subject(
            session,
            name="Archived Dir Subject",
            code="ARCHDIR201",
            is_archived=True,
        )

        result = await SubjectServiceDirector.get_subjects(
            session,
            skip=0,
            limit=100,
            filters=SearchSubjectBase(),
            sort_by=SubjectSortField.NAME,
            order=OrderBy.ASC,
        )

        returned_ids = {s.id for s in result.items}

        assert active.id in returned_ids
        assert result.total == 1

    async def test_filter_by_name_substring(self, session: AsyncSession):
        target = await make_subject(
            session, name="Findable Dir Subject", code="FINDDIR201"
        )
        await make_subject(session, name="Other Dir Subject", code="OTHDIR201")

        result = await SubjectServiceDirector.get_subjects(
            session,
            skip=0,
            limit=100,
            filters=SearchSubjectBase(name="Findable"),
            sort_by=SubjectSortField.NAME,
            order=OrderBy.ASC,
        )

        returned_ids = {s.id for s in result.items}

        assert returned_ids == {target.id}

    async def test_filter_by_code_substring(self, session: AsyncSession):
        target = await make_subject(
            session, name="Code Dir Subject", code="UNIQUEDIR201"
        )
        await make_subject(session, name="Other Code Dir Subject", code="OTHCDIR201")

        result = await SubjectServiceDirector.get_subjects(
            session,
            skip=0,
            limit=100,
            filters=SearchSubjectBase(code="UNIQUEDIR"),
            sort_by=SubjectSortField.NAME,
            order=OrderBy.ASC,
        )

        returned_ids = {s.id for s in result.items}

        assert returned_ids == {target.id}

    async def test_sort_by_name_ascending(self, session: AsyncSession):
        z_subject = await make_subject(
            session, name="Zebra Dir Subject", code="ZEBDIR201"
        )
        a_subject = await make_subject(
            session, name="Apple Dir Subject", code="APPDIR201"
        )

        result = await SubjectServiceDirector.get_subjects(
            session,
            skip=0,
            limit=100,
            filters=SearchSubjectBase(),
            sort_by=SubjectSortField.NAME,
            order=OrderBy.ASC,
        )

        ids_in_order = [s.id for s in result.items]

        assert ids_in_order.index(a_subject.id) < ids_in_order.index(z_subject.id)

    async def test_has_more_true_when_results_exceed_limit(self, session: AsyncSession):
        for i in range(3):
            await make_subject(
                session,
                name=f"Dir Paginated Subject {i}",
                code=f"DIRPAG20{i}",
            )

        result = await SubjectServiceDirector.get_subjects(
            session,
            skip=0,
            limit=2,
            filters=SearchSubjectBase(),
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
                name=f"Dir Final Subject {i}",
                code=f"DIRFIN20{i}",
            )

        result = await SubjectServiceDirector.get_subjects(
            session,
            skip=2,
            limit=2,
            filters=SearchSubjectBase(),
            sort_by=SubjectSortField.NAME,
            order=OrderBy.ASC,
        )

        assert len(result.items) == 1
        assert result.has_more is False

    async def test_cannot_include_archived(self, session: AsyncSession):
        await make_subject(session, name="Dir Active Only", code="DIRACTONLY201")
        await make_subject(
            session,
            name="Dir Archived Only",
            code="DIRARCHONLY201",
            is_archived=True,
        )

        result = await SubjectServiceDirector.get_subjects(
            session,
            skip=0,
            limit=100,
            filters=SearchSubjectBase(),
            sort_by=SubjectSortField.NAME,
            order=OrderBy.ASC,
        )

        assert result.total == 1
