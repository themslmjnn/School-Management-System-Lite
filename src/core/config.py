import os

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ALGORITHM = "HS256"

_env_file = {"test": ".env.test"}.get(os.getenv("ENVIRONMENT", "development"), ".env")


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"

    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PSSW: str
    DB_NAME: str

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0

    JWT_SECRET_KEY: str

    ACCESS_TOKEN_EXPIRES_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRES_DAYS: int = 7

    INVITE_TOKEN_EXPIRES_HOURS: int = 48
    RESET_PASSWORD_EXPIRES_MINUTES: int = 15
    EMAIL_CHANGE_CODE_EXPIRES_MINUTES: int = 15

    RESEND_API_KEY: str
    MAIL_FROM: str = "onboarding@resend.dev"
    MAIL_FROM_NAME: str = "LFGS | SMS Lite"

    MAILTRAP_HOST: str = "sandbox.smtp.mailtrap.io"
    MAILTRAP_PORT: int = 587
    MAILTRAP_USERNAME: str
    MAILTRAP_PASSWORD: str

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "test"}

        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}, got '{v}'")

        return v

    @field_validator("DB_PORT")
    @classmethod
    def validate_db_port(cls, v: int) -> int:
        if not (1 <= v <= 65535):
            raise ValueError(f"DB_PORT must be between 1 and 65535, got {v}")

        return v

    @field_validator("DB_HOST", "REDIS_HOST")
    @classmethod
    def validate_host_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Host cannot be empty or whitespace")

        return v

    @field_validator("DB_NAME", "DB_USER")
    @classmethod
    def validate_db_identifiers(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Database name and user cannot be empty")

        return v

    @field_validator("REDIS_PORT")
    @classmethod
    def validate_redis_port(cls, v: int) -> int:
        if not (1 <= v <= 65535):
            raise ValueError(f"REDIS_PORT must be between 1 and 65535, got {v}")

        return v

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters")

        return v

    @field_validator("ACCESS_TOKEN_EXPIRES_MINUTES")
    @classmethod
    def validate_access_token_expiry(cls, v: int) -> int:
        if v < 1:
            raise ValueError("ACCESS_TOKEN_EXPIRES_MINUTES must be at least 1")
        if v > 15:
            raise ValueError("ACCESS_TOKEN_EXPIRES_MINUTES should not exceed 15")

        return v

    @field_validator("REFRESH_TOKEN_EXPIRES_DAYS")
    @classmethod
    def validate_refresh_token_expiry(cls, v: int) -> int:
        if v < 1:
            raise ValueError("REFRESH_TOKEN_EXPIRES_DAYS must be at least 1")
        if v > 90:
            raise ValueError("REFRESH_TOKEN_EXPIRES_DAYS should not exceed 90")

        return v

    @property
    def cookie_secure(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def DB_URL(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PSSW}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def APP_URL(self) -> str:
        if self.ENVIRONMENT == "production":
            return "https://sms-lite.com"

        return "http://localhost:8000"

    model_config = SettingsConfigDict(
        env_file=_env_file if os.path.exists(_env_file) else None,
        env_file_encoding="utf-8",
    )


settings = Settings()
