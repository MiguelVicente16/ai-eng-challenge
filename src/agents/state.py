"""Shared LangGraph state for the customer support agents."""

from typing import TypedDict

from src.agents.flags import Service, Stage, Tier


class AgentState(TypedDict, total=False):
    """State shared across all agent nodes. All fields are optional."""

    # Input/output text (wrapped by stt/tts nodes)
    input_text: str
    output_text: str

    # Raw audio bytes, only populated when the /chat or /voice caller sends audio.
    input_audio: bytes | None
    output_audio: bytes | None

    # Optional TTS output format override (threaded from ChatRequest).
    # When unset, the tts_node uses its default (mp3).
    tts_encoding: str | None
    tts_sample_rate: int | None

    # Current user turn
    user_message: str

    # Stage drives graph routing
    stage: Stage

    # Caller ID (optional, from the API request)
    caller_phone: str | None
    known_name_hint: str | None
    caller_recognized: bool

    # Identity extraction (accumulates across turns)
    extracted_name: str | None
    extracted_phone: str | None
    extracted_iban: str | None
    verified_iban: str | None

    # Secret question challenge
    secret_question: str | None

    # Problem captured BEFORE auth
    user_problem: str | None

    # Retry counter for the current stage (resets on stage advance)
    retry_count: int

    # Classification
    tier: Tier | None
    matched_service: Service | None

    # Clarify loop (Specialist ambiguous-intent branch)
    clarification_question: str | None
    clarify_retry_count: int

    # Response assembly
    response_phrase_key: str | None
    response_variables: dict[str, str]
