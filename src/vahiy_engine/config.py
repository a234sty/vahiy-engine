"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Vahiy Engine"
    app_version: str = "1.0.0"
    environment: str = "development"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="VAHIY_", extra="ignore")


settings = Settings()
