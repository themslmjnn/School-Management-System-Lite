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
