from enum import StrEnum


class UserRole(StrEnum):
    SYSTEM_ADMIN = "system_admin"
    DIRECTOR = "director"
    VICE_DIRECTOR = "vice_director"
    TEACHER = "teacher"
    STUDENT = "student"
    PARENT = "parent"


class UserStatus(StrEnum):
    ACTIVE = "active"
    GRADUATED = "graduated"
    EXPELLED = "expelled"
    WITHDRAWN = "withdrawn"
    DEACTIVATED = "deactivated"
    PENDING_DELETION = "pending_deletion"
    DELETED = "deleted"
    PENDING_ACTIVATION = "pending_activation"


class GuardianPriority(StrEnum):
    PRIMARY = "primary"
    SECONDARY = "secondary"


class EmailType(StrEnum):
    INVITE = "invite"
    PASSWORD_RESET_ADMIN = "password_reset_admin"
    ACTIVATION_WITH_TOKEN = "activation_with_token"
    ACCOUNT_DEACTIVATION = "account_deactivation"
    ACCOUNT_ACTIVATION = "account_activation"
    ACCOUNT_DELETION = "account_deletion"
    ADMIN_EMAIL_OVERRIDE = "admin_email_override"


class EmailSendingStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class UserSortField(StrEnum):
    created_at = "created_at"
    first_name = "first_name"
    last_name = "last_name"


class OrderBy(StrEnum):
    asc = "asc"
    desc = "desc"
