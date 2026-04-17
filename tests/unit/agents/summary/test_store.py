"""Tests for the SummaryStore persistence layer."""

import json
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _reset_store_cache():
    from src.agents.summary import store

    store.get_summary_store.cache_clear()
    yield
    store.get_summary_store.cache_clear()


@pytest.mark.asyncio
async def test_jsonl_summary_store_should_append_record_to_file(tmp_path):
    from src.agents.summary.store import JsonlSummaryStore

    # Arrange
    path = tmp_path / "summaries.jsonl"
    store = JsonlSummaryStore(path)

    # Act
    await store.save({"session_id": "s1", "tier": "premium"})
    await store.save({"session_id": "s2", "tier": "regular"})

    # Assert
    lines = path.read_text().strip().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0]) == {"session_id": "s1", "tier": "premium"}
    assert json.loads(lines[1]) == {"session_id": "s2", "tier": "regular"}


@pytest.mark.asyncio
async def test_jsonl_summary_store_should_create_parent_directory_if_missing(tmp_path):
    from src.agents.summary.store import JsonlSummaryStore

    # Arrange — target path has a missing parent directory
    path = tmp_path / "nested" / "deeper" / "summaries.jsonl"
    store = JsonlSummaryStore(path)

    # Act
    await store.save({"session_id": "s1"})

    # Assert
    assert path.exists()
    assert json.loads(path.read_text().strip()) == {"session_id": "s1"}


@pytest.mark.asyncio
async def test_jsonl_summary_store_should_serialize_concurrent_writes(tmp_path):
    import asyncio

    from src.agents.summary.store import JsonlSummaryStore

    # Arrange — 50 concurrent saves, each with a distinct index
    path = tmp_path / "summaries.jsonl"
    store = JsonlSummaryStore(path)

    # Act
    await asyncio.gather(*[store.save({"i": i, "payload": "x" * 500}) for i in range(50)])

    # Assert — every line is valid JSON (no torn writes) and every index is present
    lines = path.read_text().strip().splitlines()
    assert len(lines) == 50
    seen = {json.loads(line)["i"] for line in lines}
    assert seen == set(range(50))


@pytest.mark.asyncio
async def test_mongo_summary_store_should_insert_record_into_collection(mocker):
    from src.agents.summary.store import MongoSummaryStore

    # Arrange
    collection = mocker.MagicMock()
    client = mocker.MagicMock()
    client.__getitem__.return_value.__getitem__.return_value = collection
    mocker.patch("src.agents.summary.store.MongoClient", return_value=client)

    store = MongoSummaryStore("mongodb://fake", "deus_bank", "call_summaries")

    # Act
    await store.save({"session_id": "s1", "tier": "premium"})

    # Assert
    collection.insert_one.assert_called_once_with({"session_id": "s1", "tier": "premium"})


def test_get_summary_store_should_return_mongo_when_mongodb_url_set(mocker):
    from src.agents.summary import store

    # Arrange
    settings = mocker.MagicMock(
        mongodb_url="mongodb://localhost:27017",
        mongodb_db_name="deus_bank",
        summaries_jsonl_path=Path("data/call_summaries.jsonl"),
    )
    mocker.patch("src.agents.summary.store.get_settings", return_value=settings)
    mocker.patch("src.agents.summary.store.MongoClient")

    # Act
    actual = store.get_summary_store()

    # Assert
    assert actual.__class__.__name__ == "MongoSummaryStore"


def test_get_summary_store_should_return_jsonl_when_mongodb_url_unset(mocker, tmp_path):
    from src.agents.summary import store

    # Arrange
    settings = mocker.MagicMock(
        mongodb_url=None,
        mongodb_db_name="deus_bank",
        summaries_jsonl_path=tmp_path / "summaries.jsonl",
    )
    mocker.patch("src.agents.summary.store.get_settings", return_value=settings)

    # Act
    actual = store.get_summary_store()

    # Assert
    assert actual.__class__.__name__ == "JsonlSummaryStore"


def test_summary_store_should_be_abstract():
    import pytest as _pytest

    from src.agents.summary.store import SummaryStore

    # Act + Assert — instantiating the ABC must fail
    with _pytest.raises(TypeError):
        SummaryStore()  # type: ignore[abstract]


@pytest.mark.asyncio
async def test_jsonl_store_list_should_return_all_records_newest_first(tmp_path):
    from src.agents.summary.store import JsonlSummaryStore

    # Arrange
    store = JsonlSummaryStore(tmp_path / "sum.jsonl")
    await store.save(
        {"session_id": "a", "timestamp": "2026-01-01T00:00:00+00:00", "metrics": {"sentiment": "positive"}}
    )
    await store.save(
        {"session_id": "b", "timestamp": "2026-02-01T00:00:00+00:00", "metrics": {"sentiment": "negative"}}
    )

    # Act
    items, total = await store.list(filters={}, skip=0, limit=10)

    # Assert
    assert total == 2
    assert [r["session_id"] for r in items] == ["b", "a"]


