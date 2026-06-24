from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.users.models import User
from src.utils.enums import UserRole


class AuthRepository:
    @staticmethod
    async def get_user_by_username(
        db: AsyncSession,
        username: str,
        *,
        load_session: bool = False,
        load_activation: bool = False,
        load_login_lockout: bool = False,
    ) -> User | None:
        query = select(User).filter(User.username == username)

        if load_session:
            query = query.options(joinedload(User.session))
        if load_activation:
            query = query.options(joinedload(User.activation))
        if load_login_lockout:
            query = query.options(joinedload(User.login_lockout))

        result = await db.execute(query)

        return result.scalar_one_or_none()