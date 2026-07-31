from sqlalchemy.exc import IntegrityError


class AppException(Exception):
    status_code: int = 500

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


# AUTHENTICATION
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


# AUTHORIZATION
class AccessDeniedError(AppException):
    status_code = 403


# NON-AUTH TOKENS
class InvalidInviteTokenError(AppException):
    status_code = 400


class ExpiredInviteTokenError(AppException):
    status_code = 400


class NoChangesDetectedError(AppException):
    status_code = 409


class ExpiredResetPasswordTokenError(AppException):
    status_code = 400


class InvalidResetPasswordTokenError(AppException):
    status_code = 400


def raise_unhandled_integrity_error(error: IntegrityError) -> None:
    raise error
