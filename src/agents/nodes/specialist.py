"""Specialist node — routes the verified customer to the right service."""

import logging

from langchain_core.runnables import RunnableConfig

from src.agents.config.routing import build_rules_prompt, get_service_metadata
from src.agents.intent_cache import pop_classification
from src.agents.llm import get_llm
from src.agents.results import ServiceClassification
from src.agents.state import AgentState
from src.logging_config import trim

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT_TEMPLATE = (
    "You are a routing assistant for a bank's customer support. Decide how to "
    "handle the customer's request by choosing ONE of three decisions:\n\n"
    "- 'route': the request clearly matches one of the services listed below. "
    "Pick the matching service as the 'service' field.\n"
    "- 'escalate': the customer explicitly asked to speak to a human operator "
    "(e.g. 'I want to talk to a person', 'transfer me to an agent').\n"
    "- 'none': the request is off-topic, unclear, or doesn't match any service.\n\n"
    "{rules_block}\n\n"
    "Respond with: decision (route/escalate/none), service (only when "
    "decision='route'), and a short reasoning (max 10 words)."
)


async def classify_service(user_problem: str) -> ServiceClassification:
    """Run the service-classification LLM call. Public so capture_problem can fire it early."""
    logger.info("LLM (background): classify_service %s", trim(user_problem))
    rules_block = build_rules_prompt()
    system = _SYSTEM_PROMPT_TEMPLATE.format(rules_block=rules_block)
    llm = get_llm().with_structured_output(ServiceClassification)
    result = await llm.ainvoke(
        [
            ("system", system),
            ("human", user_problem),
        ]
    )
    logger.info(
        "LLM ← classified: decision=%s service=%s reasoning=%r",
        result.decision,
        result.service or "-",
        result.reasoning,
    )
    return result


def _resolve_service(classification: ServiceClassification) -> str:
    """Pick the service to route to based on the decision.

    - route     → use classification.service (fallback to general if None)
    - escalate  → general (human operator lives in general support)
    - none      → general (off-topic / unclear)
    """
    if classification.decision == "route" and classification.service is not None:
        return classification.service
    return "general"


async def specialist_node(state: AgentState, config: RunnableConfig) -> dict:
    """Use the cached classification when available, otherwise classify sync."""
    tier = state.get("tier", "non_customer")
    user_problem = state.get("user_problem") or state.get("user_message", "")

    if tier == "non_customer":
        logger.info("non-customer → non_customer_response")
        return {
            "stage": "completed",
            "response_phrase_key": "non_customer_response",
            "response_variables": {},
        }

    thread_id = config["configurable"]["thread_id"]
    classification = await pop_classification(thread_id)

    if classification is None:
        logger.info("cache miss — classifying now...")
        classification = await classify_service(user_problem)

    service = _resolve_service(classification)
    metadata = get_service_metadata(service)
    phrase_key = "premium_response" if tier == "premium" else "regular_response"

    logger.info(
        "routed: %s → %s @ %s (decision=%s)",
        tier,
        service,
        metadata["dept_phone"],
        classification.decision,
    )

    return {
        "matched_service": service,
        "stage": "completed",
        "response_phrase_key": phrase_key,
        "response_variables": {
            "name": state.get("extracted_name", ""),
            "service_label": metadata["label"],
            "dept_phone": metadata["dept_phone"],
        },
    }
