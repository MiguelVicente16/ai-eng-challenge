"""Speech-to-text node — Deepgram Nova (batch).

Pass-through when no `input_audio` is provided: copies `input_text` to
`user_message`. When audio bytes are present AND the Deepgram key is set,
calls Nova and uses the transcript instead. On any Deepgram failure the
node silently falls back to whatever text was supplied.
"""

import logging

from src.agents.deepgram.batch import transcribe_audio
from src.agents.state import AgentState
from src.logging_config import trim

logger = logging.getLogger(__name__)


async def stt_node(state: AgentState) -> dict:
    """Populate `user_message` from audio (if given) or input text."""
    audio = state.get("input_audio")
    input_text = state.get("input_text", "")

    if audio:
        transcript = await transcribe_audio(audio)
        if transcript:
            logger.info("STT -> %s", trim(transcript))
            return {"user_message": transcript}
        logger.info("STT empty - falling back to input_text")

    return {"user_message": input_text}
