from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from core.security import generate_invite_token
from models.users import User, UserActivation, UserSession
from repositories.pending_emails import PendingEmailRepository
from repositories.users import UserRepositoryBase
from schemas.user import CreateUserAdmin
from utils.custom_exceptions import CannotCreateSystemAdminError
from utils.enums import EmailType, UserRole
from src.core.logging import get_logger
from src.core.config import settings
from sqlalchemy.exc import IntegrityError
from src.utils import email as email_sender
from src.utils.custom_exceptions import handle_user_integrity_error

logger = get_logger(__name__)

MESSAGE_404 = "User not found"


# class UserService:
#     @staticmethod
#     def get_users(db, user):
#         try:
#             require_admin(user)
#             result = UserRepository.get_users_admin(db)

#         except HTTPException:
#             require_director(user)
#             result = UserRepository.get_users_public(db)

#         return result

#     @staticmethod
#     def search_users(db, user, users_request):
#         try:
#             require_admin(user)

#         except HTTPException:
#             require_director(user)

#         return UserRepository.search_users(db, users_request)

#     @staticmethod
#     def update_user_info(db, user, user_id, user_request):
#         require_admin(user)

#         user = UserRepository.get_user_by_id(db, user_id)

#         ensure_exists(user, MESSAGE_404)

#         update_object(user, user_request)

#         db.commit()

#         return user

#     @staticmethod
#     def update_user_password(db, user, user_id, user_password_request, bcrypt_context):
#         try:
#             require_admin(user)

#         except HTTPException:
#             require_user(user, user_id)

#         user = UserRepository.get_user_by_id(db, user_id)

#         ensure_exists(user, MESSAGE_404)

#         verify_password(
#             user_password_request.old_password, user.password_hash, bcrypt_context
#         )

#         user.password_hash = hash_password(
#             user_password_request.new_password, bcrypt_context
#         )

#         db.commit()


class UserServiceAdmin:
    async def create_user(db: AsyncSession, current_user_id: int, create_request: CreateUserAdmin) -> User:
        if create_request.role == UserRole.system_admin:
            logger.warning(
                "user_creation_denied",
                reason="cannot_create_system_admin_through_api",
            )

            raise CannotCreateSystemAdminError("Cannot create system admin through API")
        
        raw_invite_token, hashed_invite_token = generate_invite_token()
        invite_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.INVITE_TOKEN_EXPIRES_HOURS)

        try:
            new_user = User(
                username=create_request.username,
                first_name=create_request.first_name,
                last_name=create_request.last_name,
                date_of_birth=create_request.date_of_birth,
                email=create_request.email,
                phone_number=create_request.phone_number,
                citizenship=create_request.citizenship,
                address=create_request.address,
                role=create_request.role,
                is_active=False,
            )

            UserRepositoryBase.add_user(db, new_user)

            await db.flush()

            new_user_activation = UserActivation(
                user_id=new_user.id,
                invite_token_hash=hashed_invite_token,
                invite_token_expires_at=invite_token_expires_at,
            )

            new_user_session = UserSession(user_id=new_user.id)

            UserRepositoryBase.add_user(db, new_user_activation)
            UserRepositoryBase.add_user(db, new_user_session)

            subject, html_body, text_body = email_sender.build_invite_email(
                raw_invite_token, new_user.email
            )

            PendingEmailRepository.add_pending_email(
                db,
                recipient=new_user.email,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
                email_type=EmailType.invite,
                triggered_by=current_user_id,
                recipient_user_id=new_user.id,
            )

            await db.commit()
            await db.refresh(new_user)

            logger.info(
                "user_created",
                new_user_id=new_user.id,
                role=new_user.role,
            )

            return new_user
        except IntegrityError as e:
            await db.rollback()

            logger.error(
                "user_creation_failed",
                reason="integrity_error",
                error=str(e.orig),
            )

            handle_user_integrity_error(e)
            raise