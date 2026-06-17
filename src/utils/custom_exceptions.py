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
