from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models.user import User
from tests.conftest import make_auth_header
from tests.factories import (
    make_student,
    make_system_admin,
    make_teacher,
)


class TestUpdateUser:
    async def test_update_user_returns_200_and_expected_shape(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        teacher: User,
        mock_send_account_info_updated_email,
    ):
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch(
            f"/users/{teacher.id}",
            json={"type": "staff_or_guardian", "firstname": "UpdatedFirstName"},
            headers=headers,
        )

        body = response.json()

        assert response.status_code == 200
        assert body["firstname"] == "Updatedfirstname"
        assert body["id"] == teacher.id

    async def test_update_user_returns_404_when_not_found(
        self, test_db: AsyncClient, client: AsyncClient, system_admin: User
    ):
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch(
            "/users/999999",
            json={"type": "staff_or_guardian", "firstname": "Whoever"},
            headers=headers,
        )

        assert response.status_code == 404

    async def test_update_user_returns_404_for_system_admin_target(
        self, test_db: AsyncClient, client: AsyncClient, system_admin: User
    ):
        other_admin = await make_system_admin(test_db)
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch(
            f"/users/{other_admin.id}",
            json={"type": "staff_or_guardian", "firstname": "Whoever"},
            headers=headers,
        )

        assert response.status_code == 404

    async def test_update_user_returns_409_when_no_changes(
        self,
        test_db: AsyncClient,
        client: AsyncClient,
        system_admin: User,
        teacher: User,
    ):
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch(
            f"/users/{teacher.id}",
            json={"type": "staff_or_guardian"},
            headers=headers,
        )

        assert response.status_code == 409

    async def test_update_user_returns_409_for_duplicate_phone(
        self,
        test_db: AsyncClient,
        client: AsyncClient,
        system_admin: User,
        teacher: User,
    ):
        existing = await make_teacher(test_db, phone_number="+992555111444")
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch(
            f"/users/{teacher.id}",
            json={"type": "staff_or_guardian", "phone_number": existing.phone_number},
            headers=headers,
        )

        assert response.status_code == 409

    async def test_update_student_returns_409_when_contact_limit_reached(
        self,
        test_db: AsyncClient,
        client: AsyncClient,
        system_admin: User,
        student: User,
    ):
        shared_phone = "+992555444333"

        for i in range(3):
            await make_student(
                test_db,
                phone_number=shared_phone,
                email=f"other_{i}@example.com",
                username=f"other_student_{i}",
            )

        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch(
            f"/users/{student.id}",
            json={"type": "student", "phone_number": shared_phone},
            headers=headers,
        )

        assert response.status_code == 409

    async def test_update_user_returns_403_for_non_admin(
        self, test_db: AsyncClient, client: AsyncClient, teacher: User, student: User
    ):
        headers = await make_auth_header(test_db, teacher)

        response = await client.patch(
            f"/users/{student.id}",
            json={"type": "staff_or_guardian", "firstname": "Whoever"},
            headers=headers,
        )

        assert response.status_code == 403

    async def test_update_user_returns_401_when_unauthenticated(
        self, client: AsyncClient, teacher: User
    ):
        response = await client.patch(
            f"/users/{teacher.id}",
            json={"type": "staff_or_guardian", "firstname": "Whoever"},
        )

        assert response.status_code == 401

    async def test_update_user_returns_422_for_invalid_firstname(
        self,
        test_db: AsyncClient,
        client: AsyncClient,
        system_admin: User,
        teacher: User,
    ):
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch(
            f"/users/{teacher.id}",
            json={"type": "staff_or_guardian", "firstname": "Name123"},
            headers=headers,
        )

        assert response.status_code == 422

    async def test_student_payload_for_staff_target_returns_400(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        teacher: User,
    ) -> None:
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch(
            f"/users/{teacher.id}",
            json={"type": "student", "firstname": "NewName"},
            headers=headers,
        )

        assert response.status_code == 400

    async def test_staff_payload_for_student_target_returns_400(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        student: User,
    ) -> None:
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch(
            f"/users/{student.id}",
            json={"type": "staff_or_guardian", "firstname": "NewName"},
            headers=headers,
        )

        assert response.status_code == 400
