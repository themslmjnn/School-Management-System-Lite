from sqlalchemy.exc import IntegrityError

from src.users.exceptions.constants import HTTP409
from src.utils.base_exception import AppException


# USER
class UserNotFoundError(AppException):
    pass


class UsernameAlreadyTakenError(AppException):
    pass


class DuplicateEmailError(AppException):
    pass


class DuplicatePhoneNumberError(AppException):
    pass


class PendingEmailNotFoundError(AppException):
    pass


class UserAlreadyActiveError(AppException):
    pass


class UserAlreadyInactiveError(AppException):
    pass


class UserAlreadyPendingDeletionError(AppException):
    pass


class MaxStudentsPerEmailError(AppException):
    pass


class MaxStudentsPerPhoneNumberError(AppException):
    pass


class MaxStaffOrGuardianPerEmailError(AppException):
    pass


class MaxStaffOrGuardianPerPhoneNumberError(AppException):
    pass


class UserTypeMismatchError(AppException):
    pass


class UserNotPendingActivationError(AppException):
    pass


class ProfileFieldsNotEditableForRoleError(AppException):
    pass


class NoPendingEmailChangeError(AppException):
    pass


class EmailChangeCodeExpiredError(AppException):
    pass


class InvalidEmailChangeCodeError(AppException):
    pass


class IncorrectPasswordError(AppException):
    pass


# GUARDIAN LINK
class GuardianSlotAlreadyFilledError(AppException):
    pass


class GuardianLinkAlreadyExistsError(AppException):
    pass


class InvalidGuardianLinkError(AppException):
    pass


class GuardianLinkNotFoundError(AppException):
    pass


class DuplicateEmailChangeRequestError(AppException):
    pass


# ROLE RESTRICTIONS
class CannotCreateDirectorError(AppException):
    pass


class CannotCreateSystemAdminError(AppException):
    pass


# INTEGRITY ERROR HANDLERS
def handle_username_integrity_error(error: IntegrityError) -> None:
    if "users_username_key" in str(error.orig):
        raise UsernameAlreadyTakenError(HTTP409.USERNAME)


def handle_non_student_unique_contact_error(error: IntegrityError) -> None:
    error_detail = str(error.orig)

    if "uix_non_student_unique_phone" in error_detail:
        raise DuplicatePhoneNumberError(HTTP409.DUPLICATE_PHONE_NUMBER)

    if "uix_non_student_unique_email" in error_detail:
        raise DuplicateEmailError(HTTP409.DUPLICATE_EMAIL)
