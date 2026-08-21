import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.subjects.exceptions.exceptions import SubjectNotFoundError
from src.subjects.repository import SubjectRepository
from src.subjects.services.system_admin import SubjectServiceAdmin
from src.utils.cache_keys import SubjectCacheKey
from tests.factories import make_subject


class TestGetSubjectById:
    async def test_returns_correct_data(self, session: AsyncSession):
        subject = await make_subject(session, name="Detail Subject", code="DET201")

        result = await SubjectServiceAdmin.get_subject_by_id(session, subject.id)

        assert result.id == subject.id
        assert result.name == subject.name
        assert result.code == subject.code

    async def test_not_found_raises(self, session: AsyncSession):
        with pytest.raises(SubjectNotFoundError):
            await SubjectServiceAdmin.get_subject_by_id(session, 999_999)

    async def test_archived_subject_is_returned(self, session: AsyncSession):
        subject = await make_subject(
            session,
            name="Archived Detail",
            code="ARCHDET201",
            is_archived=True,
        )

        result = await SubjectServiceAdmin.get_subject_by_id(session, subject.id)

        assert result.id == subject.id
        assert result.is_archived is True

    async def test_populates_cache_after_db_hit(
        self, session: AsyncSession, mock_set_cache_subject_system_admin, mocker
    ):
        subject = await make_subject(
            session, name="Cache Detail Subject", code="CDET201"
        )

        await SubjectServiceAdmin.get_subject_by_id(session, subject.id)

        mock_set_cache_subject_system_admin.assert_called_once_with(
            SubjectCacheKey.subject_detail_key_admin(subject.id),
            mocker.ANY,
            900,
        )

    async def test_does_not_hit_db_on_cache_hit(self, session: AsyncSession, mocker):
        subject = await make_subject(session, name="Cache Hit Subject", code="CHIT201")

        await SubjectServiceAdmin.get_subject_by_id(session, subject.id)

        mock_repo = mocker.patch.object(SubjectRepository, "get_subject_by_id")

        await SubjectServiceAdmin.get_subject_by_id(session, subject.id)

        mock_repo.assert_not_called()

    async def test_returns_same_data_on_cache_hit(self, session: AsyncSession):
        subject = await make_subject(
            session, name="Cache Same Subject", code="CSAME201"
        )

        first = await SubjectServiceAdmin.get_subject_by_id(session, subject.id)
        second = await SubjectServiceAdmin.get_subject_by_id(session, subject.id)

        assert second.id == first.id
        assert second.code == first.code
