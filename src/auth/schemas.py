from pydantic import BaseModel

from src.utils.enums import UserRole


class CreateAccessToken(BaseModel):
    user_id: int
    role: UserRole
    access_token_version: int
