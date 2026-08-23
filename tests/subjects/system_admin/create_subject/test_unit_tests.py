import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.subjects.schemas import CreateSubjectAdmin
from src.subjects.services.system_admin import SubjectServiceAdmin
from src.users.models.user import User
from src.utils.exceptions import SubjectCodeAlreadyExistsError
from tests.factories import make_subject


class TestCreateSubject:
    async def test_creates_subject_successfully(
        self, session: AsyncSession, system_admin: User
    ):
        request = CreateSubjectAdmin(name="Mathematics", code="MATH101")

        subject = await SubjectServiceAdmin.create_subject(
            session, system_admin.id, request
        )

        assert subject.id is not None
        assert subject.name == "Mathematics"
        assert subject.code == "MATH101"
        assert subject.is_archived is False

    async def test_code_normalized_to_uppercase(
        self, session: AsyncSession, system_admin: User
    ):
        request = CreateSubjectAdmin(name="Physics Course", code="phy101")

        subject = await SubjectServiceAdmin.create_subject(
            session, system_admin.id, request
        )

        assert subject.code == "PHY101"

    async def test_description_stored_when_provided(
        self, session: AsyncSession, system_admin: User
    ):
        request = CreateSubjectAdmin(
            name="Chemistry Course",
            code="CHEM101",
            description="Introduction to chemistry",
        )

        subject = await SubjectServiceAdmin.create_subject(
            session, system_admin.id, request
        )

        assert subject.description == "Introduction to chemistry"

    async def test_description_none_when_not_provided(
        self, session: AsyncSession, system_admin: User
    ):
        request = CreateSubjectAdmin(name="Biology Course", code="BIO101")

        subject = await SubjectServiceAdmin.create_subject(
            session, system_admin.id, request
        )

        assert subject.description is None

    async def test_duplicate_code_raises_error(
        self, session: AsyncSession, system_admin: User
    ):
        await make_subject(session, name="Existing Subject", code="DUP101")

        request = CreateSubjectAdmin(name="Another Subject", code="DUP101")

        with pytest.raises(SubjectCodeAlreadyExistsError):
            await SubjectServiceAdmin.create_subject(session, system_admin.id, request)
