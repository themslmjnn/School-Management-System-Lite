from pydantic import BaseModel, EmailStr, field_validator

from src.utils.enums import UserRole
from src.utils.validators import validate_password


class CreateAccessToken(BaseModel):
    user_id: int
    role: UserRole
    access_token_version: int

class CreateRefreshToken(BaseModel):
    user_id: int

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ActivateAccountWithToken(BaseModel):
    email: EmailStr
    invite_token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        return validate_password(v)