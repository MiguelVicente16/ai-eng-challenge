"""LangGraph ↔ Pipecat bridge.

A minimal FrameProcessor that sits where an LLM service would in a standard
Pipecat pipeline. It consumes finalized user `TranscriptionFrame`s from the
STT stage, runs them through `ChatService.handle_message` (the same entry
point `/chat` uses), and emits the response as the LLM-frame trio expected
downstream:

    LLMFullResponseStartFrame → LLMTextFrame(response) → LLMFullResponseEndFrame

That sequence is what `DeepgramTTSService` synthesises and what the RTVI
observer translates into `bot-llm-text` / `bot-tts-*` messages for the
client. The graph's MongoDB / InMemory checkpointer remains the source of
truth for conversation memory — we thread `session_id` (== LangGraph
`thread_id`) through each turn so the compiled graph reloads the correct
state.

The bridge does not handle the initial opener; the pipeline builder fires
that once on `on_client_ready` (see `src/voice/pipeline.py`).
"""

from __future__ import annotations

import logging

from pipecat.frames.frames import (
    Frame,
    InterimTranscriptionFrame,
    LLMFullResponseEndFrame,
    LLMFullResponseStartFrame,
    LLMTextFrame,
    TranscriptionFrame,
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

from src.schemas.api import ChatRequest
from src.services.chat import ChatService

logger = logging.getLogger(__name__)


class LangGraphBridge(FrameProcessor):
    """Run each finalized user turn through the LangGraph agent."""

    def __init__(self, chat_service: ChatService) -> None:
        super().__init__()
        self._chat_service = chat_service
        self._session_id: str | None = None

    @property
    def session_id(self) -> str | None:
        """Current LangGraph thread_id, set after the first graph response."""
        return self._session_id

    @session_id.setter
    def session_id(self, value: str | None) -> None:
        self._session_id = value

    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        await super().process_frame(frame, direction)

        # Drop interim results — running the graph on every partial would
        # dogpile the LLM. The STT service emits a final TranscriptionFrame
        # once the turn settles; that's our trigger.
        if isinstance(frame, InterimTranscriptionFrame):
            await self.push_frame(frame, direction)
            return

        if isinstance(frame, TranscriptionFrame) and direction == FrameDirection.DOWNSTREAM:
            text = (frame.text or "").strip()
            if not text:
                # Empty finals happen when the VAD closes a silent window.
                # Don't bother the graph with them.
                return
            await self._run_turn(text)
            return

        await self.push_frame(frame, direction)

    async def _run_turn(self, text: str) -> None:
        logger.info("bridge turn (session=%s): %r", (self._session_id or "?")[:8], text[:60])
        request = ChatRequest(message=text, session_id=self._session_id)
        response = await self._chat_service.handle_message(request)
        self._session_id = response.session_id
        await self.emit_assistant_text(response.response)

    async def emit_assistant_text(self, text: str) -> None:
        """Emit an assistant reply as the standard LLM frame trio.

        Kept public so the pipeline builder can fire the opener without
        routing an empty frame through STT.
        """
        if not text:
            return
        await self.push_frame(LLMFullResponseStartFrame())
        await self.push_frame(LLMTextFrame(text=text))
        await self.push_frame(LLMFullResponseEndFrame())
