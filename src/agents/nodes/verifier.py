"""Verifier node — handles the secret question challenge with retry budget."""

import logging

from src.agents.llm import get_llm
from src.agents.normalization import normalize_iban
from src.agents.results import SecretAnswer
from src.agents.state import AgentState
from src.data import CUSTOMERS
from src.logging_config import mask
from src.models import Customer

logger = logging.getLogger(__name__)

_MAX_RETRIES = 2

_SYSTEM_PROMPT = (
    "You are extracting the customer's answer to a secret question. "
    "Return ONLY the answer they stated, verbatim. "
    "If they did not answer, return null."
)


async def _extract_answer(user_message: str) -> SecretAnswer:
    logger.info("LLM: extracting secret answer")
    llm = get_llm().with_structured_output(SecretAnswer)
    result = await llm.ainvoke(
        [
            ("system", _SYSTEM_PROMPT),
            ("human", user_message),
        ]
    )
    logger.info("LLM ← answer received (masked)")
    return result


def _find_customer(iban: str) -> Customer | None:
    target = normalize_iban(iban)
    for customer in CUSTOMERS:
        if normalize_iban(customer.iban) == target:
            return customer
    return None


def _answer_matches(expected: str, given: str) -> bool:
    return expected.lower().strip() == given.lower().strip()


async def verifier_node(state: AgentState) -> dict:
    """Verify the secret question answer with retry budget."""
    iban = state.get("verified_iban")
    user_message = state.get("user_message", "")

    customer = _find_customer(iban) if iban else None

    if customer is None:
        logger.error("customer not found in DB iban=%s → fallback to general", mask(iban))
        return {
            "stage": "failed",
            "response_phrase_key": "fallback_to_general",
            "response_variables": {"dept_phone": "+1999888000"},
        }

    extracted = await _extract_answer(user_message)

    if extracted.answer and _answer_matches(customer.answer, extracted.answer):
        logger.info("secret matches customer %s → routing", mask(iban))
        return {
            "stage": "routing",
            "response_phrase_key": "verifier_success",
            "response_variables": {},
            "retry_count": 0,
        }

    retry_count = state.get("retry_count", 0) + 1
    if retry_count >= _MAX_RETRIES:
        logger.error("retry exhausted (%d/%d) → fallback to general", retry_count, _MAX_RETRIES)
        return {
            "stage": "failed",
            "response_phrase_key": "fallback_to_general",
            "response_variables": {"dept_phone": "+1999888000"},
            "retry_count": retry_count,
        }

    logger.warning("wrong answer — retry %d/%d", retry_count, _MAX_RETRIES)
    return {
        "response_phrase_key": "retry_unclear_secret",
        "response_variables": {},
        "retry_count": retry_count,
    }
