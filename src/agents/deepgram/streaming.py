"""Deepgram Flux streaming adapter.

Wraps `DeepgramClient.listen.v2.connect(...)` — which is callback-based and
runs its reader loop on a background thread — in an async interface. Consumers
drive it with:

    session = FluxSession()
    await session.start()
    async for event in session.events():
        if event["type"] == "turn":
            ...
    await session.close()

The SDK reader thread pushes events into an asyncio queue via
`loop.call_soon_threadsafe`, so `events()` can `async for` over them.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator

from deepgram.core.events import EventType

from src.agents.deepgram.client import get_deepgram_client

logger = logging.getLogger(__name__)

_SENTINEL_CLOSE = object()


class FluxSession:
    """One Deepgram Flux streaming connection bridged to asyncio."""

    def __init__(self, *, model: str = "flux-general-en", sample_rate: int = 16000) -> None:
        self._model = model
        self._sample_rate = sample_rate
        self._connection = None
        self._connection_ctx = None
        self._queue: asyncio.Queue = asyncio.Queue()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._started = False

    async def start(self) -> None:
        """Open the Flux connection and register event handlers."""
        client = get_deepgram_client()
        if client is None:
            raise RuntimeError("DEEPGRAM_API_KEY is not set — /voice is unavailable")

        self._loop = asyncio.get_running_loop()
        # Aggressive end-of-turn detection: 800ms silence triggers a turn,
        # and the confidence bar is low enough that a single-sentence utterance
        # (like "I need help with my yacht insurance") fires an EOT as soon as
        # the speaker pauses. Conservative defaults (0.7 / 5000ms) were missing
        # turns when users didn't hold a long pause.
        self._connection_ctx = client.listen.v2.connect(
            model=self._model,
            encoding="linear16",
            sample_rate=self._sample_rate,
            eot_threshold=0.3,
            eot_timeout_ms=800,
        )
        self._connection = self._connection_ctx.__enter__()

        def _on_message(result) -> None:
            event = getattr(result, "event", None)
            transcript = getattr(result, "transcript", None)
            if event == "EndOfTurn" and transcript:
                self._emit({"type": "turn", "transcript": transcript})
            elif transcript:
                self._emit({"type": "interim", "transcript": transcript})

        def _on_close(_: object) -> None:
            self._emit(_SENTINEL_CLOSE)

        self._connection.on(EventType.MESSAGE, _on_message)
        self._connection.on(EventType.CLOSE, _on_close)
        self._started = True

    def send_audio(self, chunk: bytes) -> None:
        """Forward an audio frame to Deepgram. Call from the async side."""
        if self._connection is None:
            raise RuntimeError("FluxSession.start() must be called before send_audio")
        self._connection.send_media(chunk)

    async def events(self) -> AsyncIterator[dict]:
        """Yield transcription events until the connection closes."""
        while True:
            event = await self._queue.get()
            if event is _SENTINEL_CLOSE:
                return
            yield event

    async def close(self) -> None:
        """Close the Deepgram connection."""
        if self._connection is None:
            return
        try:
            self._connection.send_close_stream()
        except Exception as exc:  # noqa: BLE001
            logger.warning("FluxSession send_close_stream failed: %s", exc)
        finally:
            if self._connection_ctx is not None:
                try:
                    self._connection_ctx.__exit__(None, None, None)
                except Exception:  # noqa: BLE001
                    pass
        self._emit(_SENTINEL_CLOSE)
        self._started = False

    def _emit(self, event: object) -> None:
        """Push an event into the queue from any thread."""
        if self._loop is None:
            return
        self._loop.call_soon_threadsafe(self._queue.put_nowait, event)
