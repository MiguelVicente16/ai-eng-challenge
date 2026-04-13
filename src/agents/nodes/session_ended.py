"""Session-ended node — replies when a new turn arrives on a terminal session.

Once a session reaches the `completed` or `failed` stage, any further turns
the client sends should not replay the old routing message. This node emits
a terminal-state phrase instructing the user to start a new conversation.
"""

import logging

from src.agents.state import AgentState

logger = logging.getLogger(__name__)


async def session_ended_node(state: AgentState) -> dict:
    """Short-circuit response for new turns on a completed/failed session."""
    logger.info("new turn on terminal session (stage=%s) → session_ended", state.get("stage"))
    return {
        "response_phrase_key": "session_ended",
        "response_variables": {},
    }
