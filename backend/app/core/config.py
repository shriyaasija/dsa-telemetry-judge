from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "DSA Telemetry Judge"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(
        env_file="../.env",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()