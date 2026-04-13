"""Text-to-speech node (placeholder).

Currently a no-op. When real TTS is wired in, this returns an audio URL.
"""

import logging

from src.agents.state import AgentState
from src.logging_config import trim

logger = logging.getLogger(__name__)


async def tts_node(state: AgentState) -> dict:
    """Pass-through TTS — no audio generated yet."""
    output_text = state.get("output_text", "")
    logger.debug("output_text=%s", trim(output_text))
    logger.debug("(no-op)")
    return {}
