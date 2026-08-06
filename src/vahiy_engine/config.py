"""Application configuration loaded from environment variables."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Vahiy Engine"
    app_version: str = "1.0.0"
    environment: str = "development"
    ahit_corpus_path: str = "data/corpus/ahit/bible"
    # Root of a local checkout of the separate ahit-corpus repository. Unset
    # by default: only the bundled KJV sample data (ahit_corpus_path above)
    # is available then. When set, additional translations (YTC, SBLGNT)
    # register automatically if their real subdirectories are present.
    ahit_corpus_root: str | None = None

    # Provider credentials/model names use their SDK-conventional env var names
    # (no VAHIY_ prefix), so validation_alias overrides env_prefix per field.
    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", validation_alias="OPENAI_MODEL")
    gemini_api_key: str | None = Field(default=None, validation_alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", validation_alias="GEMINI_MODEL")

    model_config = SettingsConfigDict(env_file=".env", env_prefix="VAHIY_", extra="ignore")


settings = Settings()
