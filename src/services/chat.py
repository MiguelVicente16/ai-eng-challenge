"""Chat service — invokes the LangGraph agent for each incoming message."""

import logging
import time
import uuid

from fastapi import HTTPException

from src.agents.deepgram.batch import decode_base64_audio, encode_base64_audio
from src.agents.graph import build_graph
from src.data import CUSTOMERS
from src.logging_config import mask, trim
from src.schemas.api import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)


def _lookup_customer_by_phone(phone: str) -> tuple[bool, str | None]:
    """Return (recognized, known_name) for a caller phone lookup."""
    for customer in CUSTOMERS:
        if customer.phone == phone:
            return True, customer.name
    return False, None


class ChatService:
    """Orchestrates the multi-agent conversation via the LangGraph."""

    def __init__(self) -> None:
        self._graph = build_graph()

    async def handle_message(self, request: ChatRequest) -> ChatResponse:
        """Run the graph for this message under the session's thread_id."""
        session_id = request.session_id or str(uuid.uuid4())
        config = {"configurable": {"thread_id": session_id}}

        audio_bytes: bytes | None = None
        if request.audio_base64:
            try:
                audio_bytes = decode_base64_audio(request.audio_base64)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc

        start = time.perf_counter()
        snapshot = await self._graph.aget_state(config)

        if snapshot.values:
            inputs: dict = {"input_text": request.message}
            if audio_bytes is not None:
                inputs["input_audio"] = audio_bytes
            if request.audio_encoding:
                inputs["tts_encoding"] = request.audio_encoding
            if request.audio_sample_rate is not None:
                inputs["tts_sample_rate"] = request.audio_sample_rate
            logger.info("turn on %s: %s", session_id[:8], trim(request.message, 60))
        else:
            inputs = {
                "input_text": request.message,
                "stage": "new_session",
            }
            if audio_bytes is not None:
                inputs["input_audio"] = audio_bytes
            if request.audio_encoding:
                inputs["tts_encoding"] = request.audio_encoding
            if request.audio_sample_rate is not None:
                inputs["tts_sample_rate"] = request.audio_sample_rate
            if request.caller_phone:
                recognized, known_name = _lookup_customer_by_phone(request.caller_phone)
                inputs["caller_phone"] = request.caller_phone
                inputs["caller_recognized"] = recognized
                if recognized:
                    inputs["extracted_phone"] = request.caller_phone
                    inputs["known_name_hint"] = known_name
                caller_desc = f"caller ID {mask(request.caller_phone)}"
            else:
                caller_desc = "no caller ID"
            logger.info("new session %s - %s", session_id[:8], caller_desc)

        result = await self._graph.ainvoke(inputs, config=config)

        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info("-> reply in %dms", round(elapsed_ms))

        output_audio = result.get("output_audio") or None
        audio_b64 = encode_base64_audio(output_audio) if output_audio else None
        transcript = result.get("user_message") if audio_bytes is not None else None

        return ChatResponse(
            response=result.get("output_text", ""),
            session_id=session_id,
            audio_base64=audio_b64,
            transcript=transcript,
        )
