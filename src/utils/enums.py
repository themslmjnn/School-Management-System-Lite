from enum import StrEnum


class UserRole(StrEnum):
    SYSTEM_ADMIN = "system_admin"
    DIRECTOR = "director"
    VICE_DIRECTOR = "vice_director"
    TEACHER = "teacher"
    STUDENT = "student"
    GUARDIAN = "guardian"


class UserStatus(StrEnum):
    ACTIVE = "active"
    DEACTIVATED = "deactivated"
    DELETED = "deleted"
    PENDING_ACTIVATION = "pending_activation"
    PENDING_DELETION = "pending_deletion"
    GRADUATED = "graduated"
    EXPELLED = "expelled"
    WITHDRAWN = "withdrawn"


class GuardianPriority(StrEnum):
    PRIMARY = "primary"
    SECONDARY = "secondary"


class EmailType(StrEnum):
    INVITE = "invite"
    UPDATING_ACCOUNT = "updating_account"
    ADMIN_CREDENTIALS_OVERRIDE = "admin_credentials_override"
    CCOUNT_DELETION = "account_deletion"
    CANCEL_ACCOUNT_DELETION = "cancel_account_deletion"
    PASSWORD_RESET_ADMIN = "password_reset_admin"
    ACTIVATION_WITH_TOKEN = "activation_with_token"
    ACCOUNT_DEACTIVATION = "account_deactivation"
    ACCOUNT_ACTIVATION = "account_activation"
    EMAIL_CHANGE_CODE = "email_change_code"
    PASSWORD_CHANGED = "password_changed"


class EmailSendingStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class UserSortField(StrEnum):
    CREATED_AT = "created_at"
    FIRSTNAME = "firstname"
    LASTNAME = "lastname"


class OrderBy(StrEnum):
    ASC = "asc"
    DESC = "desc"
