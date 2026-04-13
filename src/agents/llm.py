"""LLM client factory for Google AI Studio."""

from langchain_google_genai import ChatGoogleGenerativeAI

from src.config import get_settings


def get_llm(temperature: float = 0.3) -> ChatGoogleGenerativeAI:
    """Create a Gemma LLM instance via Google AI Studio."""
    settings = get_settings()
    return ChatGoogleGenerativeAI(
        model="gemma-4-31b-it",
        google_api_key=settings.google_api_key,
        temperature=temperature,
    )
