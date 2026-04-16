"""Settings for the DEUS Bank customer support system."""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    google_api_key: str
    google_llm_model: str = "gemini-2.0-flash"
    mongodb_url: str | None = None
    mongodb_db_name: str = "deus_bank"
    deepgram_api_key: str | None = None
    deepgram_stt_model: str = "nova-2-general"
    deepgram_tts_model: str = "aura-2-thalia-en"
    # Where to append post-call summaries when MongoDB is not configured.
    # One JSON object per line, created lazily on first write.
    summaries_jsonl_path: Path = Path("data/call_summaries.jsonl")

    model_config = {"env_file": ".env"}


def get_settings() -> Settings:
    return Settings()
