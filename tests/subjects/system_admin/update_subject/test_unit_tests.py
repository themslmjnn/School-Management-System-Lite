import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.subjects.exceptions.exceptions import (
    SubjectCodeAlreadyExistsError,
    SubjectNotFoundError,
)
from src.subjects.repository import SubjectRepository
from src.subjects.schemas import UpdateSubjectAdmin
from src.subjects.services.system_admin import SubjectServiceAdmin
from utils.exceptions import NoChangesDetectedError
from tests.factories import make_subject


class TestUpdateSubject:
    async def test_updates_name_successfully(self, session: AsyncSession, system_admin):
        subject = await make_subject(session, name="Old Name", code="UPD101")

        await SubjectServiceAdmin.update_subject(
            session,
            system_admin.id,
            subject.id,
            UpdateSubjectAdmin(name="New Long Name"),
        )

        updated = await SubjectRepository.get_subject_by_id(session, subject.id)

        assert updated.name == "New Long Name"

    async def test_updates_code_successfully(self, session: AsyncSession, system_admin):
        subject = await make_subject(session, name="Some Subject", code="OLD101")

        await SubjectServiceAdmin.update_subject(
            session, system_admin.id, subject.id, UpdateSubjectAdmin(code="NEW101")
        )

        updated = await SubjectRepository.get_subject_by_id(session, subject.id)

        assert updated.code == "NEW101"

    async def test_updates_description_successfully(
        self, session: AsyncSession, system_admin
    ):
        subject = await make_subject(session, name="Described Subject", code="DESC101")

        await SubjectServiceAdmin.update_subject(
            session,
            system_admin.id,
            subject.id,
            UpdateSubjectAdmin(description="A new description"),
        )

        updated = await SubjectRepository.get_subject_by_id(session, subject.id)

        assert updated.description == "A new description"

    async def test_not_found_raises(self, session: AsyncSession, system_admin):
        with pytest.raises(SubjectNotFoundError):
            await SubjectServiceAdmin.update_subject(
                session,
                system_admin.id,
                999_999,
                UpdateSubjectAdmin(name="Doesnt Matter"),
            )

    async def test_no_changes_raises(self, session: AsyncSession, system_admin):
        subject = await make_subject(session, name="Unchanged Subject", code="NOCH101")

        with pytest.raises(NoChangesDetectedError):
            await SubjectServiceAdmin.update_subject(
                session,
                system_admin.id,
                subject.id,
                UpdateSubjectAdmin(),
            )

    async def test_duplicate_code_raises(self, session: AsyncSession, system_admin):
        await make_subject(session, name="Taken Subject", code="TAKEN101")
        subject = await make_subject(session, name="Target Subject", code="TARGET101")

        with pytest.raises(SubjectCodeAlreadyExistsError):
            await SubjectServiceAdmin.update_subject(
                session,
                system_admin.id,
                subject.id,
                UpdateSubjectAdmin(code="TAKEN101"),
            )

    async def test_cache_invalidated_after_update(
        self, session: AsyncSession, system_admin, mocker
    ):
        subject = await make_subject(session, name="Cache Subject", code="CACHE101")
        calls = []

        async def capture(*args):
            calls.extend(args)

        mocker.patch(
            "src.subjects.services.system_admin.delete_cache", side_effect=capture
        )

        await SubjectServiceAdmin.update_subject(
            session,
            system_admin.id,
            subject.id,
            UpdateSubjectAdmin(name="Cache Subject Updated"),
        )

        from src.utils.cache_keys import SubjectCacheKey

        assert SubjectCacheKey.subject_detail_key_admin(subject.id) in calls
