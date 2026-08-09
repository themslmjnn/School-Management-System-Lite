from sqlalchemy.exc import IntegrityError

from src.users.exceptions.constants import HTTP409
from src.utils.base_exception import AppException


class UsernameAlreadyTakenError(AppException):
    status_code = 409


class MaxStudentsPerEmailError(AppException):
    status_code = 409


class MaxStudentsPerPhoneNumberError(AppException):
    status_code = 409


class MaxStaffOrGuardianPerEmailError(AppException):
    status_code = 409


class MaxStaffOrGuardianPerPhoneNumberError(AppException):
    status_code = 409


class UserNotFoundError(AppException):
    status_code = 404


class UserTypeMismatchError(AppException):
    status_code = 400


class DuplicateEmailError(AppException):
    status_code = 409


class DuplicatePhoneNumberError(AppException):
    status_code = 409


class GuardianAlreadyPendingDeletionError(AppException):
    status_code = 409


class UserAlreadyActiveError(AppException):
    status_code = 409


class UserAlreadyInactiveError(AppException):
    status_code = 409


class UserNotPendingActivationError(AppException):
    status_code = 404


class NoPendingEmailChangeError(AppException):
    status_code = 404


class EmailChangeCodeExpiredError(AppException):
    status_code = 400


class InvalidEmailChangeCodeError(AppException):
    status_code = 400


class IncorrectPasswordError(AppException):
    status_code = 400


# GUARDIAN LINK
class GuardianSlotAlreadyFilledError(AppException):
    status_code = 409


class GuardianLinkAlreadyExistsError(AppException):
    status_code = 409


class InvalidGuardianLinkError(AppException):
    status_code = 400


class GuardianLinkNotFoundError(AppException):
    status_code = 404


class DuplicateEmailChangeRequestError(AppException):
    status_code = 409


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


def handle_guardian_student_pair_error(error: IntegrityError) -> None:
    if "uix_guardian_student_pair" in str(error.orig):
        raise GuardianLinkAlreadyExistsError("This guardian link could not be created")


def handle_one_primary_guardian_per_student_error(error: IntegrityError) -> None:
    if "uix_one_primary_guardian_per_student" in str(error.orig):
        raise GuardianSlotAlreadyFilledError(
            "Guardian with this priority already exists"
        )


def handle_one_secondary_guardian_per_student_error(error: IntegrityError) -> None:
    if "uix_one_secondary_guardian_per_student" in str(error.orig):
        raise GuardianSlotAlreadyFilledError(
            "Guardian with this priority already exists"
        )
