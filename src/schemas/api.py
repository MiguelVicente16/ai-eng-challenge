"""Request and response schemas for the chat API."""

from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Incoming chat message from a user.

    Either `message` (text) or `audio_base64` (base64-encoded audio bytes,
    any format Deepgram supports) may be provided. When both are given,
    audio wins once it transcribes successfully.

    `audio_encoding` / `audio_sample_rate` let the caller ask for a
    specific TTS output format. Default is mp3 (good for JSON-over-HTTP
    transport). The PTT call simulator uses linear16@16000 so it can
    play the bytes directly with no client-side decoder or re-synthesis.
    """

    message: str = ""
    session_id: str | None = None
    caller_phone: str | None = None
    audio_base64: str | None = None
    audio_encoding: str = "mp3"
    audio_sample_rate: int | None = None


class ChatResponse(BaseModel):
    """Outgoing chat response to a user."""

    response: str
    session_id: str
    audio_base64: str | None = None
    transcript: str | None = None
