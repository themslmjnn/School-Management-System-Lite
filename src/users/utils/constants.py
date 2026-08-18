from src.utils.enums import UserRole

STUDENT_MAX_SHARED_CONTACT = 3
TEACHER_MAX_SHARED_CONTACT = 1
SYSTEM_ADMIN_INVISIBLE_ROLES = frozenset({UserRole.SYSTEM_ADMIN})
TEACHER_ROLE = frozenset({UserRole.TEACHER})
STUDENT_ROLE = frozenset({UserRole.STUDENT})


class HTTP404:
    USER = "User not found"


class HTTP409:
    USERNAME = "Username already taken"
    DUPLICATE_PHONE_NUMBER = "Phone number already taken"
    DUPLICATE_EMAIL = "Email already taken"
