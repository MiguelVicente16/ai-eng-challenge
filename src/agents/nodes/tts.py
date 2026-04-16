"""Text-to-speech node — Deepgram Aura (batch).

Pass-through when no `output_text` is set OR the Deepgram key is unset. When
both are present, synthesizes MP3 audio and stores it in `output_audio`. The
ChatService is responsible for serializing that to base64 for JSON responses.
"""

import logging

from src.agents.deepgram.batch import synthesize_speech
from src.agents.state import AgentState
from src.logging_config import trim

logger = logging.getLogger(__name__)


async def tts_node(state: AgentState) -> dict:
    """Populate `output_audio` when Deepgram is configured and there is text to speak."""
    output_text = state.get("output_text", "")
    if not output_text:
        logger.debug("no output_text - skipping TTS")
        return {}

    encoding = state.get("tts_encoding") or "mp3"
    sample_rate = state.get("tts_sample_rate")
    audio = await synthesize_speech(output_text, encoding=encoding, sample_rate=sample_rate)
    if not audio:
        return {}

    logger.info("TTS <- %d bytes (%s) for %s", len(audio), encoding, trim(output_text))
    return {"output_audio": audio}
