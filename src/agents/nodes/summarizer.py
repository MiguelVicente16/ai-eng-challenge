"""Summarizer graph node — fire-and-forget post-call summary.

Schedules `run_summarization` as a background asyncio Task so the graph
returns immediately and the user's audio reply isn't delayed. The task
inherits the FastAPI event loop and completes independently of the
current request.

Trade-off: best-effort persistence. If the process dies before the task
finishes, that one summary is lost. Documented in architecture.md.
"""

import asyncio
import logging

from langchain_core.runnables import RunnableConfig

from src.agents.state import AgentState
from src.agents.summary import summarizer as svc

logger = logging.getLogger(__name__)

_TERMINAL_STAGES = {"completed", "failed"}


async def summarizer_node(state: AgentState, config: RunnableConfig) -> dict:
    """Schedule the summary LLM call when the call has just ended."""
    stage = state.get("stage")
    if stage not in _TERMINAL_STAGES:
        return {}
    if state.get("summary_fired"):
        return {}

    thread_id = config["configurable"]["thread_id"]
    logger.info("scheduling post-call summary (stage=%s)", stage)
    asyncio.create_task(svc.run_summarization(thread_id, dict(state)))
    return {"summary_fired": True}
