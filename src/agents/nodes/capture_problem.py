"""Capture Problem node — stores the user's problem and kicks off background classification."""

import asyncio
import logging

from langchain_core.runnables import RunnableConfig

from src.agents.intent_cache import start_classification
from src.agents.nodes.specialist import classify_service
from src.agents.state import AgentState

logger = logging.getLogger(__name__)

_MAX_RETRIES = 2


def _is_meaningful(text: str) -> bool:
    """Light heuristic: require at least a few characters of content."""
    return len(text.strip()) >= 3


async def capture_problem_node(state: AgentState, config: RunnableConfig) -> dict:
    """Store the user's problem, start background classification, advance stage."""
    user_message = state.get("user_message", "")

    if not _is_meaningful(user_message):
        retry_count = state.get("retry_count", 0) + 1
        if retry_count >= _MAX_RETRIES:
            logger.error(
                "retry exhausted (%d/%d) → fallback to general",
                retry_count,
                _MAX_RETRIES,
            )
            return {
                "stage": "failed",
                "response_phrase_key": "fallback_to_general",
                "response_variables": {"dept_phone": "+1999888000"},
                "retry_count": retry_count,
            }
        logger.warning("unclear problem — retry %d/%d", retry_count, _MAX_RETRIES)
        return {
            "response_phrase_key": "retry_unclear_problem",
            "response_variables": {},
            "retry_count": retry_count,
        }

    thread_id = config["configurable"]["thread_id"]
    task = asyncio.create_task(classify_service(user_message))
    start_classification(thread_id, task)

    logger.info("problem captured (%d chars) — starting background classification", len(user_message))

    phrase_key = "auth_kickoff_known_caller" if state.get("caller_recognized") else "auth_kickoff_unknown_caller"

    return {
        "user_problem": user_message,
        "stage": "collecting_identity",
        "response_phrase_key": phrase_key,
        "response_variables": {},
        "retry_count": 0,
    }
