"""Post-call summarizer: transcript -> LLM -> persistence.

Pure functions so they can be tested in isolation. `run_summarization` is
the top-level entry point called from the graph node; it wraps
`generate_summary` (LLM call) and `get_summary_store().save` (persistence)
and swallows errors so the caller doesn't have to.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from src.agents.llm import get_llm
from src.agents.state import AgentState
from src.agents.summary.metrics import build_summary_model, build_summary_prompt
from src.agents.summary.store import get_summary_store
from src.logging_config import mask

logger = logging.getLogger(__name__)


def build_transcript(state: AgentState) -> str:
    """Render the call's salient state into a short text block for the LLM.

    Includes identity/tier/problem/outcome plus signals the LLM needs for
    good sentiment + resolved classification: retry counts (friction),
    whether the specialist had to clarify, and whether the caller's IBAN
    was successfully verified (auth succeeded).
    """
    lines: list[str] = []

    if state.get("caller_recognized") and state.get("known_name_hint"):
        lines.append(f"Caller: {state['known_name_hint']} (recognized by phone lookup)")
    elif state.get("extracted_name"):
        lines.append(f"Caller self-identified as: {state['extracted_name']}")
    else:
        lines.append("Caller: not identified")

    if tier := state.get("tier"):
        lines.append(f"Tier: {tier}")

    if problem := state.get("user_problem"):
        lines.append(f"Stated problem: {problem}")

    last_msg = state.get("user_message") or ""
    if last_msg and last_msg != state.get("user_problem"):
        lines.append(f"Last user message: {last_msg}")

    if question := state.get("clarification_question"):
        lines.append(f"System asked to clarify: {question}")

    if retries := state.get("retry_count"):
        if retries > 0:
            lines.append(f"Stage retry count: {retries}")

    if clarify_retries := state.get("clarify_retry_count"):
        if clarify_retries > 0:
            lines.append(f"Clarification retries: {clarify_retries}")

    lines.append(f"Authenticated: {state.get('verified_iban') is not None}")

    if service := state.get("matched_service"):
        lines.append(f"Routed to service: {service}")

    if stage := state.get("stage"):
        lines.append(f"Final stage: {stage}")

    return "\n".join(lines)


def build_record(thread_id: str, state: AgentState, summary: Any) -> dict:
    """Assemble the document that gets written to the SummaryStore.

    Uses `summary.model_dump(mode="json")` so datetimes, enums, and UUIDs
    serialize to JSON-safe primitives (the JSONL store's `default=str`
    fallback otherwise produces inconsistent datetime formats).
    """
    phone = state.get("caller_phone")
    record: dict = {
        "session_id": thread_id,
        "timestamp": datetime.now(UTC).isoformat(),
        # Bump this when the shape of `summary_metrics.yaml` changes
        # (metric added/removed/renamed, type changed). Downstream
        # consumers use it to pick the right parser for older records.
        "metrics_schema_version": 1,
        "tier": state.get("tier"),
        "matched_service": state.get("matched_service"),
        "stage": state.get("stage"),
        "caller_phone_masked": mask(phone) if phone else None,
        "user_problem": state.get("user_problem"),
        "metrics": summary.model_dump(mode="json"),
    }
    return record


async def generate_summary(state: AgentState) -> Any | None:
    """Call the LLM with the dynamic schema. Returns None on any failure."""
    try:
        model_cls = build_summary_model()
        system_prompt = build_summary_prompt()
        transcript = build_transcript(state)
        llm = get_llm(temperature=0.1).with_structured_output(model_cls)
        logger.info(
            "generating summary for stage=%s service=%s",
            state.get("stage"),
            state.get("matched_service"),
        )
        return await llm.ainvoke(
            [
                ("system", system_prompt),
                ("human", transcript),
            ]
        )
    except Exception as exc:  # noqa: BLE001 — best-effort background work
        logger.warning("summary LLM call failed: %s", exc)
        return None


async def run_summarization(thread_id: str, state: AgentState) -> None:
    """End-to-end: generate summary and persist. Swallows all errors."""
    summary = await generate_summary(state)
    if summary is None:
        return

    record = build_record(thread_id, state, summary)
    store = get_summary_store()
    try:
        await store.save(record)
        logger.info("summary saved for session=%s", thread_id[:8])
    except Exception as exc:  # noqa: BLE001
        logger.warning("summary persistence failed: %s", exc)
