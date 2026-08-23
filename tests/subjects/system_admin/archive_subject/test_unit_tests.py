import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.subjects.repository import SubjectRepository
from src.subjects.services.system_admin import SubjectServiceAdmin
from src.users.models.user import User
from src.utils.cache_keys import SubjectCacheKey
from src.utils.exceptions import (
    SubjectAlreadyArchivedError,
    SubjectNotFoundError,
)
from tests.factories import make_subject


class TestArchiveSubject:
    async def test_archives_subject_successfully(
        self, session: AsyncSession, system_admin: User
    ):
        subject = await make_subject(session, name="Active Subject", code="ACT101")

        await SubjectServiceAdmin.archive_subject(session, system_admin.id, subject.id)

        updated = await SubjectRepository.get_subject_by_id(session, subject.id)

        assert updated.is_archived is True
        assert updated.archived_at is not None

    async def test_not_found_raises(self, session: AsyncSession, system_admin: User):
        with pytest.raises(SubjectNotFoundError):
            await SubjectServiceAdmin.archive_subject(session, system_admin.id, 999_999)

    async def test_already_archived_raises(
        self, session: AsyncSession, system_admin: User
    ):
        subject = await make_subject(
            session,
            name="Already Archived",
            code="ARCH101",
            is_archived=True,
        )

        with pytest.raises(SubjectAlreadyArchivedError):
            await SubjectServiceAdmin.archive_subject(
                session, system_admin.id, subject.id
            )

    async def test_cache_invalidated_after_archive(
        self, session: AsyncSession, system_admin: User, mocker
    ):
        subject = await make_subject(
            session, name="Cache Archive Subject", code="CARCH101"
        )
        calls = []

        async def capture(*args):
            calls.extend(args)

        mocker.patch(
            "src.subjects.services.system_admin.delete_cache", side_effect=capture
        )

        await SubjectServiceAdmin.archive_subject(session, system_admin.id, subject.id)

        assert SubjectCacheKey.subject_detail_key_admin(subject.id) in calls
