"""Checkpointer factory — selects between InMemorySaver and MongoDBSaver.

The factory inspects Settings.mongodb_url. When set, it constructs a
MongoDB-backed checkpointer. When unset, it falls back to InMemorySaver
so the app runs with zero external dependencies.

The MongoDBSaver is the sync variant from langgraph-checkpoint-mongodb.
LangGraph's base BaseCheckpointSaver provides default async method
implementations that wrap the sync methods via asyncio.to_thread(),
so the sync saver works correctly with our async graph (ainvoke,
aget_state). The only cost is a small thread-pool hop per DB operation.

The factory is lru_cached so the checkpointer is created once per process.
"""

from functools import lru_cache

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.mongodb import MongoDBSaver
from pymongo import MongoClient

from src.config import get_settings


@lru_cache(maxsize=1)
def get_checkpointer():
    """Return the appropriate checkpointer based on configuration."""
    settings = get_settings()

    if settings.mongodb_url:
        client = MongoClient(settings.mongodb_url)
        return MongoDBSaver(client, db_name=settings.mongodb_db_name)

    return InMemorySaver()
