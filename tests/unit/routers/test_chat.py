"""Tests for the chat router endpoint."""

import pytest


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from src.main import app

    return TestClient(app)


def test_health_should_return_ok(client):
    # Act
    actual = client.get("/health")

    # Assert
    assert actual.status_code == 200
    assert actual.json() == {"status": "ok"}


def test_chat_should_return_200_with_response_and_session_id(client):
    # Arrange
    payload = {"message": "Hello"}

    # Act
    actual = client.post("/chat", json=payload)

    # Assert
    assert actual.status_code == 200
    data = actual.json()
    assert "response" in data
    assert "session_id" in data
    assert isinstance(data["session_id"], str)
    assert len(data["session_id"]) > 0


def test_chat_should_preserve_session_id_when_provided(client):
    # Arrange
    payload = {"message": "Hello", "session_id": "existing-session"}

    # Act
    actual = client.post("/chat", json=payload)

    # Assert
    assert actual.status_code == 200
    assert actual.json()["session_id"] == "existing-session"
