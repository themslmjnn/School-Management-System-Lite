import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

from jose import ExpiredSignatureError, JWTError, jwt

from src.auth.schemas import CreateAccessToken
from src.core.config import ALGORITHM, settings
from src.utils.constants import HTTP401


def create_access_token(payload: CreateAccessToken) -> str:
    payload = {
        "sub": str(payload.user_id),
        "role": payload.role,
        "version": payload.access_token_version,
        "type": "access",
        "exp": datetime.now(UTC)
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
    except ExpiredSignatureError as exc:
        raise ValueError(HTTP401.EXPIRED_ACCESS_TOKEN) from exc
    except JWTError as exc:
        raise ValueError(HTTP401.INVALID_ACCESS_TOKEN) from exc


def generate_invite_token() -> tuple[str, str]:
    raw_invite_token = secrets.token_urlsafe(32)
    hashed_invite_token = hashlib.sha256(raw_invite_token.encode()).hexdigest()

    return raw_invite_token, hashed_invite_token


def verify_invite_token(raw_invite_token: str, hashed_invite_token: str) -> bool:
    return hmac.compare_digest(
        hashlib.sha256(raw_invite_token.encode()).hexdigest(),
        hashed_invite_token,
    )
