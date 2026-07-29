from src.utils.base_exception import AppException


class PendingEmailNotFoundError(AppException):
    status_code = 404
