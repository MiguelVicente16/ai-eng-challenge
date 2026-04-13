"""Guardrails node — safety check on rendered response before it leaves the graph."""

import logging

from src.agents.config.phrases import render
from src.agents.state import AgentState
from src.data import CUSTOMERS

logger = logging.getLogger(__name__)

# Collected once at import time: every customer's sensitive identifiers
_SENSITIVE_IDENTIFIERS: set[str] = set()
for _c in CUSTOMERS:
    _SENSITIVE_IDENTIFIERS.add(_c.phone)
    _SENSITIVE_IDENTIFIERS.add(_c.iban)

_FALLBACK_DEPT_PHONE = "+1999888000"


def _contains_unverified_sensitive_data(text: str, verified_iban: str | None) -> bool:
    """True if the text leaks any sensitive identifier that is NOT the current verified customer's."""
    for identifier in _SENSITIVE_IDENTIFIERS:
        if identifier in text:
            if verified_iban and identifier == verified_iban:
                continue
            return True
    return False


async def guardrails_node(state: AgentState) -> dict:
    """Verify the rendered output_text is safe. Replace with fallback if not."""
    output_text = state.get("output_text", "")
    verified_iban = state.get("verified_iban")

    if _contains_unverified_sensitive_data(output_text, verified_iban):
        logger.warning("BLOCKED: sensitive data leak detected → emitting fallback")
        safe_text = render("guardrails_fallback", {"dept_phone": _FALLBACK_DEPT_PHONE})
        return {"output_text": safe_text}

    return {}
