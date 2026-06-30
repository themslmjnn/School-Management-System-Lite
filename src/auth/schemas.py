from pydantic import BaseModel, Field, field_validator

from src.utils.enums import UserRole
from src.utils.validators import validate_password, parse_and_validate_mobile_number


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
    username: str
    invite_token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        return validate_password(v)


class ResetPassword(BaseModel):
    username: str
    reset_token: str
    new_password: str


class ForgotPasswordPublicRequest(BaseModel):
    username: str = Field(min_length=6, max_length=20)
    phone_number: str

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        return parse_and_validate_mobile_number(v)
