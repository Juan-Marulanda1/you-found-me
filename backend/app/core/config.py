from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "You Found Me API"
    APP_VERSION: str = "1.0.0"

    DEBUG: bool = False

    DATABASE_URL: str

    API_PREFIX: str = "/api/v1"

    PROJECT_DESCRIPTION: str = "Backend API for You Found Me."

    ALLOWED_ORIGINS: list[str] = Field(default_factory=list)

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
