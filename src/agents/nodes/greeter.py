"""Greeter node — extracts identity and verifies 2-of-3 match."""

import logging

from src.agents.llm import get_llm
from src.agents.normalization import normalize_iban, normalize_phone
from src.agents.results import IdentityExtraction
from src.agents.state import AgentState
from src.data import CUSTOMERS
from src.logging_config import mask, trim
from src.models import Customer

logger = logging.getLogger(__name__)

_MAX_RETRIES = 2

_SYSTEM_PROMPT = (
    "You are an identity extraction assistant for a bank. "
    "The user may provide their name, phone number, or IBAN in natural language. "
    "Extract ONLY what they state — do not guess or invent values. "
    "For phone numbers: return just the digits the user said, without spaces, "
    "dashes, or parentheses. Preserve a leading + only if the user clearly "
    "stated a country code. "
    "For IBANs: return uppercase with no spaces. "
    "If a field is not mentioned, return null."
)


async def _extract_identity(user_message: str) -> IdentityExtraction:
    logger.info("LLM: extracting identity from %s", trim(user_message, 60))
    llm = get_llm().with_structured_output(IdentityExtraction)
    result = await llm.ainvoke(
        [
            ("system", _SYSTEM_PROMPT),
            ("human", user_message),
        ]
    )
    logger.info(
        "LLM ← extracted: name=%s, phone=%s, iban=%s",
        result.name or "<none>",
        mask(result.phone),
        mask(result.iban),
    )
    return result


def _verify_identity(
    name: str | None,
    phone: str | None,
    iban: str | None,
) -> Customer | None:
    norm_phone = normalize_phone(phone)
    norm_iban = normalize_iban(iban)
    for customer in CUSTOMERS:
        matches = 0
        if name and customer.name.lower() == name.lower():
            matches += 1
        if norm_phone and normalize_phone(customer.phone) == norm_phone:
            matches += 1
        if norm_iban and normalize_iban(customer.iban) == norm_iban:
            matches += 1
        if matches >= 2:
            return customer
    return None


async def greeter_node(state: AgentState) -> dict:
    """Extract identity fields, verify 2-of-3, or handle retries."""
    user_message = state.get("user_message", "")
    extracted = await _extract_identity(user_message)

    name = extracted.name or state.get("extracted_name")
    phone = extracted.phone or state.get("extracted_phone")
    iban = extracted.iban or state.get("extracted_iban")

    customer = _verify_identity(name, phone, iban)

    if customer is not None:
        logger.info("verified customer %s → ask_secret", mask(customer.iban))
        return {
            "extracted_name": name,
            "extracted_phone": phone,
            "extracted_iban": iban,
            "verified_iban": customer.iban,
            "secret_question": customer.secret,
            "stage": "ask_secret",
            "response_phrase_key": "verifier_ask_secret",
            "response_variables": {"secret_question": customer.secret},
            "retry_count": 0,
        }

    nothing_new = extracted.name is None and extracted.phone is None and extracted.iban is None

    if nothing_new:
        retry_count = state.get("retry_count", 0) + 1
        if retry_count >= _MAX_RETRIES:
            logger.error("retry exhausted (%d/%d) → fallback to general", retry_count, _MAX_RETRIES)
            return {
                "stage": "failed",
                "response_phrase_key": "fallback_to_general",
                "response_variables": {"dept_phone": "+1999888000"},
                "retry_count": retry_count,
            }
        logger.warning("no progress — retry %d/%d", retry_count, _MAX_RETRIES)
        return {
            "response_phrase_key": "retry_unclear_identity",
            "response_variables": {},
            "retry_count": retry_count,
        }

    provided = sum(1 for x in [name, phone, iban] if x)
    if provided < 2:
        missing = "phone number or IBAN" if not phone and not iban else "name or IBAN"
        logger.info("partial identity (%d fields) — need %s", provided, missing)
        return {
            "extracted_name": name,
            "extracted_phone": phone,
            "extracted_iban": iban,
            "response_phrase_key": "greeter_need_more_info",
            "response_variables": {"missing_field": missing},
        }

    # 2+ fields given but no customer matched — give one retry for typos,
    # then recognize as non-customer.
    retry_count = state.get("retry_count", 0) + 1
    if retry_count >= _MAX_RETRIES:
        logger.error("identity not found after %d tries → non_customer_response", retry_count)
        return {
            "extracted_name": name,
            "extracted_phone": phone,
            "extracted_iban": iban,
            "stage": "completed",
            "response_phrase_key": "non_customer_response",
            "response_variables": {},
            "retry_count": retry_count,
        }

    logger.warning("identity not found — retry %d/%d", retry_count, _MAX_RETRIES)
    return {
        "extracted_name": name,
        "extracted_phone": phone,
        "extracted_iban": iban,
        "response_phrase_key": "greeter_identity_not_found",
        "response_variables": {},
        "retry_count": retry_count,
    }
