import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

from fastapi.concurrency import run_in_threadpool
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext

from src.auth.schemas import CreateAccessToken, CreateRefreshToken
from src.core.config import ALGORITHM, settings
from src.utils.constants import HTTP401

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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


def create_refresh_token(payload: CreateRefreshToken) -> tuple[str, str]:
    raw_refresh_token = jwt.encode(
        {
            "sub": str(payload.user_id),
            "type": "refresh",
            "jti": secrets.token_urlsafe(16),
            "exp": datetime.now(UTC)
            + timedelta(days=settings.REFRESH_TOKEN_EXPIRES_DAYS),
        },
        settings.JWT_SECRET_KEY,
        algorithm=ALGORITHM,
    )

    hashed_refresh_token = hashlib.sha256(raw_refresh_token.encode()).hexdigest()

    return raw_refresh_token, hashed_refresh_token


def decode_refresh_token(refresh_token: str) -> dict:
    try:
        payload = jwt.decode(
            refresh_token,
            settings.JWT_SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        if payload.get("type") != "refresh":
            raise ValueError(HTTP401.INVALID_TOKEN_TYPE)

        return payload
    except ExpiredSignatureError as exc:
        raise ValueError(HTTP401.EXPIRED_ACCESS_TOKEN) from exc
    except JWTError as exc:
        raise ValueError(HTTP401.INVALID_REFRESH_TOKEN) from exc


def verify_refresh_token(raw_refresh_token: str, hashed_refresh_token: str) -> bool:
    return hmac.compare_digest(
        hashlib.sha256(raw_refresh_token.encode()).hexdigest(),
        hashed_refresh_token,
    )


def generate_invite_token() -> tuple[str, str]:
    raw_invite_token = secrets.token_urlsafe(32)
    hashed_invite_token = hashlib.sha256(raw_invite_token.encode()).hexdigest()

    return raw_invite_token, hashed_invite_token


def verify_invite_token(raw_invite_token: str, hashed_invite_token: str) -> bool:
    return hmac.compare_digest(
        hashlib.sha256(raw_invite_token.encode()).hexdigest(),
        hashed_invite_token,
    )


async def hash_password(password: str) -> str:
    return await run_in_threadpool(bcrypt_context.hash, password)


async def verify_password(plain_password: str, hashed_password: str) -> bool:
    return await run_in_threadpool(
        bcrypt_context.verify, plain_password, hashed_password
    )


def generate_reset_password_token() -> tuple[str, str]:
    raw_reset_token = secrets.token_urlsafe(32)
    hashed_reset_token = hashlib.sha256(raw_reset_token.encode()).hexdigest()

    return raw_reset_token, hashed_reset_token


def verify_reset_password_token(raw_reset_token: str, hashed_reset_token: str) -> bool:
    return hmac.compare_digest(
        hashlib.sha256(raw_reset_token.encode()).hexdigest(),
        hashed_reset_token,
    )
