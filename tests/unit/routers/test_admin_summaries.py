"""Tests for /api/summaries routes."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def client_with_mock_store(mocker):
    """Spin a FastAPI app with a mocked SummaryStore."""
    # Arrange
    store = mocker.MagicMock()

    async def _list(filters, skip, limit):
        return [{"session_id": "a"}], 1

    async def _get(session_id):
        if session_id == "a":
            return {"session_id": "a", "metrics": {}}
        return None

    store.list = mocker.AsyncMock(side_effect=_list)
    store.get = mocker.AsyncMock(side_effect=_get)

    mocker.patch("src.routers.admin_summaries.get_summary_store", return_value=store)

    from src.routers.admin_summaries import router

    app = FastAPI()
    app.include_router(router, prefix="/api")
    return TestClient(app), store


def test_list_summaries_should_default_to_page_1_size_20(client_with_mock_store):
    # Arrange
    client, store = client_with_mock_store

    # Act
    response = client.get("/api/summaries")

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert body == {"items": [{"session_id": "a"}], "total": 1, "page": 1, "size": 20}
    store.list.assert_awaited_once_with({}, 0, 20)


def test_list_summaries_should_forward_filters(client_with_mock_store):
    # Arrange
    client, store = client_with_mock_store

    # Act
    response = client.get(
        "/api/summaries",
        params={"page": 2, "size": 5, "sentiment": "positive", "resolved": "true", "q": "card", "from": "2026-01-01", "to": "2026-12-31"},
    )

    # Assert
    assert response.status_code == 200
    call = store.list.await_args
    filters = call.args[0]
    assert filters["sentiment"] == "positive"
    assert filters["resolved"] is True
    assert filters["q"] == "card"
    assert filters["from"] == "2026-01-01"
    assert filters["to"] == "2026-12-31"
    assert call.args[1] == 5  # skip
    assert call.args[2] == 5  # limit


def test_get_summary_should_return_record(client_with_mock_store):
    # Arrange
    client, _ = client_with_mock_store

    # Act
    response = client.get("/api/summaries/a")

    # Assert
    assert response.status_code == 200
    assert response.json()["session_id"] == "a"


def test_get_summary_should_404_when_missing(client_with_mock_store):
    # Arrange
    client, _ = client_with_mock_store

    # Act
    response = client.get("/api/summaries/missing")

    # Assert
    assert response.status_code == 404
