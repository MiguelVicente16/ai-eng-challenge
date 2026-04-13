"""Bouncer node — classifies the verified customer into a tier."""

import logging

from src.agents.state import AgentState
from src.data import ACCOUNTS
from src.logging_config import mask

logger = logging.getLogger(__name__)


async def bouncer_node(state: AgentState) -> dict:
    """Deterministic tier lookup by verified IBAN."""
    iban = state.get("verified_iban")

    if iban is None:
        logger.info("no matching account → non_customer")
        return {"tier": "non_customer"}

    for account in ACCOUNTS:
        if account.iban == iban:
            tier = "premium" if account.premium else "regular"
            logger.info("tier: %s (%s)", tier, mask(iban))
            return {"tier": tier}

    logger.info("no matching account → non_customer")
    return {"tier": "non_customer"}
