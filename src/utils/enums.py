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


class EmailSendingStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
