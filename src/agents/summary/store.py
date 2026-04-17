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


def _matches(record: dict, filters: dict) -> bool:
    """Return True if `record` passes all active filters. See `SummaryStore.list` for supported filter keys."""
    metrics = record.get("metrics") or {}
    if (sentiment := filters.get("sentiment")) and metrics.get("sentiment") != sentiment:
        return False
    if "resolved" in filters and metrics.get("resolved") != filters["resolved"]:
        return False
    if q := filters.get("q"):
        needle = q.lower()
        haystack = (
            (metrics.get("summary") or "").lower()
            + " "
            + " ".join(str(t).lower() for t in (metrics.get("topics") or []))
        )
        if needle not in haystack:
            return False
    ts = record.get("timestamp") or ""
    if (start := filters.get("from")) and ts < start:
        return False
    if (end := filters.get("to")) and ts > end:
        return False
    return True


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

    @abstractmethod
    async def list(self, filters: dict, skip: int = 0, limit: int = 20) -> tuple[list[dict], int]:
        """Return (page, total_count). Newest-first. `filters` supports:
        sentiment (str), resolved (bool), q (case-insensitive substring
        on summary+topics), from/to (ISO 8601 strings compared to timestamp).
        Unknown keys are ignored."""

    @abstractmethod
    async def get(self, session_id: str) -> dict | None:
        """Return one record by session_id, or None."""


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

    async def _read_all(self) -> list[dict]:
        def _load() -> list[dict]:
            if not self._path.exists():
                return []
            out: list[dict] = []
            with self._path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        out.append(json.loads(line))
                    except json.JSONDecodeError:
                        logger.warning("skipping malformed jsonl line")
            return out

        async with self._lock:
            return await asyncio.to_thread(_load)

    async def list(self, filters: dict, skip: int = 0, limit: int = 20) -> tuple[list[dict], int]:
        records = await self._read_all()
        records.sort(key=lambda r: r.get("timestamp") or "", reverse=True)
        filtered = [r for r in records if _matches(r, filters)]
        return filtered[skip : skip + limit], len(filtered)

    async def get(self, session_id: str) -> dict | None:
        # O(n) full-file linear scan — acceptable at demo scale. At larger
        # scale, switch to the Mongo backend (indexed on session_id).
        for record in await self._read_all():
            if record.get("session_id") == session_id:
                return record
        return None


def _strip_mongo_id(record: dict | None) -> dict | None:
    """Convert Mongo's non-JSON-serializable `_id: ObjectId` to a plain string."""
    if record is None:
        return None
    if "_id" in record:
        record["_id"] = str(record["_id"])
    return record


class MongoSummaryStore(SummaryStore):
    """MongoDB-backed store — inserts one document per call into `call_summaries`."""

    def __init__(self, mongo_url: str, db_name: str, collection_name: str = _MONGO_COLLECTION) -> None:
        client = MongoClient(mongo_url)
        self._collection = client[db_name][collection_name]

    async def save(self, record: dict) -> None:
        await asyncio.to_thread(self._collection.insert_one, record)

    async def list(self, filters: dict, skip: int = 0, limit: int = 20) -> tuple[list[dict], int]:
        query: dict = {}
        if sentiment := filters.get("sentiment"):
            query["metrics.sentiment"] = sentiment
        if "resolved" in filters:
            query["metrics.resolved"] = filters["resolved"]
        if q := filters.get("q"):
            query["$or"] = [
                {"metrics.summary": {"$regex": q, "$options": "i"}},
                {"metrics.topics": {"$regex": q, "$options": "i"}},
            ]
        if start := filters.get("from"):
            query.setdefault("timestamp", {})["$gte"] = start
        if end := filters.get("to"):
            query.setdefault("timestamp", {})["$lte"] = end

        def _run() -> tuple[list[dict], int]:
            cursor = self._collection.find(query).sort("timestamp", -1).skip(skip).limit(limit)
            records = [_strip_mongo_id(r) for r in cursor]
            return records, self._collection.count_documents(query)

        return await asyncio.to_thread(_run)

    async def get(self, session_id: str) -> dict | None:
        record = await asyncio.to_thread(self._collection.find_one, {"session_id": session_id})
        return _strip_mongo_id(record)


@lru_cache(maxsize=1)
def get_summary_store() -> SummaryStore:
    """Return the configured summary store — Mongo when MONGODB_URL is set, JSONL otherwise."""
    settings = get_settings()
    if settings.mongodb_url:
        logger.info("SummaryStore: MongoDB at %s (db=%s)", settings.mongodb_url, settings.mongodb_db_name)
        return MongoSummaryStore(settings.mongodb_url, settings.mongodb_db_name)
    logger.info("SummaryStore: JSONL at %s", settings.summaries_jsonl_path)
    return JsonlSummaryStore(settings.summaries_jsonl_path)
