from src.repositories.auth_repositories import AuthRepository


class AuthService:
    @staticmethod
    def authenticate_user(db, username: str, password: str, bcrypt_context):
        user = AuthRepository.get_user_by_username(db, username)

        if not user:
            return False

        if not bcrypt_context.verify(password, user.password_hash):
            return False

        return user
