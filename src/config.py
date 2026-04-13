"""Settings for the DEUS Bank customer support system."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    google_api_key: str
    mongodb_url: str | None = None
    mongodb_db_name: str = "deus_bank"

    model_config = {"env_file": ".env"}


def get_settings() -> Settings:
    return Settings()
