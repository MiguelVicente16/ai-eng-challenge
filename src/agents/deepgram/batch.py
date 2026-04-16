"""Prerecorded STT and batch TTS wrappers around the Deepgram SDK.

All network calls are wrapped in asyncio.to_thread because the SDK's
prerecorded/speak methods are synchronous. Errors and missing credentials
fall back to safe empty values — callers decide whether to degrade.
"""

from __future__ import annotations

import asyncio
import base64
import binascii
import logging

from deepgram import DeepgramClient

from src.agents.deepgram.client import get_deepgram_client
from src.config import get_settings

logger = logging.getLogger(__name__)


def _get_client() -> DeepgramClient | None:
    return get_deepgram_client()


def decode_base64_audio(encoded: str) -> bytes:
    """Decode a base64 audio payload, raising ValueError on invalid input."""
    try:
        return base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValueError("invalid base64 audio payload") from exc


def encode_base64_audio(audio: bytes) -> str:
    """Encode audio bytes as a base64 ASCII string for JSON transport."""
    return base64.b64encode(audio).decode("ascii")


async def transcribe_audio(audio: bytes) -> str:
    """Transcribe an audio clip via Deepgram Nova (prerecorded).

    Returns an empty string when:
    - the Deepgram key is unset
    - the SDK call raises (logged, not re-raised — caller falls back)
    - Deepgram returns no transcript
    """
    client = _get_client()
    if client is None:
        logger.debug("Deepgram key unset — skipping STT")
        return ""

    settings = get_settings()

    def _call() -> str:
        try:
            response = client.listen.v1.media.transcribe_file(
                request=audio,
                model=settings.deepgram_stt_model,
                smart_format=True,
                language="en",
            )
            transcript = response.results.channels[0].alternatives[0].transcript
            return transcript or ""
        except Exception as exc:  # noqa: BLE001 — safe fallback is the whole point
            logger.warning("Deepgram STT failed: %s", exc)
            return ""

    return await asyncio.to_thread(_call)


_TTS_CACHE: dict[tuple[str, str, str, int | None], bytes] = {}
_TTS_CACHE_MAX = 128


def clear_tts_cache() -> None:
    """Flush the synthesized-speech cache. Test helper."""
    _TTS_CACHE.clear()


async def synthesize_speech(
    text: str,
    *,
    encoding: str = "mp3",
    sample_rate: int | None = None,
) -> bytes:
    """Synthesize spoken audio via Deepgram Aura (batch).

    `encoding` defaults to mp3 (used by /chat for JSON-over-HTTP transport).
    For streaming playback callers (e.g. the /voice WebSocket and the PTT
    call simulator), pass `encoding="linear16"` with `sample_rate=16000` to
    get raw PCM bytes that can be fed directly to an audio device with no
    decoder.

    Results are cached by (model, text, encoding, sample_rate). The cache
    is FIFO-evicted at ~128 entries. Variable-free phrases from the
    responder (opener, auth kickoffs, verifier_success, retry prompts,
    session_ended, non_customer_response, guardrails_fallback) end up
    cached after their first use, saving ~500ms of Deepgram latency on
    every subsequent call with the same text.

    Returns b"" when the Deepgram key is unset, the SDK call raises, or the text is empty.
    """
    if not text:
        return b""

    client = _get_client()
    if client is None:
        logger.debug("Deepgram key unset — skipping TTS")
        return b""

    settings = get_settings()
    cache_key = (settings.deepgram_tts_model, text, encoding, sample_rate)
    cached = _TTS_CACHE.get(cache_key)
    if cached is not None:
        logger.debug("TTS cache hit (%d bytes)", len(cached))
        return cached

    def _call() -> bytes:
        try:
            kwargs: dict = {
                "text": text,
                "model": settings.deepgram_tts_model,
                "encoding": encoding,
            }
            if sample_rate is not None:
                kwargs["sample_rate"] = sample_rate
            chunks = client.speak.v1.audio.generate(**kwargs)
            return b"".join(chunks)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Deepgram TTS failed: %s", exc)
            return b""

    audio = await asyncio.to_thread(_call)
    if audio:
        if len(_TTS_CACHE) >= _TTS_CACHE_MAX:
            _TTS_CACHE.pop(next(iter(_TTS_CACHE)))
        _TTS_CACHE[cache_key] = audio
    return audio
