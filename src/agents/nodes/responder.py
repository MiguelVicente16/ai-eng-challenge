"""Responder node — renders the final response from phrase_key + variables."""

import logging

from src.agents.config.phrases import render
from src.agents.state import AgentState
from src.logging_config import trim

logger = logging.getLogger(__name__)


async def responder_node(state: AgentState) -> dict:
    """Look up the phrase and interpolate variables into output_text."""
    key = state.get("response_phrase_key")
    variables = state.get("response_variables") or {}

    if not key:
        return {"output_text": ""}

    try:
        text = render(key, variables)
        logger.info("rendered: %s", trim(text, 80))
    except KeyError:
        logger.warning("missing variable for phrase=%s → rendering fallback", key)
        text = render("guardrails_fallback", {"dept_phone": "+1999888000"})
        logger.info("rendered: %s", trim(text, 80))

    return {"output_text": text}
