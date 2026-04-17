"""Tests for /api/sessions/:id/state."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def client_with_mock_service(mocker):
    # Arrange
    graph = mocker.MagicMock()
    snapshot = mocker.MagicMock()
    snapshot.values = {"stage": "specialist", "matched_service": "cards"}

    async def _aget(config):
        if config["configurable"]["thread_id"] == "known":
            return snapshot
        empty = mocker.MagicMock()
        empty.values = {}
        return empty

    graph.aget_state = mocker.AsyncMock(side_effect=_aget)

    service = mocker.MagicMock()
    service._graph = graph
    mocker.patch("src.routers.admin_sessions.get_chat_service", return_value=service)

    from src.routers.admin_sessions import router

    app = FastAPI()
    app.include_router(router, prefix="/api")
    return TestClient(app)


def test_get_session_state_should_return_snapshot_values(client_with_mock_service):
    # Arrange
    client = client_with_mock_service

    # Act
    response = client.get("/api/sessions/known/state")

    # Assert
    assert response.status_code == 200
    assert response.json()["stage"] == "specialist"


def test_get_session_state_should_404_when_no_checkpoint(client_with_mock_service):
    # Arrange
    client = client_with_mock_service

    # Act
    response = client.get("/api/sessions/unknown/state")

    # Assert
    assert response.status_code == 404
