"""Settings for the DEUS Bank customer support system."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    google_api_key: str
    google_llm_model: str = "gemini-2.0-flash"
    mongodb_url: str | None = None
    mongodb_db_name: str = "deus_bank"
    deepgram_api_key: str | None = None
    deepgram_stt_model: str = "nova-2-general"
    deepgram_tts_model: str = "aura-2-thalia-en"

    model_config = {"env_file": ".env"}


def get_settings() -> Settings:
    return Settings()
