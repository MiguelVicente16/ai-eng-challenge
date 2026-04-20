"""Build and run the Pipecat pipeline for one `/voice` WebSocket session.

The shape:

    transport.input() →
      DeepgramSTTService →
        LangGraphBridge →
          DeepgramTTSService →
            transport.output()

Silero VAD on the transport input handles turn segmentation; Deepgram STT
emits finalized `TranscriptionFrame`s which the bridge consumes; the bridge
emits `LLMTextFrame`s which the TTS service synthesises and which the
RTVIObserver mirrors to the client as `bot-llm-text`.

The "opener" (bank greeting played before the user says anything) runs
once on `on_client_ready` — we invoke `ChatService.handle_message("")`
directly, store the returned `session_id` on the bridge, and ask the
bridge to emit the opener text so TTS picks it up.
"""

from __future__ import annotations

import logging

from fastapi import WebSocket
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.serializers.protobuf import ProtobufFrameSerializer
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.deepgram.tts import DeepgramTTSService
from pipecat.transports.websocket.fastapi import (
    FastAPIWebsocketParams,
    FastAPIWebsocketTransport,
)

from src.config import get_settings
from src.schemas.api import ChatRequest
from src.services.chat import ChatService
from src.voice.langgraph_bridge import LangGraphBridge

logger = logging.getLogger(__name__)

_AUDIO_SAMPLE_RATE = 16000


async def run_voice_pipeline(websocket: WebSocket, chat_service: ChatService) -> None:
    """Wire a Pipecat pipeline to this WebSocket and run it to completion."""
    settings = get_settings()
    if not settings.deepgram_api_key:
        # Caller should have already rejected the connection; belt-and-braces.
        await websocket.close(code=1011, reason="Deepgram not configured")
        return

    transport = FastAPIWebsocketTransport(
        websocket=websocket,
        params=FastAPIWebsocketParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            add_wav_header=False,
            serializer=ProtobufFrameSerializer(),
            # Callers dictate phone / account numbers with natural pauses
            # between digit groups. Silero's default 0.2 s stop window
            # closes the turn on the first pause and hands half-numbers to
            # the LLM. 0.8 s is long enough to ride through "5-5-6-6 …
            # 7-7-8-8" without feeling sluggish on normal conversation.
            vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.8)),
        ),
    )

    stt = DeepgramSTTService(
        api_key=settings.deepgram_api_key,
        sample_rate=_AUDIO_SAMPLE_RATE,
    )
    tts = DeepgramTTSService(
        api_key=settings.deepgram_api_key,
        sample_rate=_AUDIO_SAMPLE_RATE,
        encoding="linear16",
    )
    bridge = LangGraphBridge(chat_service)

    pipeline = Pipeline(
        [
            transport.input(),
            stt,
            bridge,
            tts,
            transport.output(),
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            allow_interruptions=True,
            enable_metrics=False,
        ),
    )

    @task.rtvi.event_handler("on_client_ready")
    async def _on_client_ready(_rtvi) -> None:  # noqa: ANN001 — Pipecat event handler
        """Fire the bank opener once the client finishes its RTVI handshake."""
        try:
            response = await chat_service.handle_message(ChatRequest(message=""))
            bridge.session_id = response.session_id
            await bridge.emit_assistant_text(response.response)
        except Exception as exc:  # noqa: BLE001 — non-fatal; user can still talk
            logger.warning("voice opener failed: %s", exc)

    @transport.event_handler("on_client_disconnected")
    async def _on_client_disconnected(_transport, _client) -> None:  # noqa: ANN001
        logger.info("/voice client disconnected — cancelling pipeline")
        await task.cancel()

    runner = PipelineRunner(handle_sigint=False)
    await runner.run(task)
