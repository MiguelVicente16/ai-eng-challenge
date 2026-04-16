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
