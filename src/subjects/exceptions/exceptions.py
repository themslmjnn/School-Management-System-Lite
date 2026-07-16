from sqlalchemy.exc import IntegrityError

from src.subjects.exceptions.constants import HTTP409
from src.utils.base_exception import AppException


class SubjectNotFoundError(AppException):
    pass


class SubjectCodeAlreadyExistsError(AppException):
    pass


class SubjectAlreadyArchivedError(AppException):
    pass


class SubjectNotArchivedError(AppException):
    pass


class SubjectArchiveBlockedError(AppException):
    pass


class SubjectIsArchivedError(AppException):
    pass


class SubjectIsNotArchivedError(AppException):
    pass


# INTEGRITY ERROR HANDLERS
def handle_subject_code_integrity_error(error: IntegrityError) -> None:
    if "ix_subjects_code" in str(error.orig):
        raise SubjectCodeAlreadyExistsError(HTTP409.SUBJECT_CODE)
