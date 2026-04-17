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
import threading
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
        self._listener_thread: threading.Thread | None = None
        self._audio_chunks_sent = 0
        self._audio_bytes_sent = 0

    async def start(self) -> None:
        """Open the Flux connection and register event handlers.

        The Deepgram SDK is synchronous — opening the websocket to Deepgram
        is a blocking network call. Running it inline on the event loop would
        freeze every other coroutine for the duration of the handshake,
        including uvicorn flushing our own /voice 101 Switching Protocols
        response to the browser. That manifests as the client sitting on
        "Connecting…" forever even though the backend already logged
        `accepted`. Pushing the blocking calls to a worker thread keeps the
        event loop responsive while Deepgram's TLS+WS handshake runs.
        """
        client = get_deepgram_client()
        if client is None:
            raise RuntimeError("DEEPGRAM_API_KEY is not set — /voice is unavailable")

        self._loop = asyncio.get_running_loop()

        def _open_connection():
            # Responsive end-of-turn detection while staying inside
            # Deepgram's accepted parameter range: 0.5 confidence + 1000ms
            # silence is the current minimum Flux accepts (lower values
            # return HTTP 400 at the handshake). Conservative defaults
            # (0.7 / 5000ms) missed turns when users paused briefly.
            ctx = client.listen.v2.connect(
                model=self._model,
                encoding="linear16",
                sample_rate=self._sample_rate,
                eot_threshold=0.5,
                eot_timeout_ms=1000,
            )
            conn = ctx.__enter__()
            return ctx, conn

        self._connection_ctx, self._connection = await asyncio.to_thread(_open_connection)

        def _on_message(result) -> None:
            msg_type = getattr(result, "type", None)
            event = getattr(result, "event", None)
            transcript = getattr(result, "transcript", None)
            logger.info(
                "flux <- type=%s event=%s transcript=%r",
                msg_type,
                event,
                transcript[:60] if transcript else transcript,
            )
            if event == "EndOfTurn" and transcript:
                self._emit({"type": "turn", "transcript": transcript})
            elif transcript:
                self._emit({"type": "interim", "transcript": transcript})

        def _on_error(exc: object) -> None:
            logger.warning("flux error from SDK: %r", exc)

        def _on_close(_: object) -> None:
            logger.info("flux ws closed by Deepgram")
            self._emit(_SENTINEL_CLOSE)

        self._connection.on(EventType.MESSAGE, _on_message)
        self._connection.on(EventType.ERROR, _on_error)
        self._connection.on(EventType.CLOSE, _on_close)
        # `start_listening()` is a synchronous infinite read loop on the
        # Deepgram websocket — the SDK does not spawn its own thread for the
        # sync client. If we awaited it (or even called it inline), `start()`
        # would never return and no audio would ever reach Deepgram. Run it
        # on a daemon thread instead so handlers fire and `start()` returns
        # immediately.
        self._listener_thread = threading.Thread(
            target=self._connection.start_listening,
            name="deepgram-flux-listener",
            daemon=True,
        )
        self._listener_thread.start()
        self._started = True

    def send_audio(self, chunk: bytes) -> None:
        """Forward an audio frame to Deepgram. Call from the async side."""
        if self._connection is None:
            raise RuntimeError("FluxSession.start() must be called before send_audio")
        try:
            self._connection.send_media(chunk)
        except Exception as exc:  # noqa: BLE001
            logger.warning("flux send_media failed after %d chunks: %r", self._audio_chunks_sent, exc)
            raise
        self._audio_chunks_sent += 1
        self._audio_bytes_sent += len(chunk)
        # Log only at milestones so we don't drown the console: first chunk,
        # then every ~5s of audio at 16kHz/16-bit mono (32 KB/s).
        if self._audio_chunks_sent == 1:
            logger.info("flux -> first audio chunk sent (%d bytes)", len(chunk))
        elif self._audio_bytes_sent % (32 * 1024 * 5) < len(chunk):
            logger.info(
                "flux -> %d chunks / %d KB sent so far", self._audio_chunks_sent, self._audio_bytes_sent // 1024
            )

    async def events(self) -> AsyncIterator[dict]:
        """Yield transcription events until the connection closes."""
        while True:
            event = await self._queue.get()
            if event is _SENTINEL_CLOSE:
                return
            yield event

    async def close(self) -> None:
        """Close the Deepgram connection.

        The SDK calls (`send_close_stream`, context-manager exit) are
        synchronous and join the SDK's reader thread. Running them inline on
        the event loop would freeze every other coroutine — including signal
        handlers — for as long as the SDK takes to tear down. Pushing them to
        a worker thread keeps the loop responsive; a hard timeout protects
        against an SDK hang locking up the websocket handler permanently.
        """
        if self._connection is None:
            return

        async def _shutdown() -> None:
            try:
                await asyncio.to_thread(self._connection.send_close_stream)
            except Exception as exc:  # noqa: BLE001
                logger.warning("FluxSession send_close_stream failed: %s", exc)
            if self._connection_ctx is not None:
                try:
                    await asyncio.to_thread(self._connection_ctx.__exit__, None, None, None)
                except Exception:  # noqa: BLE001
                    pass

        try:
            await asyncio.wait_for(_shutdown(), timeout=5.0)
        except TimeoutError:
            logger.warning("FluxSession close timed out — abandoning SDK handle")

        if self._listener_thread is not None:
            await asyncio.to_thread(self._listener_thread.join, 2.0)
            self._listener_thread = None

        self._emit(_SENTINEL_CLOSE)
        self._started = False

    def _emit(self, event: object) -> None:
        """Push an event into the queue from any thread."""
        if self._loop is None:
            return
        self._loop.call_soon_threadsafe(self._queue.put_nowait, event)