@pytest.mark.asyncio
async def test_jsonl_store_list_should_filter_by_sentiment(tmp_path):
    from src.agents.summary.store import JsonlSummaryStore

    # Arrange
    store = JsonlSummaryStore(tmp_path / "sum.jsonl")
    await store.save(
        {"session_id": "a", "timestamp": "2026-01-01T00:00:00+00:00", "metrics": {"sentiment": "positive"}}
    )
    await store.save(
        {"session_id": "b", "timestamp": "2026-02-01T00:00:00+00:00", "metrics": {"sentiment": "negative"}}
    )

    # Act
    items, total = await store.list(filters={"sentiment": "positive"}, skip=0, limit=10)

    # Assert
    assert total == 1
    assert items[0]["session_id"] == "a"


@pytest.mark.asyncio
async def test_jsonl_store_list_should_paginate(tmp_path):
    from src.agents.summary.store import JsonlSummaryStore

    # Arrange
    store = JsonlSummaryStore(tmp_path / "sum.jsonl")
    for i in range(5):
        await store.save({"session_id": f"s{i}", "timestamp": f"2026-01-{i + 1:02d}T00:00:00+00:00", "metrics": {}})

    # Act
    page, total = await store.list(filters={}, skip=2, limit=2)

    # Assert
    assert total == 5
    assert [r["session_id"] for r in page] == ["s2", "s1"]  # newest-first, skip 2


@pytest.mark.asyncio
async def test_jsonl_store_get_should_return_record_by_session_id(tmp_path):
    from src.agents.summary.store import JsonlSummaryStore

    # Arrange
    store = JsonlSummaryStore(tmp_path / "sum.jsonl")
    await store.save({"session_id": "target", "timestamp": "2026-01-01T00:00:00+00:00", "metrics": {}})

    # Act
    record = await store.get("target")

    # Assert
    assert record is not None
    assert record["session_id"] == "target"


@pytest.mark.asyncio
async def test_jsonl_store_get_should_return_none_when_missing(tmp_path):
    from src.agents.summary.store import JsonlSummaryStore

    # Arrange
    store = JsonlSummaryStore(tmp_path / "sum.jsonl")

    # Act
    record = await store.get("nope")

    # Assert
    assert record is None


@pytest.mark.asyncio
async def test_jsonl_store_list_should_filter_by_resolved_and_search(tmp_path):
    from src.agents.summary.store import JsonlSummaryStore

    # Arrange
    store = JsonlSummaryStore(tmp_path / "sum.jsonl")
    await store.save(
        {
            "session_id": "a",
            "timestamp": "2026-01-01T00:00:00+00:00",
            "metrics": {"resolved": True, "summary": "Helped with card fraud", "topics": ["card"]},
        }
    )
    await store.save(
        {
            "session_id": "b",
            "timestamp": "2026-02-01T00:00:00+00:00",
            "metrics": {"resolved": False, "summary": "Could not help with loans", "topics": ["loans"]},
        }
    )

    # Act
    items_true, _ = await store.list(filters={"resolved": True}, skip=0, limit=10)
    items_search, _ = await store.list(filters={"q": "loans"}, skip=0, limit=10)

    # Assert
    assert [r["session_id"] for r in items_true] == ["a"]
    assert [r["session_id"] for r in items_search] == ["b"]


@pytest.mark.asyncio
async def test_mongo_store_list_should_query_collection_with_filters_and_sort(mocker):
    from src.agents.summary.store import MongoSummaryStore

    # Arrange — mocker replaces MongoClient so no real connection is made
    mongo_client = mocker.patch("src.agents.summary.store.MongoClient")
    fake_cursor = mocker.MagicMock()
    fake_cursor.sort.return_value = fake_cursor
    fake_cursor.skip.return_value = fake_cursor
    fake_cursor.limit.return_value = [{"session_id": "a"}]
    fake_collection = mocker.MagicMock()
    fake_collection.find.return_value = fake_cursor
    fake_collection.count_documents.return_value = 1
    mongo_client.return_value = {"db": {"call_summaries": fake_collection}}

    store = MongoSummaryStore("mongodb://fake", "db")

    # Act
    items, total = await store.list(
        filters={"sentiment": "positive", "resolved": True, "q": "card", "from": "2026-01-01", "to": "2026-12-31"},
        skip=5,
        limit=10,
    )

    # Assert
    assert items == [{"session_id": "a"}]
    assert total == 1
    query = fake_collection.find.call_args.args[0]
    assert query["metrics.sentiment"] == "positive"
    assert query["metrics.resolved"] is True
    assert "$regex" in str(query)
    assert query["timestamp"]["$gte"] == "2026-01-01"
    assert query["timestamp"]["$lte"] == "2026-12-31"
    fake_cursor.sort.assert_called_once_with("timestamp", -1)
    fake_cursor.skip.assert_called_once_with(5)
    fake_cursor.limit.assert_called_once_with(10)


@pytest.mark.asyncio
async def test_mongo_store_get_should_find_by_session_id(mocker):
    from src.agents.summary.store import MongoSummaryStore

    # Arrange
    mongo_client = mocker.patch("src.agents.summary.store.MongoClient")
    fake_collection = mocker.MagicMock()
    fake_collection.find_one.return_value = {"session_id": "target"}
    mongo_client.return_value = {"db": {"call_summaries": fake_collection}}

    store = MongoSummaryStore("mongodb://fake", "db")

    # Act
    record = await store.get("target")

    # Assert
    assert record == {"session_id": "target"}
    fake_collection.find_one.assert_called_once_with({"session_id": "target"})
