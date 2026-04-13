"""Opener node — emits the scripted welcome phrase on a new session."""

import logging

from src.agents.state import AgentState

logger = logging.getLogger(__name__)


async def opener_node(state: AgentState) -> dict:
    """Emit the opener phrase and advance to awaiting_problem."""
    caller_recognized = state.get("caller_recognized")
    known_name_hint = state.get("known_name_hint")

    if caller_recognized and known_name_hint:
        logger.info("greeting known caller %s", known_name_hint)
        return {
            "stage": "awaiting_problem",
            "response_phrase_key": "opener_known_caller",
            "response_variables": {"name": known_name_hint},
            "retry_count": 0,
        }

    logger.info("greeting unknown caller")
    return {
        "stage": "awaiting_problem",
        "response_phrase_key": "opener_unknown_caller",
        "response_variables": {},
        "retry_count": 0,
    }
