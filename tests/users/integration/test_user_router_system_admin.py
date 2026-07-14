from datetime import UTC, datetime
from urllib.parse import parse_qs, urlparse

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import verify_invite_token
from src.emails.models import PendingEmail
from src.emails.repository import PendingEmailRepository
from src.users.models.users import User
from src.users.repositories.users import UserRepositoryBase
from src.users.schemas.users import (
    CreateGuardianAdmin,
    CreateStaffAdmin,
    CreateStudentAdmin,
    UpdateUserCredentials,
)
from src.utils.enums import UserRole, UserStatus
from tests.conftest import make_auth_header
from tests.factories import (
    make_deactivated_user,
    make_guardian,
    make_student,
    make_system_admin,
    make_teacher,
    make_user,
)
from users.services.system_admin import UserServiceAdmin


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

    async def test_rejects_system_admin_role(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        valid_create_staff_request: CreateStaffAdmin,
    ):
        headers = await make_auth_header(test_db, system_admin)
        valid_create_staff_request.role = UserRole.SYSTEM_ADMIN

        response = await client.post(
            "/users",
            json=valid_create_staff_request.model_dump(mode="json"),
            headers=headers,
        )

        assert response.status_code == 403
        assert response.json()["detail"] == "System admin creation via api is forbidden"

    async def test_rejects_director_role(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        valid_create_staff_request: CreateStaffAdmin,
    ):
        headers = await make_auth_header(test_db, system_admin)
        valid_create_staff_request.role = UserRole.DIRECTOR

        response = await client.post(
            "/users",
            json=valid_create_staff_request.model_dump(mode="json"),
            headers=headers,
        )

        assert response.status_code == 403
        assert response.json()["detail"] == "Director creation via api is forbidden"

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

        assert response.status_code == 200
        body = response.json()
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


