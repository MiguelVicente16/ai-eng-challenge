"""WebSocket router for streaming voice conversations.

The heavy lifting lives in `src.voice.pipeline.run_voice_pipeline`, which
owns the Pipecat pipeline (audio framing, VAD, Deepgram STT/TTS, and the
LangGraph bridge). This module is just the FastAPI entry point:

    browser  ── WS /voice ──►  FastAPI (this file)
                                ├── Deepgram key gate (1011 if unset)
                                └── run_voice_pipeline(...)  ← Pipecat lives here

Wire protocol on the WS is RTVI / Pipecat protobuf — clients connect with
`@pipecat-ai/client-js` + `@pipecat-ai/websocket-transport`.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, WebSocket
from fastapi.websockets import WebSocketState

from src.agents.deepgram.client import get_deepgram_client
from src.routers.chat import get_chat_service
from src.services.chat import ChatService
from src.voice.pipeline import run_voice_pipeline

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/voice")
async def voice_endpoint(
    websocket: WebSocket,
    chat_service: ChatService = Depends(get_chat_service),
) -> None:
    """Serve one voice session via the Pipecat pipeline."""
    await websocket.accept()
    logger.info("/voice ws accepted")

    if get_deepgram_client() is None:
        logger.warning("/voice refused: DEEPGRAM_API_KEY unset")
        await websocket.close(code=1011, reason="Deepgram not configured")
        return

    try:
        await run_voice_pipeline(websocket, chat_service)
    except Exception as exc:  # noqa: BLE001 — keep the socket handler robust
        logger.warning("/voice pipeline failed: %s", exc)
        if websocket.client_state == WebSocketState.CONNECTED:
            try:
                await websocket.close(code=1011, reason="pipeline error")
            except Exception as close_exc:  # noqa: BLE001
                logger.debug("/voice close after failure raced: %s", close_exc)
