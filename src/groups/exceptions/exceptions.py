from sqlalchemy.exc import IntegrityError

from src.groups.exceptions.constants import HTTP409
from src.utils.base_exception import AppException


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


# INTEGRITY ERROR HANDLERS
def handle_group_name_year_integrity_error(error: IntegrityError) -> None:
    if "uix_group_name_academic_year" in str(error.orig):
        raise GroupNameYearAlreadyExistsError(HTTP409.GROUP_NAME)
