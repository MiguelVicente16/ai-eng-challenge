"""LLM client factory for Google AI Studio."""

from langchain_google_genai import ChatGoogleGenerativeAI

from src.config import get_settings


def get_llm(temperature: float = 0.3) -> ChatGoogleGenerativeAI:
    """Create an LLM instance via Google AI Studio.

    Model is configurable via `GOOGLE_LLM_MODEL` env var. Default is
    `gemini-2.0-flash` because it's ~3-5x faster than `gemma-4-31b-it`
    for structured-output classification, which dominates tail latency
    on LLM-heavy turns. Set `GOOGLE_LLM_MODEL=gemma-4-31b-it` to revert.
    """
    settings = get_settings()
    return ChatGoogleGenerativeAI(
        model="gemma-4-31b-it",
        google_api_key=settings.google_api_key,
        temperature=temperature,
    )
