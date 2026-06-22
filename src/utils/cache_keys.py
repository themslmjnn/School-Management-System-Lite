class SessionCacheKey:
    @staticmethod
    def access_token_version_key(user_id: int) -> str:
        return f"user:token_version:{user_id}"
