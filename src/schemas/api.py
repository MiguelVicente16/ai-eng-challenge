"""Request and response schemas for the chat API."""

from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Incoming chat message from a user."""

    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    """Outgoing chat response to a user."""

    response: str
    session_id: str
