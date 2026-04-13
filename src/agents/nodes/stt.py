"""Speech-to-text node (placeholder).

Currently pass-through: copies input_text to user_message.
When real STT is wired in, only this function body changes — the
graph shape stays the same.
"""

import logging

from src.agents.state import AgentState
from src.logging_config import trim

logger = logging.getLogger(__name__)


async def stt_node(state: AgentState) -> dict:
    """Pass-through STT — copies input_text into user_message."""
    input_text = state.get("input_text", "")
    logger.debug("input_text=%s", trim(input_text))
    result = {"user_message": input_text}
    logger.debug("user_message=%s", trim(input_text))
    return result