class TestUpdateUserCredentials:
    async def test_update_user_credentials_returns_204(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        teacher: User,
        mock_send_admin_credentials_override_notification,
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


class TestUpdateUserCredentialsActivationReissueEndpoint:
    """HTTP-layer: only status code / response shape, per two-tier convention —
    internal state already proven at the service layer above."""

    async def test_returns_204_when_reissuing_invite_via_email_change(
        self, test_db, client, system_admin
    ):
        pending_user = await make_teacher(test_db, status=UserStatus.PENDING_ACTIVATION)
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch(
            f"/users/{pending_user.id}/credentials",
            json={"email": "http.reissue@example.com"},
            headers=headers,
        )

        assert response.status_code == 204


def _extract_raw_token_from_text_body(text_body: str) -> str:
    for line in text_body.splitlines():
        if "token=" in line:
            query = parse_qs(urlparse(line.strip()).query)
            return query["token"][0]
    raise AssertionError("No activation link with a token= param found in text_body")


class TestUpdateUserCredentialsCombinedFieldsWithReissue:
    """Covers updating username and email together when the target is
    PENDING_ACTIVATION — proves the username write isn't somehow lost or
    overwritten by the activation-reissue branch that runs afterward."""

    async def test_combined_username_and_email_update_reissues_token_and_persists_both(
        self,
        test_db,
        system_admin,
        mock_send_admin_credentials_override_notification,
    ):
        pending_user = await make_teacher(test_db, status=UserStatus.PENDING_ACTIVATION)
        original_hash = pending_user.activation.invite_token_hash
        update_request = UpdateUserCredentials(
            username="combined_update_username",
            email="combined.update@example.com",
        )

        await UserServiceAdmin.update_user_credentials(
            test_db, system_admin.id, pending_user.id, update_request
        )

        updated = await UserRepositoryBase.get_user_by_id(
            test_db, pending_user.id, load_activation=True
        )
        assert updated.username == "combined_update_username"
        assert updated.email == "combined.update@example.com"
        assert updated.activation.invite_token_hash != original_hash

        pending_email = await _get_pending_email_for(test_db, pending_user.id)
        assert pending_email.recipient == "combined.update@example.com"

        raw_token = _extract_raw_token_from_text_body(pending_email.text_body)
        assert verify_invite_token(raw_token, updated.activation.invite_token_hash)

        mock_send_admin_credentials_override_notification.assert_not_called()

    async def test_combined_update_returns_204_via_endpoint(
        self, test_db, client, system_admin
    ):
        pending_user = await make_teacher(test_db, status=UserStatus.PENDING_ACTIVATION)
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch(
            f"/users/{pending_user.id}/credentials",
            json={
                "username": "combined_http_username",
                "email": "combined.http@example.com",
            },
            headers=headers,
        )

        assert response.status_code == 204


class TestCreateGuardianDeletionRequest:
    async def test_returns_204_on_success(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        guardian: User,
        mock_send_account_deletion_email,
        mock_delete_cache,
    ):
        headers = await make_auth_header(test_db, system_admin)

        response = await client.post(
            f"/users/{guardian.id}/guardian-deletion", headers=headers
        )

        assert response.status_code == 204

    async def test_returns_404_when_not_found(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        headers = await make_auth_header(test_db, system_admin)

        response = await client.post("/users/999999/guardian-deletion", headers=headers)

        assert response.status_code == 404

    async def test_returns_404_for_non_guardian_role(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        teacher: User,
    ):
        headers = await make_auth_header(test_db, system_admin)

        response = await client.post(
            f"/users/{teacher.id}/guardian-deletion", headers=headers
        )

        assert response.status_code == 404

    async def test_returns_409_when_already_pending_deletion(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        mock_send_account_deletion_email,
        mock_delete_cache,
    ):
        guardian_pending = await make_guardian(
            test_db, status=UserStatus.PENDING_DELETION, is_active=False
        )
        headers = await make_auth_header(test_db, system_admin)

        response = await client.post(
            f"/users/{guardian_pending.id}/guardian-deletion", headers=headers
        )

        assert response.status_code == 409

    async def test_returns_403_for_non_admin(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        teacher: User,
        guardian: User,
    ):
        headers = await make_auth_header(test_db, teacher)

        response = await client.post(
            f"/users/{guardian.id}/guardian-deletion", headers=headers
        )

        assert response.status_code == 403

    async def test_returns_401_when_unauthenticated(
        self,
        client: AsyncClient,
        guardian: User,
    ):
        response = await client.post(f"/users/{guardian.id}/guardian-deletion")

        assert response.status_code == 401


class TestCancelGuardianDeletion:
    async def test_returns_204_on_success(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        mock_send_account_deletion_canceled_email,
        mock_delete_cache,
    ):
        guardian_pending = await make_guardian(
            test_db, status=UserStatus.PENDING_DELETION, is_active=False
        )
        headers = await make_auth_header(test_db, system_admin)

        response = await client.post(
            f"/users/{guardian_pending.id}/cancel-deletion", headers=headers
        )

        assert response.status_code == 204

    async def test_returns_404_when_not_found(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        headers = await make_auth_header(test_db, system_admin)

        response = await client.post("/users/999999/cancel-deletion", headers=headers)

        assert response.status_code == 404

    async def test_returns_404_for_non_pending_guardian(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        guardian: User,
    ):
        headers = await make_auth_header(test_db, system_admin)

        response = await client.post(
            f"/users/{guardian.id}/cancel-deletion", headers=headers
        )

        assert response.status_code == 404

    async def test_returns_403_for_non_admin(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        teacher: User,
        mocker,
    ):
        guardian_pending = await make_guardian(
            test_db, status=UserStatus.PENDING_DELETION, is_active=False
        )
        headers = await make_auth_header(test_db, teacher)

        response = await client.post(
            f"/users/{guardian_pending.id}/cancel-deletion", headers=headers
        )

        assert response.status_code == 403

    async def test_returns_401_when_unauthenticated(
        self,
        client: AsyncClient,
    ):
        response = await client.post("/users/1/cancel-deletion")

        assert response.status_code == 401


class TestDeactivateUser:
    async def test_deactivate_user_returns_204(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        teacher: User,
    ):
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch(
            f"/users/{teacher.id}/deactivation", headers=headers
        )

        assert response.status_code == 204
        deactivated = await UserRepositoryBase.get_user_by_id(test_db, teacher.id)
        assert deactivated.is_active is False

    async def test_deactivate_user_returns_404_when_not_found(
        self, test_db: AsyncSession, client: AsyncClient, system_admin: User
    ):
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch("/users/999999/deactivation", headers=headers)

        assert response.status_code == 404

    async def test_deactivate_user_returns_409_when_already_inactive(
        self, test_db: AsyncSession, client: AsyncClient, system_admin: User
    ):
        deactivated = await make_deactivated_user(test_db)
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch(
            f"/users/{deactivated.id}/deactivation", headers=headers
        )

        assert response.status_code == 409

    async def test_deactivate_user_returns_404_for_system_admin_target(
        self, test_db: AsyncSession, client: AsyncClient, system_admin: User
    ):
        other_admin = await make_system_admin(test_db)
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch(
            f"/users/{other_admin.id}/deactivation", headers=headers
        )

        assert response.status_code == 404

    async def test_deactivate_user_returns_403_for_non_admin(
        self, test_db: AsyncSession, client: AsyncClient, teacher: User, student: User
    ):
        headers = await make_auth_header(test_db, teacher)

        response = await client.patch(
            f"/users/{student.id}/deactivation", headers=headers
        )

        assert response.status_code == 403

    async def test_deactivate_user_returns_401_when_unauthenticated(
        self, client: AsyncClient, teacher: User
    ):
        response = await client.patch(f"/users/{teacher.id}/deactivation")

        assert response.status_code == 401

    async def test_deactivate_user_returns_422_for_invalid_path_id(
        self, test_db: AsyncSession, client: AsyncClient, system_admin: User
    ):
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch("/users/0/deactivation", headers=headers)

        assert response.status_code == 422


class TestActivateUser:
    async def test_activate_user_returns_204(
        self, test_db: AsyncSession, client: AsyncClient, system_admin: User
    ):
        deactivated = await make_deactivated_user(test_db)
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch(
            f"/users/{deactivated.id}/activation", headers=headers
        )

        assert response.status_code == 204
        activated = await UserRepositoryBase.get_user_by_id(test_db, deactivated.id)
        assert activated.is_active is True

    async def test_activate_user_returns_404_when_not_found(
        self, test_db: AsyncSession, client: AsyncClient, system_admin: User
    ):
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch("/users/999999/activation", headers=headers)

        assert response.status_code == 404

    async def test_activate_user_returns_409_when_already_active(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        teacher: User,
    ):
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch(
            f"/users/{teacher.id}/activation", headers=headers
        )

        assert response.status_code == 409

    async def test_activate_user_returns_403_for_non_admin(
        self, test_db: AsyncSession, client: AsyncClient, teacher: User
    ):
        deactivated = await make_deactivated_user(test_db)
        headers = await make_auth_header(test_db, teacher)

        response = await client.patch(
            f"/users/{deactivated.id}/activation", headers=headers
        )

        assert response.status_code == 403

    async def test_activate_user_returns_401_when_unauthenticated(
        self, client: AsyncClient
    ):
        deactivated_id = 1
        response = await client.patch(f"/users/{deactivated_id}/activation")

        assert response.status_code == 401

    async def test_activate_user_returns_422_for_invalid_path_id(
        self, test_db: AsyncSession, client: AsyncClient, system_admin: User
    ):
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch("/users/0/activation", headers=headers)

        assert response.status_code == 422


class TestCreateResetPasswordRequest:
    async def test_returns_204(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        teacher: User,
    ):
        headers = await make_auth_header(test_db, system_admin)

        response = await client.post(f"/users/{teacher.id}/password", headers=headers)

        assert response.status_code == 204

    async def test_returns_404_when_not_found(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        headers = await make_auth_header(test_db, system_admin)

        response = await client.post("/users/999999/password", headers=headers)

        assert response.status_code == 404

    async def test_returns_404_for_system_admin_target(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        other_admin = await make_system_admin(test_db)
        headers = await make_auth_header(test_db, system_admin)

        response = await client.post(
            f"/users/{other_admin.id}/password", headers=headers
        )

        assert response.status_code == 404

    async def test_returns_403_for_non_admin(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        teacher: User,
        student: User,
    ):
        headers = await make_auth_header(test_db, teacher)

        response = await client.post(f"/users/{student.id}/password", headers=headers)

        assert response.status_code == 403

    async def test_returns_401_when_unauthenticated(
        self,
        client: AsyncClient,
        teacher: User,
    ):
        response = await client.post(f"/users/{teacher.id}/password")

        assert response.status_code == 401

    async def test_returns_422_for_invalid_path_id(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        headers = await make_auth_header(test_db, system_admin)

        response = await client.post("/users/0/password", headers=headers)

        assert response.status_code == 422


async def _get_pending_email_for(db, recipient_user_id: int) -> PendingEmail:
    result = await db.execute(
        select(PendingEmail).where(PendingEmail.recipient_user_id == recipient_user_id)
    )

    return result.scalar_one()


class TestResendActivationInvite:
    async def test_system_admin_resends_invite_returns_204(
        self, test_db, client, system_admin
    ):
        target = await make_user(
            test_db, role=UserRole.TEACHER, status=UserStatus.PENDING_ACTIVATION
        )
        headers = await make_auth_header(test_db, system_admin)

        response = await client.post(
            f"/users/{target.id}/resend-invite", headers=headers
        )

        assert response.status_code == 204
        assert response.content == b""

        pending_email = await _get_pending_email_for(test_db, target.id)
        assert pending_email.recipient == target.email

    async def test_nonexistent_target_returns_404(self, test_db, client, system_admin):
        headers = await make_auth_header(test_db, system_admin)

        response = await client.post("/users/999999999/resend-invite", headers=headers)

        assert response.status_code == 404

    async def test_system_admin_target_returns_404(self, test_db, client, system_admin):
        other_admin = await make_system_admin(
            test_db, status=UserStatus.PENDING_ACTIVATION
        )
        headers = await make_auth_header(test_db, system_admin)

        response = await client.post(
            f"/users/{other_admin.id}/resend-invite", headers=headers
        )

        assert response.status_code == 404

    async def test_target_not_pending_activation_returns_404(
        self, test_db, client, system_admin
    ):
        active_target = await make_teacher(test_db, status=UserStatus.ACTIVE)
        headers = await make_auth_header(test_db, system_admin)

        response = await client.post(
            f"/users/{active_target.id}/resend-invite", headers=headers
        )

        assert response.status_code == 404

    async def test_non_admin_caller_forbidden(self, test_db, client, teacher):
        target = await make_user(
            test_db, role=UserRole.STUDENT, status=UserStatus.PENDING_ACTIVATION
        )
        headers = await make_auth_header(test_db, teacher)

        response = await client.post(
            f"/users/{target.id}/resend-invite", headers=headers
        )

        assert response.status_code == 403

    async def test_unauthenticated_caller_returns_401(self, test_db, client):
        target = await make_user(
            test_db, role=UserRole.STUDENT, status=UserStatus.PENDING_ACTIVATION
        )

        response = await client.post(f"/users/{target.id}/resend-invite")

        assert response.status_code == 401


class TestGetStaffEndpoint:
    async def test_returns_200_with_staff_only(
        self, test_db, client, system_admin, teacher, vice_director, student
    ):
        headers = await make_auth_header(test_db, system_admin)

        response = await client.get("/users/staff", headers=headers)

        assert response.status_code == 200
        body = response.json()
        returned_ids = {item["id"] for item in body["items"]}
        assert teacher.id in returned_ids
        assert vice_director.id in returned_ids
        assert student.id not in returned_ids

    async def test_forbidden_for_non_admin(self, test_db, client, teacher):
        headers = await make_auth_header(test_db, teacher)

        response = await client.get("/users/staff", headers=headers)

        assert response.status_code == 403

    async def test_unauthenticated_returns_401(self, client):
        response = await client.get("/users/staff")

        assert response.status_code == 401

    async def test_limit_exceeding_max_returns_422(self, test_db, client, system_admin):
        headers = await make_auth_header(test_db, system_admin)

        response = await client.get(
            "/users/staff", params={"limit": 101}, headers=headers
        )

        assert response.status_code == 422
