import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.subjects.exceptions.exceptions import SubjectNotFoundError
from src.subjects.repository import SubjectRepository
from src.subjects.services.director import SubjectServiceDirector
from src.utils.cache_keys import SubjectCacheKey
from tests.factories import make_subject


class TestDirectorGetSubjectById:
    async def test_returns_correct_data(self, session: AsyncSession):
        subject = await make_subject(
            session, name="Dir Detail Subject", code="DIRDET301"
        )

        result = await SubjectServiceDirector.get_subject_by_id(session, subject.id)

        assert result.name == subject.name
        assert result.code == subject.code

    async def test_not_found_raises(self, session: AsyncSession):
        with pytest.raises(SubjectNotFoundError):
            await SubjectServiceDirector.get_subject_by_id(session, 999_999)

    async def test_archived_subject_is_returned(self, session: AsyncSession):
        subject = await make_subject(
            session,
            name="Dir Archived Detail",
            code="DIRARCHDET301",
            is_archived=True,
        )

        result = await SubjectServiceDirector.get_subject_by_id(session, subject.id)

        assert result.name == subject.name

    async def test_response_excludes_archived_at(self, session: AsyncSession):
        subject = await make_subject(
            session, name="Dir Schema Detail", code="DIRSCHDET301"
        )

        result = await SubjectServiceDirector.get_subject_by_id(session, subject.id)

        assert not hasattr(result, "archived_at")

    async def test_populates_cache_after_db_hit(
        self, session: AsyncSession, mock_set_cache_subject_director, mocker
    ):
        subject = await make_subject(
            session, name="Dir Cache Subject", code="DIRCDET301"
        )

        await SubjectServiceDirector.get_subject_by_id(session, subject.id)
        mock_set_cache_subject_director.assert_called_once_with(
            SubjectCacheKey.subject_detail_key_staff(subject.id),
            mocker.ANY,
            900,
        )

    async def test_does_not_hit_db_on_cache_hit(self, session: AsyncSession, mocker):
        subject = await make_subject(
            session, name="Dir Cache Hit Subject", code="DIRCHIT301"
        )

        await SubjectServiceDirector.get_subject_by_id(session, subject.id)

        mock_repo = mocker.patch.object(SubjectRepository, "get_subject_by_id")

        await SubjectServiceDirector.get_subject_by_id(session, subject.id)

        mock_repo.assert_not_called()
