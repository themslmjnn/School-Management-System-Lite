from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models.user import User
from src.utils.enums import UserStatus
from tests.conftest import make_auth_header
from tests.factories import (
    make_student,
    make_system_admin,
    make_teacher,
)


class TestUpdateUserCredentials:
    async def test_update_user_credentials_returns_204(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        teacher: User,
    ):
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch(
            f"/users/{teacher.id}/credentials",
            json={"username": "newusername4"},
            headers=headers,
        )

        assert response.status_code == 204

    async def test_returns_404_when_not_found(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch(
            "/users/999999/credentials",
            json={"username": "doesntmatter"},
            headers=headers,
        )

        assert response.status_code == 404

    async def test_returns_404_for_system_admin_target(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        other_admin = await make_system_admin(test_db)
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch(
            f"/users/{other_admin.id}/credentials",
            json={"username": "doesntmatter"},
            headers=headers,
        )

        assert response.status_code == 404

    async def test_returns_409_when_no_changes(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        teacher: User,
    ):
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch(
            f"/users/{teacher.id}/credentials",
            json={},
            headers=headers,
        )

        assert response.status_code == 409

    async def test_returns_409_for_duplicate_username(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        teacher: User,
    ):
        await make_teacher(test_db, username="taken_username")
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch(
            f"/users/{teacher.id}/credentials",
            json={"username": "taken_username"},
            headers=headers,
        )

        assert response.status_code == 409

    async def test_returns_409_for_duplicate_email_non_student(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        teacher: User,
    ):
        await make_teacher(test_db, email="taken@example.com")
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch(
            f"/users/{teacher.id}/credentials",
            json={"email": "taken@example.com"},
            headers=headers,
        )

        assert response.status_code == 409

    async def test_returns_409_student_email_contact_limit(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        student: User,
    ):
        shared_email = "shared.route@example.com"

        for i in range(3):
            await make_student(
                test_db,
                email=shared_email,
                phone_number=f"+99255522{i:04d}",
                username=f"route_student_{i}",
            )

        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch(
            f"/users/{student.id}/credentials",
            json={"email": shared_email},
            headers=headers,
        )

        assert response.status_code == 409

    async def test_returns_403_for_non_admin(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        teacher: User,
        student: User,
    ):
        headers = await make_auth_header(test_db, teacher)

        response = await client.patch(
            f"/users/{student.id}/credentials",
            json={"username": "doesntmatter"},
            headers=headers,
        )

        assert response.status_code == 403

    async def test_returns_401_when_unauthenticated(
        self,
        client: AsyncClient,
        teacher: User,
    ):
        response = await client.patch(
            f"/users/{teacher.id}/credentials",
            json={"username": "doesntmatter"},
        )

        assert response.status_code == 401

    async def test_returns_422_for_invalid_username_symbol(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        teacher: User,
    ):
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch(
            f"/users/{teacher.id}/credentials",
            json={"username": "bad-name!"},
            headers=headers,
        )

        errors = response.json()["detail"]
        error_fields = [error["loc"][-1] for error in errors]

        assert response.status_code == 422
        assert "username" in error_fields

    async def test_returns_422_for_invalid_path_id(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch(
            "/users/0/credentials",
            json={"username": "doesntmatter"},
            headers=headers,
        )

        assert response.status_code == 422

    async def test_returns_204_on_pending_user_email_change(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ) -> None:
        pending_user = await make_teacher(
            test_db, status=UserStatus.PENDING_ACTIVATION, is_active=False
        )
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch(
            f"/users/{pending_user.id}/credentials",
            json={"email": "route.reissue@example.com"},
            headers=headers,
        )

        assert response.status_code == 204

    async def test_returns_204_on_combined_update_for_pending_user(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ) -> None:
        pending_user = await make_teacher(
            test_db, status=UserStatus.PENDING_ACTIVATION, is_active=False
        )
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch(
            f"/users/{pending_user.id}/credentials",
            json={
                "username": "combined_username",
                "email": "combined.route@example.com",
            },
            headers=headers,
        )

        assert response.status_code == 204
