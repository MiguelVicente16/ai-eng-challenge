"""SummaryStore persistence layer — MongoDB when configured, JSONL fallback.

Factory selection mirrors `src.agents.checkpointer.get_checkpointer`: when
`MONGODB_URL` is set, writes go to the `call_summaries` collection in the
configured database; otherwise, records are appended to a local JSONL
file (default `data/call_summaries.jsonl`). Both implementations expose
the same async `save(record: dict) -> None` interface.

The factory is `lru_cache`d so the store is created once per process.
Tests should call `get_summary_store.cache_clear()` between cases that
patch settings.
"""

from __future__ import annotations

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from functools import lru_cache
from pathlib import Path

from pymongo import MongoClient

from src.config import get_settings

logger = logging.getLogger(__name__)

_MONGO_COLLECTION = "call_summaries"


class SummaryStore(ABC):
    """Abstract base class for post-call summary persistence."""

    @abstractmethod
    async def save(self, record: dict) -> None:
        """Persist one summary record. Must be safe to call concurrently.

        Raises backend-specific exceptions on failure (e.g. pymongo errors,
        OSError). Callers are responsible for handling these — the
        summarizer runs fire-and-forget and swallows errors at the
        top level.
        """


class JsonlSummaryStore(SummaryStore):
    """Append-only JSONL file writer. Creates parent directories on first write."""

    def __init__(self, path: Path) -> None:
        self._path = Path(path)
        self._lock = asyncio.Lock()

    async def save(self, record: dict) -> None:
        # `default=str` is a safety net for rare objects like ObjectId.
        # Callers should pre-serialize complex types (datetime, Enum, UUID)
        # via `pydantic.BaseModel.model_dump(mode="json")` so encoded values
        # stay round-trippable. Relying on `default=str` would produce
        # inconsistent datetime formats and lossy set/bytes output.
        line = json.dumps(record, default=str) + "\n"

        def _append() -> None:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._path.open("a", encoding="utf-8") as f:
                f.write(line)

        async with self._lock:
            await asyncio.to_thread(_append)


class MongoSummaryStore(SummaryStore):
    """MongoDB-backed store — inserts one document per call into `call_summaries`."""

    def __init__(self, mongo_url: str, db_name: str, collection_name: str = _MONGO_COLLECTION) -> None:
        client = MongoClient(mongo_url)
        self._collection = client[db_name][collection_name]

    async def save(self, record: dict) -> None:
        await asyncio.to_thread(self._collection.insert_one, record)


@lru_cache(maxsize=1)
def get_summary_store() -> SummaryStore:
    """Return the configured summary store — Mongo when MONGODB_URL is set, JSONL otherwise."""
    settings = get_settings()
    if settings.mongodb_url:
        logger.info("SummaryStore: MongoDB at %s (db=%s)", settings.mongodb_url, settings.mongodb_db_name)
        return MongoSummaryStore(settings.mongodb_url, settings.mongodb_db_name)
    logger.info("SummaryStore: JSONL at %s", settings.summaries_jsonl_path)
    return JsonlSummaryStore(settings.summaries_jsonl_path)
