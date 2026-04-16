"""WebSocket router for streaming voice conversations.

The client speaks in raw linear16 16kHz mono PCM. Deepgram Flux groups frames
into turns and emits an EndOfTurn event on natural pauses. Each turn becomes
one ChatService.handle_message call — exactly the same entry point as /chat,
so both endpoints share the compiled graph, checkpointer, and thread IDs.

Wire protocol:
    Client -> Server:
        binary frames: linear16 PCM @ 16kHz mono
        text frame "__end__": session is over
    Server -> Client:
        text frame: {"type": "turn", "transcript", "response", "session_id"}
        binary frame: linear16 PCM @ 16kHz mono TTS of the reply (when
            Deepgram key is set) — chosen over MP3 so clients can play
            the audio directly without an MP3 decoder
        text frame: {"type": "done"} on clean close
        1011 close when Deepgram is unavailable
"""

from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter, Depends, WebSocket
from fastapi.websockets import WebSocketState

from src.agents.deepgram.batch import synthesize_speech
from src.agents.deepgram.client import get_deepgram_client
from src.agents.deepgram.streaming import FluxSession
from src.routers.chat import get_chat_service
from src.schemas.api import ChatRequest
from src.services.chat import ChatService

logger = logging.getLogger(__name__)

router = APIRouter()


def _flux_available() -> bool:
    """Return True when Deepgram is configured and /voice can be served."""
    return get_deepgram_client() is not None


async def _run_turn(
    transcript: str,
    session_id: str | None,
    chat_service: ChatService,
    ws: WebSocket,
) -> str:
    """Run one graph turn and stream the reply back to the client."""
    request = ChatRequest(message=transcript, session_id=session_id)
    reply = await chat_service.handle_message(request)

    payload = {
        "type": "turn",
        "transcript": transcript,
        "response": reply.response,
        "session_id": reply.session_id,
    }
    await ws.send_text(json.dumps(payload))

    audio = await synthesize_speech(reply.response, encoding="linear16", sample_rate=16000)
    if audio:
        await ws.send_bytes(audio)

    return reply.session_id


@router.websocket("/voice")
async def voice_endpoint(
    websocket: WebSocket,
    chat_service: ChatService = Depends(get_chat_service),
) -> None:
    """Stream audio from the client through Deepgram Flux into the graph."""
    await websocket.accept()

    if not _flux_available():
        logger.warning("/voice refused: DEEPGRAM_API_KEY unset")
        await websocket.close(code=1011, reason="Deepgram not configured")
        return

    session = FluxSession()
    try:
        await session.start()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Flux start failed: %s", exc)
        await websocket.close(code=1011, reason="Deepgram Flux unavailable")
        return

    session_id: str | None = None

    async def pump_events() -> None:
        nonlocal session_id
        async for event in session.events():
            if event["type"] != "turn":
                continue
            transcript = event["transcript"]
            try:
                session_id = await _run_turn(transcript, session_id, chat_service, websocket)
            except Exception as exc:  # noqa: BLE001
                logger.warning("turn failed: %s", exc)
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.close(code=1011, reason="turn execution failed")
                return

    events_task = asyncio.create_task(pump_events())

    try:
        while True:
            message = await websocket.receive()
            if message.get("type") == "websocket.disconnect":
                break
            if "bytes" in message and message["bytes"] is not None:
                session.send_audio(message["bytes"])
            elif "text" in message and message["text"] == "__end__":
                break
    finally:
        await session.close()
        await events_task
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.send_text(json.dumps({"type": "done"}))
            await websocket.close()
