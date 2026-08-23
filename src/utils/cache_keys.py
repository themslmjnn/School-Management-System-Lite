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


class EmailCacheKey:
    @staticmethod
    def email_detail_key(email_id: int) -> str:
        return f"emails:{email_id}:admin"


class SubjectCacheKey:
    @staticmethod
    def subject_detail_key_admin(subject_id: int) -> str:
        return f"subjects:{subject_id}:admin"

    @staticmethod
    def subject_detail_key_staff(subject_id: int) -> str:
        return f"subjects:{subject_id}:staff"


class GroupCacheKey:
    @staticmethod
    def group_detail_key_admin(group_id: int) -> str:
        return f"groups:{group_id}:admin"

    @staticmethod
    def group_detail_key_staff(group_id: int) -> str:
        return f"groups:{group_id}:staff"
