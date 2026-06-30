class SessionCacheKey:
    @staticmethod
    def access_token_version_key(user_id: int) -> str:
        return f"user:token_version:{user_id}"


class UserCacheKey:
    @staticmethod
    def user_detail_key_admin(user_id: int) -> str:
        return f"users:detail:{user_id}:admin"

    @staticmethod
    def user_detail_key_staff(user_id: int) -> str:
        return f"users:detail:{user_id}:staff"

    @staticmethod
    def user_detail_key_self(user_id: int) -> str:
        return f"users:detail:{user_id}:self"
