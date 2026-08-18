class SessionCacheKey:
    @staticmethod
    def access_token_version_key(user_id: int) -> str:
        return f"user:token_version:{user_id}"


class UserCacheKey:
    @staticmethod
    def user_detail_key_admin(user_id: int) -> str:
        return f"users:detail:{user_id}:admin"

    @staticmethod
    def user_detail_key_staf(user_id: int) -> str:
        return f"users:detail:{user_id}:staff"

    @staticmethod
    def user_detail_key_self(user_id: int) -> str:
        return f"users:detail:{user_id}:self"


class SubjectCacheKey:
    @staticmethod
    def subject_detail_key_admin(subject_id: int) -> str:
        return f"subjects:{subject_id}:admin"

    @staticmethod
    def subject_detail_key_non_admin(subject_id: int) -> str:
        return f"subjects:{subject_id}:non_admin"


class GroupCacheKey:
    @staticmethod
    def group_detail_key_admin(group_id: int) -> str:
        return f"groups:{group_id}:admin"

    @staticmethod
    def group_detail_key_non_admin(group_id: int) -> str:
        return f"groups:{group_id}:non_admin"
