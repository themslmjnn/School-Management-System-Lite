class HTTP401:
    INVALID_CREDENTIALS = "Invalid credentials"
    ACCOUNT_NOT_ACTIVATED = "Account has not been activated yet"
    INVALID_REFRESH_TOKEN = "Invalid refresh token"
    EXPIRED_REFRESH_TOKEN = "Expired refresh token"
    INVALID_ACCESS_TOKEN = "Invalid access token"
    EXPIRED_ACCESS_TOKEN = "Expired access token"
    INVALID_TOKEN_TYPE = "Invalid token type"


class HTTP403:
    ACCESS_DENIED = "Access denied"
    ACCOUNT_DEACTIVATED = "Your account has been deactivated"

class HTTP409:
    USERNAME = "Username already taken"
    EMAIL = "Email already taken"
    PHONE_NUMBER = "Phone number already taken"