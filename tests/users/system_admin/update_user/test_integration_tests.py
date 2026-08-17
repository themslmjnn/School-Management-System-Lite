from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models.user import User
from src.users.repositories.user import UserRepositoryBase
from tests.conftest import make_auth_header
from tests.factories import (
    make_student,
    make_system_admin,
    make_teacher,
)


class TestUpdateUser:
    async def test_update_user_returns_204(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        teacher: User,
        mock_send_account_info_updated_email,
    ):
        headers = await make_auth_header(session, system_admin)
        target_teacher_id = teacher.id

        response = await client.patch(
            f"/users/{target_teacher_id}",
            json={
                "type": "teacher",
                "firstname": "UpdatedFirstName",
            },
            headers=headers,
        )

        updated_user = await UserRepositoryBase.get_user_by_id(
            session, target_teacher_id
        )

        assert response.status_code == 204
        assert updated_user.firstname == "Updatedfirstname"
        assert updated_user.id == teacher.id

    async def test_update_user_returns_404_when_not_found(
        self, session: AsyncSession, client: AsyncClient, system_admin: User
    ):
        headers = await make_auth_header(session, system_admin)

        response = await client.patch(
            "/users/999999",
            json={
                "type": "teacher",
                "firstname": "Whoever",
            },
            headers=headers,
        )

        assert response.status_code == 404

    async def test_update_user_returns_404_for_system_admin_target(
        self, session: AsyncSession, client: AsyncClient, system_admin: User
    ):
        other_admin = await make_system_admin(session)
        headers = await make_auth_header(session, system_admin)

        response = await client.patch(
            f"/users/{other_admin.id}",
            json={
                "type": "teacher",
                "firstname": "Whoever",
            },
            headers=headers,
        )

        assert response.status_code == 404

    async def test_update_user_returns_400_when_no_changes(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        teacher: User,
    ):
        headers = await make_auth_header(session, system_admin)

        response = await client.patch(
            f"/users/{teacher.id}",
            json={"type": "teacher"},
            headers=headers,
        )

        assert response.status_code == 400

    async def test_update_user_returns_409_for_duplicate_phone(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        teacher: User,
    ):
        existing = await make_teacher(session, phone_number="+992555111444")
        headers = await make_auth_header(session, system_admin)

        response = await client.patch(
            f"/users/{teacher.id}",
            json={
                "type": "teacher",
                "phone_number": existing.phone_number,
            },
            headers=headers,
        )

        assert response.status_code == 409

    async def test_update_student_returns_409_when_contact_limit_reached(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        student: User,
    ):
        shared_phone = "+992555444333"

        for i in range(3):
            await make_student(
                session,
                phone_number=shared_phone,
                email=f"other_{i}@example.com",
                username=f"other_student_{i}",
            )

        headers = await make_auth_header(session, system_admin)

        response = await client.patch(
            f"/users/{student.id}",
            json={
                "type": "student",
                "phone_number": shared_phone,
            },
            headers=headers,
        )

        assert response.status_code == 409

    async def test_update_user_returns_403_for_non_admin(
        self, session: AsyncSession, client: AsyncClient, teacher: User, student: User
    ):
        headers = await make_auth_header(session, teacher)

        response = await client.patch(
            f"/users/{student.id}",
            json={
                "type": "teacher",
                "firstname": "Whoever",
            },
            headers=headers,
        )

        assert response.status_code == 403

    async def test_update_user_returns_401_when_unauthenticated(
        self, client: AsyncClient, teacher: User
    ):
        response = await client.patch(
            f"/users/{teacher.id}",
            json={
                "type": "teacher",
                "firstname": "Whoever",
            },
        )

        assert response.status_code == 401

    async def test_update_user_returns_422_for_invalid_firstname(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        teacher: User,
    ):
        headers = await make_auth_header(session, system_admin)

        response = await client.patch(
            f"/users/{teacher.id}",
            json={
                "type": "teacher",
                "firstname": "Name123",
            },
            headers=headers,
        )

        assert response.status_code == 422

    async def test_student_payload_for_teacher_target_returns_400(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        teacher: User,
    ) -> None:
        headers = await make_auth_header(session, system_admin)

        response = await client.patch(
            f"/users/{teacher.id}",
            json={
                "type": "student",
                "firstname": "NewName",
            },
            headers=headers,
        )

        assert response.status_code == 400

    async def test_staff_payload_for_student_target_returns_400(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        student: User,
    ) -> None:
        headers = await make_auth_header(session, system_admin)

        response = await client.patch(
            f"/users/{student.id}",
            json={
                "type": "teacher",
                "firstname": "NewName",
            },
            headers=headers,
        )

        assert response.status_code == 400
