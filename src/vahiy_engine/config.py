"""Application configuration loaded from environment variables."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Vahiy Engine"
    app_version: str = "1.0.0"
    environment: str = "development"
    ahit_corpus_path: str = "data/corpus/ahit/bible"
    # Root of a local checkout of the separate ahit-corpus repository —
    # unprefixed (no VAHIY_) and matching scripts/setup_corpus.sh's own
    # default target, so running that script with no configuration at all is
    # enough for the app to pick it up automatically. If nothing has cloned
    # the corpus there, only the bundled KJV sample data is available (no
    # error); if it's present, additional translations (YTC, SBLGNT)
    # register automatically.
    ahit_corpus_root: str = Field(
        default="external/ahit-corpus", validation_alias="AHIT_CORPUS_ROOT"
    )

    # Provider credentials/model names use their SDK-conventional env var names
    # (no VAHIY_ prefix), so validation_alias overrides env_prefix per field.
    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", validation_alias="OPENAI_MODEL")
    gemini_api_key: str | None = Field(default=None, validation_alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", validation_alias="GEMINI_MODEL")

    # Cost/quality tiers. A question the analyzer marks SIMPLE (a verse
    # lookup) does not need the model a DEEP comparative question needs, and
    # billing every question at the deep tier is the single largest avoidable
    # cost in this pipeline. Left unset, both fall back to the provider's
    # default model above, so tiering is opt-in per deployment rather than a
    # behavior change forced on existing ones.
    openai_model_fast: str | None = Field(default=None, validation_alias="OPENAI_MODEL_FAST")
    openai_model_deep: str | None = Field(default=None, validation_alias="OPENAI_MODEL_DEEP")
    gemini_model_fast: str | None = Field(default=None, validation_alias="GEMINI_MODEL_FAST")
    gemini_model_deep: str | None = Field(default=None, validation_alias="GEMINI_MODEL_DEEP")

    # How long a single LLM provider call may run before failing with a clean
    # LLMProviderError (-> 502) instead of hanging until an external proxy
    # kills the connection with an opaque 504.
    llm_request_timeout_seconds: float = 30.0

    model_config = SettingsConfigDict(env_file=".env", env_prefix="VAHIY_", extra="ignore")


settings = Settings()
