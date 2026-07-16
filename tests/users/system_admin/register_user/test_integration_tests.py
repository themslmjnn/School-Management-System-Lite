from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.emails.repository import PendingEmailRepository
from src.users.models.user import User
from src.users.repositories.user import UserRepositoryBase
from src.users.schemas.user import (
    CreateGuardianAdmin,
    CreateStaffAdmin,
    CreateStudentAdmin,
)
from src.utils.enums import UserRole
from tests.conftest import make_auth_header
from tests.factories import make_teacher


class TestRegisterUser:
    async def test_creates_staff_user_with_invite_token(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        valid_create_staff_request: CreateStaffAdmin,
    ):
        headers = await make_auth_header(test_db, system_admin)

        response = await client.post(
            "/users",
            json=valid_create_staff_request.model_dump(mode="json"),
            headers=headers,
        )

        data = response.json()
        user_with_activation = await UserRepositoryBase.get_user_by_id(
            test_db, data["id"], load_activation=True
        )
        activation = user_with_activation.activation
        pending_emails = await PendingEmailRepository.get_pending_email_by_triggered_by(
            test_db, system_admin.id
        )

        assert response.status_code == 201
        assert len(pending_emails) == 1
        assert data["id"] is not None
        assert data["role"] == valid_create_staff_request.role.value
        assert data["is_active"] is False
        assert activation.invite_token_hash is not None
        assert activation.invite_token_expires_at is not None
        assert activation.invite_token_expires_at > datetime.now(UTC)
        assert activation.user_id == data["id"]

    async def test_creates_student_with_invite_token(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        valid_create_student_request: CreateStudentAdmin,
    ):
        headers = await make_auth_header(test_db, system_admin)

        response = await client.post(
            "/users",
            json=valid_create_student_request.model_dump(mode="json"),
            headers=headers,
        )

        data = response.json()
        user_with_activation = await UserRepositoryBase.get_user_by_id(
            test_db, data["id"], load_activation=True
        )
        activation = user_with_activation.activation

        assert response.status_code == 201
        assert data["id"] is not None
        assert data["role"] == UserRole.STUDENT.value
        assert data["is_active"] is False
        assert activation.invite_token_hash is not None
        assert activation.invite_token_expires_at is not None
        assert activation.invite_token_expires_at > datetime.now(UTC)
        assert activation.user_id == data["id"]

    async def test_creates_guardian_with_invite_token(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        valid_create_guardian_request: CreateGuardianAdmin,
    ):
        headers = await make_auth_header(test_db, system_admin)

        response = await client.post(
            "/users",
            json=valid_create_guardian_request.model_dump(mode="json"),
            headers=headers,
        )

        data = response.json()
        user_with_activation = await UserRepositoryBase.get_user_by_id(
            test_db, data["id"], load_activation=True
        )
        activation = user_with_activation.activation

        assert response.status_code == 201
        assert data["id"] is not None
        assert data["role"] == UserRole.GUARDIAN.value
        assert data["is_active"] is False
        assert activation.invite_token_hash is not None
        assert activation.invite_token_expires_at is not None
        assert activation.invite_token_expires_at > datetime.now(UTC)
        assert activation.user_id == data["id"]

    @pytest.mark.parametrize(
        ("existing_user_data", "request_override"),
        [
            (
                {"username": "taken_username"},
                {"username": "taken_username"},
            ),
            (
                {"email": "taken@example.com"},
                {"email": "taken@example.com"},
            ),
            (
                {"phone_number": "+992555111222"},
                {"phone_number": "+992555111222"},
            ),
        ],
    )
    async def test_reject_duplicate_fields_staff(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        valid_create_staff_request: CreateStaffAdmin,
        existing_user_data: dict,
        request_override: dict,
    ):
        await make_teacher(test_db, **existing_user_data)

        for field, value in request_override.items():
            setattr(valid_create_staff_request, field, value)

        headers = await make_auth_header(test_db, system_admin)

        response = await client.post(
            "/users",
            json=valid_create_staff_request.model_dump(mode="json"),
            headers=headers,
        )

        assert response.status_code == 409

    async def test_reject_duplicate_username_student(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        valid_create_student_request: CreateStudentAdmin,
    ):
        await make_teacher(test_db, username="taken_username")
        valid_create_student_request.username = "taken_username"

        headers = await make_auth_header(test_db, system_admin)

        response = await client.post(
            "/users",
            json=valid_create_student_request.model_dump(mode="json"),
            headers=headers,
        )

        assert response.status_code == 409

    async def test_reject_guardian_when_contact_limit_reached(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        valid_create_guardian_request: CreateGuardianAdmin,
    ):
        await make_teacher(
            test_db,
            email=valid_create_guardian_request.email,
            phone_number=valid_create_guardian_request.phone_number,
        )

        headers = await make_auth_header(test_db, system_admin)

        response = await client.post(
            "/users",
            json=valid_create_guardian_request.model_dump(mode="json"),
            headers=headers,
        )

        assert response.status_code == 409

    async def test_returns_403_for_non_admin(
        self,
        test_db: AsyncClient,
        client: AsyncClient,
        teacher: User,
        valid_create_staff_request: CreateStaffAdmin,
    ):
        headers = await make_auth_header(test_db, teacher)

        response = await client.post(
            "/users",
            json=valid_create_staff_request.model_dump(mode="json"),
            headers=headers,
        )

        assert response.status_code == 403

    async def test_unauthenticated_request_returns_401(self, client):
        response = await client.post("/users")

        assert response.status_code == 401

    async def test_rejects_invalid_username(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        valid_create_staff_request: CreateStaffAdmin,
    ):
        headers = await make_auth_header(test_db, system_admin)
        payload = valid_create_staff_request.model_dump(mode="json")
        payload["username"] = "bad-name!"

        response = await client.post("/users", json=payload, headers=headers)

        errors = response.json()["detail"]
        error_fields = [error["loc"][-1] for error in errors]

        assert response.status_code == 422
        assert "username" in error_fields

    async def test_rejects_missing_date_of_birth_for_student(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        valid_create_student_request: CreateStudentAdmin,
    ):
        headers = await make_auth_header(test_db, system_admin)
        payload = valid_create_student_request.model_dump(mode="json")
        del payload["date_of_birth"]

        response = await client.post("/users", json=payload, headers=headers)

        errors = response.json()["detail"]
        error_fields = [error["loc"][-1] for error in errors]

        assert response.status_code == 422
        assert "date_of_birth" in error_fields
