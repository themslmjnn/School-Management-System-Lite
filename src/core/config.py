from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ALGORITHM = "HS256"

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"

    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PSSW: str
    DB_NAME: str

    JWT_SECRET_KEY: str

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
        return v

    @field_validator("DB_PORT")
    @classmethod
    def validate_db_port(cls, v: int) -> int:
        if not (1 <= v <= 65535):
            raise ValueError(f"DB_PORT must be between 1 and 65535, got {v}")
        return v
    
    @field_validator("DB_HOST")
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

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "production", "test"}
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}, got '{v}'")

    @property
    def DB_URL(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PSSW}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def cookie_secure(self) -> bool:
        return self.ENVIRONMENT == "production"
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()