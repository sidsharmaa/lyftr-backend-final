import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    """
    Application configuration using Pydantic.
    Validates environment variables on initialization.
    """
    webhook_secret: str = Field(..., min_length=1)
    database_url: str = "sqlite:////data/app.db"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

try:
    settings = Settings()
except Exception as e:
    print(f"CRITICAL: Configuration validation failed. {e}")
    raise