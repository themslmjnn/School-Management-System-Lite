from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from emails.repository import PendingEmailRepository
from tests.conftest import make_auth_header
from tests.factories import make_deactivated_user, make_system_admin, make_teacher
from users.models.users import User
from users.repositories.users import UserRepositoryBase
from users.schemas.users import CreateStaffAdmin, CreateStudentAdmin
from utils.enums import UserRole


class TestRegisterStaffRoute:
    async def test_creates_user_with_invite_token(
        self,
        test_db,
        client,
        system_admin,
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

    async def test_rejects_system_admin_role(
        self,
        test_db,
        client,
        system_admin,
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
        assert response.json()["detail"] == "System admin creation via API is forbidden"

    async def test_rejects_director_role(
        self,
        test_db,
        client,
        system_admin,
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
        assert response.json()["detail"] == "Director creation via API is forbidden"

    async def test_rejects_student_role(
        self,
        test_db,
        client,
        system_admin,
        valid_create_staff_request: CreateStaffAdmin,
    ):
        headers = await make_auth_header(test_db, system_admin)
        valid_create_staff_request.role = UserRole.STUDENT

        response = await client.post(
            "/users",
            json=valid_create_staff_request.model_dump(mode="json"),
            headers=headers,
        )

        assert response.status_code == 403
        assert (
            response.json()["detail"]
            == "Student creation via staff service is forbidden"
        )

    @pytest.mark.parametrize(
        ("existing_user_data", "request_override"),
        [
            (
                {"username": "taken_username"},
                {"username": "taken_username"},
            ),
            (
                {"email": "taken@example.com", "phone_number": "+15551112222"},
                {"email": "taken@example.com", "phone_number": "+15551112222"},
            ),
        ],
    )
    async def test_reject_duplicate_fields(
        self,
        test_db,
        client,
        system_admin,
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

    async def test_returns_403_for_non_admin(
        self, test_db, client, teacher, valid_create_staff_request: CreateStaffAdmin
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
        test_db,
        client,
        system_admin,
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


class TestRegisterStudentRoute:
    async def test_creates_student_with_invite_token(
        self,
        test_db,
        client,
        system_admin,
        valid_create_student_request: CreateStudentAdmin,
    ):
        headers = await make_auth_header(test_db, system_admin)

        response = await client.post(
            "/users/student",
            json=valid_create_student_request.model_dump(mode="json"),
            headers=headers,
        )

        data = response.json()

        assert response.status_code == 201
        assert data["id"] is not None
        assert data["role"] == "STUDENT"
        assert data["is_active"] is False

    async def test_reject_duplicate_username(
        self,
        test_db,
        client,
        system_admin,
        valid_create_student_request: CreateStudentAdmin,
    ):
        await make_teacher(test_db, username="taken_username")
        valid_create_student_request.username = "taken_username"

        headers = await make_auth_header(test_db, system_admin)

        response = await client.post(
            "/users/student",
            json=valid_create_student_request.model_dump(mode="json"),
            headers=headers,
        )

        assert response.status_code == 409

    async def test_returns_403_for_non_admin(
        self, test_db, client, teacher, valid_create_student_request: CreateStudentAdmin
    ):
        headers = await make_auth_header(test_db, teacher)

        response = await client.post(
            "/users/student",
            json=valid_create_student_request.model_dump(mode="json"),
            headers=headers,
        )

        assert response.status_code == 403

    async def test_unauthenticated_request_returns_401(self, client):
        response = await client.post("/users/student")

        assert response.status_code == 401

    async def test_rejects_invalid_username(
        self,
        test_db,
        client,
        system_admin,
        valid_create_student_request: CreateStudentAdmin,
    ):
        headers = await make_auth_header(test_db, system_admin)
        payload = valid_create_student_request.model_dump(mode="json")
        payload["username"] = "bad-name!"

        response = await client.post("/users/student", json=payload, headers=headers)

        errors = response.json()["detail"]
        error_fields = [error["loc"][-1] for error in errors]

        assert response.status_code == 422
        assert "username" in error_fields

    async def test_rejects_missing_date_of_birth(
        self,
        test_db,
        client,
        system_admin,
        valid_create_student_request: CreateStudentAdmin,
    ):
        headers = await make_auth_header(test_db, system_admin)
        payload = valid_create_student_request.model_dump(mode="json")
        del payload["date_of_birth"]

        response = await client.post("/users/student", json=payload, headers=headers)

        errors = response.json()["detail"]
        error_fields = [error["loc"][-1] for error in errors]

        assert response.status_code == 422
        assert "date_of_birth" in error_fields


class TestDeleteParentRoute:
    async def test_delete_parent_returns_204(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        parent: User,
    ) -> None:
        headers = await make_auth_header(test_db, system_admin)

        response = await client.delete(f"/users/{parent.id}", headers=headers)

        assert response.status_code == 204
        deleted_user = await UserRepositoryBase.get_user_by_id(test_db, parent.id)
        assert deleted_user is None

    async def test_delete_parent_returns_404_when_not_found(
        self, test_db: AsyncSession, client: AsyncClient, system_admin: User
    ) -> None:
        headers = await make_auth_header(test_db, system_admin)

        response = await client.delete("/users/999999", headers=headers)

        assert response.status_code == 404

    async def test_delete_parent_returns_404_for_non_parent_role(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        teacher: User,
    ) -> None:
        headers = await make_auth_header(test_db, system_admin)

        response = await client.delete(f"/users/{teacher.id}", headers=headers)

        assert response.status_code == 404

    async def test_delete_parent_returns_403_for_non_admin(
        self, test_db: AsyncSession, client: AsyncClient, teacher: User, parent: User
    ) -> None:
        headers = await make_auth_header(test_db, teacher)

        response = await client.delete(f"/users/{parent.id}", headers=headers)

        assert response.status_code == 403

    async def test_delete_parent_returns_401_when_unauthenticated(
        self, client: AsyncClient, parent: User
    ) -> None:
        response = await client.delete(f"/users/{parent.id}")

        assert response.status_code == 401

    async def test_delete_parent_returns_422_for_invalid_path_id(
        self, test_db: AsyncSession, client: AsyncClient, system_admin: User
    ) -> None:
        headers = await make_auth_header(test_db, system_admin)

        response = await client.delete("/users/0", headers=headers)

        assert response.status_code == 422


class TestDeactivateUserRoute:
    async def test_deactivate_user_returns_204(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        teacher: User,
    ) -> None:
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch(
            f"/users/{teacher.id}/deactivate", headers=headers
        )

        assert response.status_code == 204
        deactivated = await UserRepositoryBase.get_user_by_id(test_db, teacher.id)
        assert deactivated.is_active is False

    async def test_deactivate_user_returns_404_when_not_found(
        self, test_db: AsyncSession, client: AsyncClient, system_admin: User
    ) -> None:
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch("/users/999999/deactivate", headers=headers)

        assert response.status_code == 404

    async def test_deactivate_user_returns_409_when_already_inactive(
        self, test_db: AsyncSession, client: AsyncClient, system_admin: User
    ) -> None:
        deactivated = await make_deactivated_user(test_db)
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch(
            f"/users/{deactivated.id}/deactivate", headers=headers
        )

        assert response.status_code == 409

    async def test_deactivate_user_returns_404_for_system_admin_target(
        self, test_db: AsyncSession, client: AsyncClient, system_admin: User
    ) -> None:
        other_admin = await make_system_admin(test_db)
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch(
            f"/users/{other_admin.id}/deactivate", headers=headers
        )

        assert response.status_code == 404

    async def test_deactivate_user_returns_403_for_non_admin(
        self, test_db: AsyncSession, client: AsyncClient, teacher: User, student: User
    ) -> None:
        headers = await make_auth_header(test_db, teacher)

        response = await client.patch(
            f"/users/{student.id}/deactivate", headers=headers
        )

        assert response.status_code == 403

    async def test_deactivate_user_returns_401_when_unauthenticated(
        self, client: AsyncClient, teacher: User
    ) -> None:
        response = await client.patch(f"/users/{teacher.id}/deactivate")

        assert response.status_code == 401

    async def test_deactivate_user_returns_422_for_invalid_path_id(
        self, test_db: AsyncSession, client: AsyncClient, system_admin: User
    ) -> None:
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch("/users/0/deactivate", headers=headers)

        assert response.status_code == 422


class TestActivateUserRoute:
    async def test_activate_user_returns_204(
        self, test_db: AsyncSession, client: AsyncClient, system_admin: User
    ) -> None:
        deactivated = await make_deactivated_user(test_db)
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch(
            f"/users/{deactivated.id}/activate", headers=headers
        )

        assert response.status_code == 204
        activated = await UserRepositoryBase.get_user_by_id(test_db, deactivated.id)
        assert activated.is_active is True

    async def test_activate_user_returns_404_when_not_found(
        self, test_db: AsyncSession, client: AsyncClient, system_admin: User
    ) -> None:
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch("/users/999999/activate", headers=headers)

        assert response.status_code == 404

    async def test_activate_user_returns_409_when_already_active(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        teacher: User,
    ) -> None:
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch(f"/users/{teacher.id}/activate", headers=headers)

        assert response.status_code == 409

    async def test_activate_user_returns_403_for_non_admin(
        self, test_db: AsyncSession, client: AsyncClient, teacher: User
    ) -> None:
        deactivated = await make_deactivated_user(test_db)
        headers = await make_auth_header(test_db, teacher)

        response = await client.patch(
            f"/users/{deactivated.id}/activate", headers=headers
        )

        assert response.status_code == 403

    async def test_activate_user_returns_401_when_unauthenticated(
        self, client: AsyncClient
    ) -> None:
        deactivated_id = 1
        response = await client.patch(f"/users/{deactivated_id}/activate")

        assert response.status_code == 401

    async def test_activate_user_returns_422_for_invalid_path_id(
        self, test_db: AsyncSession, client: AsyncClient, system_admin: User
    ) -> None:
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch("/users/0/activate", headers=headers)

        assert response.status_code == 422


class TestUpdateUserRoute:
    async def test_update_user_returns_200_and_expected_shape(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        teacher: User,
    ) -> None:
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch(
            f"/users/{teacher.id}",
            json={"firstname": "UpdatedFirstName"},
            headers=headers,
        )

        assert response.status_code == 200
        body = response.json()
        assert body["firstname"] == "UpdatedFirstName"
        assert "id" not in body

    async def test_update_user_returns_404_when_not_found(
        self, test_db: AsyncSession, client: AsyncClient, system_admin: User
    ) -> None:
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch(
            "/users/999999", json={"firstname": "Whoever"}, headers=headers
        )

        assert response.status_code == 404

    async def test_update_user_returns_404_for_system_admin_target(
        self, test_db: AsyncSession, client: AsyncClient, system_admin: User
    ) -> None:
        other_admin = await make_system_admin(test_db)
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch(
            f"/users/{other_admin.id}", json={"firstname": "Whoever"}, headers=headers
        )

        assert response.status_code == 404

    async def test_update_user_returns_409_when_no_changes(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        teacher: User,
    ) -> None:
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch(f"/users/{teacher.id}", json={}, headers=headers)

        assert response.status_code == 409

    async def test_update_user_returns_409_for_duplicate_username(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        teacher: User,
    ) -> None:
        await make_teacher(test_db, username="taken_username")
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch(
            f"/users/{teacher.id}",
            json={"username": "taken_username"},
            headers=headers,
        )

        assert response.status_code == 409

    async def test_update_user_returns_403_for_non_admin(
        self, test_db: AsyncSession, client: AsyncClient, teacher: User, student: User
    ) -> None:
        headers = await make_auth_header(test_db, teacher)

        response = await client.patch(
            f"/users/{student.id}", json={"firstname": "Whoever"}, headers=headers
        )

        assert response.status_code == 403

    async def test_update_user_returns_401_when_unauthenticated(
        self, client: AsyncClient, teacher: User
    ) -> None:
        response = await client.patch(
            f"/users/{teacher.id}", json={"firstname": "Whoever"}
        )

        assert response.status_code == 401

    async def test_update_user_returns_422_for_invalid_username_symbol(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        teacher: User,
    ) -> None:
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch(
            f"/users/{teacher.id}", json={"username": "bad-name!"}, headers=headers
        )

        assert response.status_code == 422


class TestUpdateUserEmailRoute:
    async def test_update_user_email_returns_204(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        teacher: User,
    ) -> None:
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch(
            f"/users/{teacher.id}/email",
            json={"new_email": "fresh.email@example.com"},
            headers=headers,
        )

        assert response.status_code == 204
        updated_user = await UserRepositoryBase.get_user_by_id(test_db, teacher.id)
        assert updated_user.email == "fresh.email@example.com"

    async def test_update_user_email_returns_404_when_not_found(
        self, test_db: AsyncSession, client: AsyncClient, system_admin: User
    ) -> None:
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch(
            "/users/999999/email",
            json={"new_email": "nobody@example.com"},
            headers=headers,
        )

        assert response.status_code == 404

    async def test_update_user_email_returns_409_for_duplicate_contact(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        teacher: User,
    ) -> None:
        await make_teacher(
            test_db, email="taken@example.com", phone_number=teacher.phone_number
        )
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch(
            f"/users/{teacher.id}/email",
            json={"new_email": "taken@example.com"},
            headers=headers,
        )

        assert response.status_code == 409

    async def test_update_user_email_returns_403_for_non_admin(
        self, test_db: AsyncSession, client: AsyncClient, teacher: User, student: User
    ) -> None:
        headers = await make_auth_header(test_db, teacher)

        response = await client.patch(
            f"/users/{student.id}/email",
            json={"new_email": "whoever@example.com"},
            headers=headers,
        )

        assert response.status_code == 403

    async def test_update_user_email_returns_401_when_unauthenticated(
        self, client: AsyncClient, teacher: User
    ) -> None:
        response = await client.patch(
            f"/users/{teacher.id}/email", json={"new_email": "whoever@example.com"}
        )

        assert response.status_code == 401

    async def test_update_user_email_returns_422_for_invalid_email(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        teacher: User,
    ) -> None:
        headers = await make_auth_header(test_db, system_admin)

        response = await client.patch(
            f"/users/{teacher.id}/email",
            json={"new_email": "not-an-email"},
            headers=headers,
        )

        assert response.status_code == 422


class TestCreateResetPasswordRequestRoute:
    async def test_create_reset_password_request_returns_204(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        teacher: User,
    ) -> None:
        """Will fail until the FLAGGED BUG in create_reset_password_request
        is fixed (PendingEmailRepository.create -> add_pending_email)."""
        headers = await make_auth_header(test_db, system_admin)

        response = await client.post(f"/users/{teacher.id}/password", headers=headers)

        assert response.status_code == 204

    async def test_create_reset_password_request_returns_404_when_not_found(
        self, test_db: AsyncSession, client: AsyncClient, system_admin: User
    ) -> None:
        headers = await make_auth_header(test_db, system_admin)

        response = await client.post("/users/999999/password", headers=headers)

        assert response.status_code == 404

    async def test_create_reset_password_request_returns_403_for_non_admin(
        self, test_db: AsyncSession, client: AsyncClient, teacher: User, student: User
    ) -> None:
        headers = await make_auth_header(test_db, teacher)

        response = await client.post(f"/users/{student.id}/password", headers=headers)

        assert response.status_code == 403

    async def test_create_reset_password_request_returns_401_when_unauthenticated(
        self, client: AsyncClient, teacher: User
    ) -> None:
        response = await client.post(f"/users/{teacher.id}/password")

        assert response.status_code == 401

    async def test_create_reset_password_request_returns_422_for_invalid_path_id(
        self, test_db: AsyncSession, client: AsyncClient, system_admin: User
    ) -> None:
        headers = await make_auth_header(test_db, system_admin)

        response = await client.post("/users/0/password", headers=headers)

        assert response.status_code == 422
