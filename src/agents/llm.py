"""LLM client factory for Google AI Studio (Gemma 4)."""

from langchain_google_genai import ChatGoogleGenerativeAI

from src.config import get_settings


def get_llm(temperature: float = 0.3) -> ChatGoogleGenerativeAI:
    """Create a Gemma 4 LLM instance via Google AI Studio."""
    settings = get_settings()
    return ChatGoogleGenerativeAI(
        model="gemma-3-27b-it",
        google_api_key=settings.google_api_key,
        temperature=temperature,
    )
