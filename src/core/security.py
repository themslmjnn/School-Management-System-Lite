from datetime import datetime, timedelta, timezone

from jose import ExpiredSignatureError, JWTError, jwt

from src.core.config import ALGORITHM, settings
from src.schemas.auth import CreateAccessTokenRequest
from utils.custom_exceptions import ExpiredAccessTokenError, InvalidAccessTokenError
from utils.exception_constants import HTTP401


def create_access_token(payload: CreateAccessTokenRequest) -> str:
    payload = {
        "sub": str(payload.user_id),
        "role": payload.role,
        "version": payload.access_token_version,
        "type": "access",
        "exp": datetime.now(timezone.utc)
        + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRES_MINUTES),
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=ALGORITHM,
    )


def decode_access_token(access_token: str) -> dict:
    try:
        payload = jwt.decode(
            access_token,
            settings.JWT_SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        if payload.get("type") != "access":
            raise ValueError(HTTP401.INVALID_TOKEN_TYPE)

        return payload
    except ExpiredSignatureError:
        raise ExpiredAccessTokenError(HTTP401.EXPIRED_ACCESS_TOKEN)
    except JWTError:
        raise InvalidAccessTokenError(HTTP401.INVALID_ACCESS_TOKEN)
