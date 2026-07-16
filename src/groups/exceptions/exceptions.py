from sqlalchemy.exc import IntegrityError

from src.groups.exceptions.constants import HTTP409
from src.utils.base_exception import AppException


class GroupNotFoundError(AppException):
    pass


class GroupNameYearAlreadyExistsError(AppException):
    pass


class GroupAlreadyArchivedError(AppException):
    pass


class GroupNotArchivedError(AppException):
    pass


class GroupArchiveBlockedError(AppException):
    pass


class GroupCapacityExceededError(AppException):
    pass


class GroupIsNotArchivedError(AppException):
    pass


# INTEGRITY ERROR HANDLERS
def handle_group_name_year_integrity_error(error: IntegrityError) -> None:
    if "uix_group_name_academic_year" in str(error.orig):
        raise GroupNameYearAlreadyExistsError(HTTP409.GROUP_NAME)
