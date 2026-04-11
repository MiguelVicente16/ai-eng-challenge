"""Structured output schemas for LLM extraction.

These pydantic models define the shapes we ask the LLM to return
when extracting structured data from natural language conversation.
Designed to handle noisy input from speech-to-text.
"""

from pydantic import BaseModel, Field


class ExtractedIdentity(BaseModel):
    """Identity fields extracted from user's natural language input.

    The LLM extracts whatever identity info the user provides.
    Fields are None when not mentioned. Values are normalized
    (e.g., phone numbers stripped of spaces/formatting).
    """

    name: str | None = Field(None, description="Customer's name as stated")
    phone: str | None = Field(None, description="Phone number, normalized to E.164 format (e.g., +1122334455)")
    iban: str | None = Field(None, description="IBAN, normalized with no spaces")


class ExtractedSecret(BaseModel):
    """Secret question answer extracted from user's response."""

    answer: str | None = Field(None, description="The customer's answer to the secret question")


class UserIntent(BaseModel):
    """Classified intent of the user's message."""

    intent: str = Field(description="One of: 'greeting', 'provide_identity', 'answer_secret', 'ask_question', 'other'")
    summary: str = Field(description="Brief summary of what the user is asking or saying")
