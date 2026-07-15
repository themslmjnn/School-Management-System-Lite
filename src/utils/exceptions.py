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


class NoChangesDetectedError(AppException):
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


class SubjectNotFoundError(AppException):
    pass


class GroupNotFoundError(AppException):
    pass


class SubjectCodeAlreadyExistsError(AppException):
    pass


class GroupNameYearAlreadyExistsError(AppException):
    pass


class SubjectAlreadyArchivedError(AppException):
    pass


class SubjectNotArchivedError(AppException):
    pass


class GroupAlreadyArchivedError(AppException):
    pass


class GroupNotArchivedError(AppException):
    pass


class SubjectArchiveBlockedError(AppException):
    pass


class GroupArchiveBlockedError(AppException):
    pass


class GroupCapacityExceededError(AppException):
    pass


class TeachingAssignmentAlreadyExistsError(AppException):
    pass


class HeadOfClassSlotAlreadyFilledError(AppException):
    pass


class TeacherAlreadyHeadOfClassForGroupError(AppException):
    pass


class StudentAlreadyEnrolledError(AppException):
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


def handle_subject_code_integrity_error(error: IntegrityError) -> None:
    if "ix_subjects_code" in str(error.orig):
        raise SubjectCodeAlreadyExistsError(HTTP409.SUBJECT_CODE)


def handle_group_name_year_integrity_error(error: IntegrityError) -> None:
    if "uix_group_name_academic_year" in str(error.orig):
        raise GroupNameYearAlreadyExistsError(HTTP409.GROUP_NAME)


def raise_unhandled_integrity_error(error: IntegrityError) -> None:
    raise error
