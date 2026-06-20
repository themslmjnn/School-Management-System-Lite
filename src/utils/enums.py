from enum import Enum


class UserRole(str, Enum):
    system_admin = "system_admin"
    director = "director"
    vice_director = "vice_director"
    teacher = "teacher"
    student = "student"
    parent = "parent"


class EmailType(str, Enum):
    invite = "invite"
    password_reset_admin = "password_reset_admin"
    activation_with_token = "activation_with_token"
    account_deactivation = "account_deactivation"
    account_activation = "account_activation"
    admin_email_override = "admin_email_override"


class EmailSendingStatus(str, Enum):
    pending = "pending"
    sent = "sent"
    failed = "failed"