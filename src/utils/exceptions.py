class AppException(Exception):
    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class InvalidAccessTokenError(AppException):
    pass


class AccountInactiveError(AppException):
    pass


class AccessDeniedError(AppException):
    pass


class CannotCreateSystemAdminError(AppException):
    pass


class CannotCreateDirectorError(AppException):
    pass


class MaxNumberOfIdenticalCredentialsError(AppException):
    pass
