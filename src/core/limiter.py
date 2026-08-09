from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.core.config import settings
from src.core.security import decode_access_token


def get_user_identifier(request: Request) -> str:
    auth_header = request.headers.get("Authorization", "")

    if auth_header.startswith("Bearer "):
        token = auth_header[len("Bearer ") :]

        try:
            payload = decode_access_token(token)
            user_id = payload.get("sub")

            if user_id:
                return f"user:{user_id}"

        except Exception:
            pass

    return get_remote_address(request)


def _redis_uri() -> str:
    password_part = f":{settings.REDIS_PASSWORD}@" if settings.REDIS_PASSWORD else ""

    return f"redis://{password_part}{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"


ip_limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=_redis_uri(),
)

user_limiter = Limiter(
    key_func=get_user_identifier,
    storage_uri=_redis_uri(),
)
