from sqlalchemy.exc import IntegrityError

from src.utils.constants import HTTP409


class AppException(Exception):
    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


# AUTHENTICATION
class EmptyCredentialsError(AppException):
    pass


class InvalidCredentialsError(AppException):
    pass


class InvalidAccessTokenError(AppException):
    pass


class InvalidRefreshTokenError(AppException):
    pass


class ExpiredRefreshTokenError(AppException):
    pass


class AccountInactiveError(AppException):
    pass


class AccountLockedError(AppException):
    pass


# AUTHORIZATION
class AccessDeniedError(AppException):
    pass


# NON-AUTH TOKENS
class InvalidInviteTokenError(AppException):
    pass


class ExpiredInviteTokenError(AppException):
    pass


class InvalidResetPasswordTokenError(AppException):
    pass


class ExpiredResetPasswordTokenError(AppException):
    pass


# USER
class UsernameAlreadyTakenError(AppException):
    pass


class DuplicateValueError(AppException):
    pass


class MaxNumberOfIdenticalContactsError(AppException):
    pass


class DateOfBirthNullError(AppException):
    pass


# ROLE RESTRICTIONS
class CannotCreateSystemAdminError(AppException):
    pass


class CannotCreateDirectorError(AppException):
    pass


class InvalidGuardianLinkError(AppException):
    pass


class GuardianLinkAlreadyExistsError(AppException):
    pass


class GuardianSlotAlreadyFilledError(AppException):
    pass


class GuardianLinkNotFoundError(AppException):
    pass


class PendingEmailNotFoundError(AppException):
    pass


class UserNotFoundError(AppException):
    pass


class NoChangesDetectedError(AppException):
    pass


class UserAlreadyInactiveError(AppException):
    pass


class CannotCreateStudentError(AppException):
    pass


class UserAlreadyActiveError(AppException):
    pass


def handle_username_integrity_error(error: IntegrityError) -> None:
    error_str = str(error.orig)

    if "users_username_key" in error_str:
        raise UsernameAlreadyTakenError(HTTP409.USERNAME)


def handle_non_student_unique_contact_error(error: IntegrityError) -> None:
    error_str = str(error.orig)

    if "uix_non_student_unique_contact" in error_str:
        raise DuplicateValueError(HTTP409.DUPLICATE_VALUE)
