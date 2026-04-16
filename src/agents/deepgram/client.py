"""Deepgram client factory — cached, lazy, returns None when the key is unset."""

from functools import lru_cache

from deepgram import DeepgramClient

from src.config import get_settings


@lru_cache(maxsize=1)
def get_deepgram_client() -> DeepgramClient | None:
    """Return a shared Deepgram client, or None if DEEPGRAM_API_KEY is unset.

    Caller is responsible for handling the None case (falling back to
    pass-through or rejecting the request).
    """
    settings = get_settings()
    if not settings.deepgram_api_key:
        return None
    return DeepgramClient(api_key=settings.deepgram_api_key)
