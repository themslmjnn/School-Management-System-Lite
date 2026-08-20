from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    field_validator,
)

from src.utils import validators as validators
from src.utils.enums import UserStatus


class UserResponseBase(BaseModel):
    firstname: str
    lastname: str
    middlename: str | None


class UpdateUserCredentials(BaseModel):
    username: str | None = Field(min_length=6, max_length=20, default=None)
    email: str | None = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str | None) -> str | None:
        if v is None:
            return None

        return validators.validate_username(v)

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(cls, v: EmailStr | None) -> str | None:
        if v is None:
            return None

        return validators.validate_email(v)


class SearchUserBase(BaseModel):
    firstname: str | None = Field(default=None, min_length=3, max_length=50)
    lastname: str | None = Field(default=None, min_length=3, max_length=50)
    middlename: str | None = Field(default=None, min_length=3, max_length=50)
    status: UserStatus | None = None
