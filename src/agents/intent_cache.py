"""Module-level asyncio task cache for background service classification.

The cache lives in process memory. When the capture_problem node captures
the user's problem, it fires an asyncio.Task to classify the service in
parallel with the auth flow. The specialist node pops and awaits the task
later, saving ~1-2 seconds on the final turn.

Cache entries are NOT persisted via the LangGraph checkpointer — if the
process restarts mid-conversation, the specialist falls back to classifying
synchronously from `user_problem` in state.
"""

from __future__ import annotations

import asyncio
import logging

from src.agents.results import ServiceClassification

logger = logging.getLogger(__name__)

_cache: dict[str, asyncio.Task[ServiceClassification]] = {}


def start_classification(thread_id: str, task: asyncio.Task[ServiceClassification]) -> None:
    """Register a background classification task for a session."""
    _cache[thread_id] = task
    logger.info("task registered for %s", thread_id[:8])


async def pop_classification(thread_id: str) -> ServiceClassification | None:
    """Pop and await the cached task. Returns None on miss or error."""
    task = _cache.pop(thread_id, None)
    if task is None:
        logger.info("cache miss for %s", thread_id[:8])
        return None
    try:
        result = await task
        logger.info("cache hit for %s: %s", thread_id[:8], result.service)
        return result
    except Exception as exc:
        logger.warning("cache task failed for %s: %s", thread_id[:8], exc)
        return None


def clear() -> None:
    """Clear the entire cache. For test isolation."""
    _cache.clear()
