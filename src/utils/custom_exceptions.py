from sqlalchemy.exc import IntegrityError

from utils.exception_constants import HTTP409

class AppException(Exception):
    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class InvalidAccessTokenError(AppException):
    pass


class ExpiredAccessTokenError(AppException):
    pass


class InvalidRefreshTokenError(AppException):
    pass


class ExpiredRefreshTokenError(AppException):
    pass


class AccountInactiveError(AppException):
    pass


class AccessDeniedError(AppException):
    pass

class CannotCreateSystemAdminError(AppException):
    pass

class UsernameAlreadyTakenError(AppException):
    pass

class EmailAlreadyTakenError(AppException):
    pass

class PhonenumberAlreadyTakenError(AppException):
    pass

def handle_user_integrity_error(error: IntegrityError) -> None:
    error_str = str(error.orig)

    if "users_username_key" in error_str:
        raise UsernameAlreadyTakenError(HTTP409.USERNAME)

    if "users_email_key" in error_str:
        raise EmailAlreadyTakenError(HTTP409.EMAIL)

    if "users_phone_number_key" in error_str:
        raise PhonenumberAlreadyTakenError(HTTP409.PHONE_NUMBER)

