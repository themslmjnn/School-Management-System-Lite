from sqlalchemy.exc import IntegrityError


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


def raise_unhandled_integrity_error(error: IntegrityError) -> None:
    raise error
