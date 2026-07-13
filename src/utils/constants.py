class HTTP400:
    INVITE_TOKEN_USED = "Account already activated or was never invited"
    INVALID_INVITE_TOKEN = "Invalid invite token"
    EXPIRED_INVITE_TOKEN = "Expired invite token"
    DATE_OF_BIRTH = "Date of birth should not be None for Students"
    NO_CHANGES_DETECTED = "No changes detected"


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


class HTTP404:
    USER = "User not found"


class HTTP409:
    USERNAME = "Username already taken"
    DUPLICATE_VALUE = "User with the following credentials already exists"
    DUPLICATE_PHONE_NUMBER = "Phone number already taken"
    DUPLICATE_EMAIL = "Email already taken"
