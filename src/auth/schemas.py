from pydantic import BaseModel

from src.utils.enums import UserRole


class CreateAccessToken(BaseModel):
    user_id: int
    role: UserRole
    access_token_version: int

class CreateRefreshToken(BaseModel):
    user_id: int

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
