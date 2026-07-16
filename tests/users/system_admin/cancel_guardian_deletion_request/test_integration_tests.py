from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models.user import User
from src.utils.enums import UserStatus
from tests.conftest import make_auth_header
from tests.factories import make_guardian


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
