from sqlalchemy.exc import IntegrityError

from src.subjects.exceptions.constants import HTTP409
from src.utils.base_exception import AppException


class SubjectNotFoundError(AppException):
    status_code = 404


class SubjectCodeAlreadyExistsError(AppException):
    status_code = 409


class SubjectAlreadyArchivedError(AppException):
    status_code = 409


class SubjectNotArchivedError(AppException):
    status_code = 409


class SubjectArchiveBlockedError(AppException):
    status_code = 409


class SubjectIsArchivedError(AppException):
    status_code = 409


class SubjectIsNotArchivedError(AppException):
    status_code = 409


# INTEGRITY ERROR HANDLERS
def handle_subject_code_integrity_error(error: IntegrityError) -> None:
    if "ix_subjects_code" in str(error.orig):
        raise SubjectCodeAlreadyExistsError(HTTP409.SUBJECT_CODE)
