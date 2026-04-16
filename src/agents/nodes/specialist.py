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
    "handle the customer's request by choosing ONE of four decisions:\n\n"
    "- 'route': the request clearly matches ONE of the services listed below. "
    "Pick the matching service as the 'service' field.\n"
    "- 'clarify': the request plausibly matches TWO OR MORE services and you "
    "cannot confidently pick one. Return a short 'clarification' field: a SINGLE "
    "direct question (max 120 chars) that asks the customer which of the candidate "
    "services they mean. No greeting, no preamble — just the question. Example: "
    "'Are you asking about a new loan or a credit card?'\n"
    "- 'escalate': the customer explicitly asked to speak to a human operator "
    "(e.g. 'I want to talk to a person', 'transfer me to an agent').\n"
    "- 'none': the request is off-topic, unclear, or doesn't match any service.\n\n"
    "{rules_block}\n\n"
    "Respond with: decision (route/clarify/escalate/none), service (only when "
    "decision='route'), clarification (only when decision='clarify'), and a "
    "short reasoning (max 10 words)."
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
    """Route the verified customer — possibly via one clarifying question."""
    tier = state.get("tier", "non_customer")

    if tier == "non_customer":
        logger.info("non-customer → non_customer_response")
        return {
            "stage": "completed",
            "response_phrase_key": "non_customer_response",
            "response_variables": {},
        }

    thread_id = config["configurable"]["thread_id"]
    current_stage = state.get("stage")
    clarify_retry_count = state.get("clarify_retry_count", 0)

    # Build the problem text. On a clarify revisit, combine the original problem
    # with the customer's answer so the LLM has full context.
    original_problem = state.get("user_problem") or state.get("user_message", "")
    if current_stage == "clarifying":
        answer = state.get("user_message", "")
        problem_for_llm = f"{original_problem}. Follow-up answer: {answer}".strip()
        classification = await classify_service(problem_for_llm)
    else:
        problem_for_llm = original_problem
        classification = await pop_classification(thread_id)
        if classification is None:
            logger.info("cache miss — classifying now...")
            classification = await classify_service(problem_for_llm)

    # Clarify branch — only allowed on first visit. Second clarify in a row forces general.
    if classification.decision == "clarify" and classification.clarification:
        if clarify_retry_count >= 1:
            logger.warning("clarify retry budget exhausted → routing to general")
            return _route_to_service(state, tier, "general")
        logger.info("ambiguous intent → asking one clarifying question")
        return {
            "stage": "clarifying",
            "clarification_question": classification.clarification,
            "clarify_retry_count": clarify_retry_count + 1,
            "response_phrase_key": "specialist_clarify",
            "response_variables": {"clarification": classification.clarification},
        }

    # Any other decision — resolve to a concrete service and finish the call.
    service = _resolve_service(classification)
    return _route_to_service(state, tier, service)


def _route_to_service(state: AgentState, tier: str, service: str) -> dict:
    """Return the final 'route to service' state update."""
    metadata = get_service_metadata(service)
    phrase_key = "premium_response" if tier == "premium" else "regular_response"

    logger.info("routed: %s → %s @ %s", tier, service, metadata["dept_phone"])

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
