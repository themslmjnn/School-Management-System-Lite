from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    field_validator,
)

from src.utils import validators as validators


class UpdateUserCredentials(BaseModel):
    username: str | None = Field(min_length=6, max_length=20, default=None)
    email: EmailStr | None = None

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

        return v.strip().lower()
