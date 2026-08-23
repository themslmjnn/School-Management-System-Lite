from sqlalchemy.exc import IntegrityError

from utils.constants import HTTP409


class AppException(Exception):
    status_code: int = 500

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class EmptyCredentialsError(AppException):
    status_code = 400


class InvalidCredentialsError(AppException):
    status_code = 401


class InvalidAccessTokenError(AppException):
    status_code = 401


class InvalidRefreshTokenError(AppException):
    status_code = 401


class ExpiredRefreshTokenError(AppException):
    status_code = 401


class AccountInactiveError(AppException):
    status_code = 409


class AccountLockedError(AppException):
    status_code = 403


class AccessDeniedError(AppException):
    status_code = 403


class InvalidInviteTokenError(AppException):
    status_code = 400


class ExpiredInviteTokenError(AppException):
    status_code = 400


class NoChangesDetectedError(AppException):
    status_code = 400


class ExpiredResetPasswordTokenError(AppException):
    status_code = 400


class InvalidResetPasswordTokenError(AppException):
    status_code = 400


class PendingEmailNotFoundError(AppException):
    status_code = 404


class SubjectNotFoundError(AppException):
    status_code = 404


class SubjectCodeAlreadyExistsError(AppException):
    status_code = 409


class SubjectAlreadyArchivedError(AppException):
    status_code = 409


class SubjectNotArchivedError(AppException):
    status_code = 409


class GroupNotFoundError(AppException):
    status_code = 404


class GroupNameYearAlreadyExistsError(AppException):
    status_code = 409


class GroupAlreadyArchivedError(AppException):
    status_code = 409


class GroupNotArchivedError(AppException):
    status_code = 409


class GroupArchiveBlockedError(AppException):
    status_code = 409


class GroupCapacityExceededError(AppException):
    status_code = 409


class GroupIsNotArchivedError(AppException):
    status_code = 409


def handle_subject_code_integrity_error(error: IntegrityError) -> None:
    if "ix_subjects_code" in str(error.orig):
        raise SubjectCodeAlreadyExistsError(HTTP409.SUBJECT_CODE)


def handle_group_name_year_integrity_error(error: IntegrityError) -> None:
    if "uix_group_name_academic_year" in str(error.orig):
        raise GroupNameYearAlreadyExistsError(HTTP409.GROUP_NAME)


def raise_unhandled_integrity_error(error: IntegrityError) -> None:
    raise error
