"""Tests for the chat router endpoint."""

import pytest


@pytest.fixture
def mock_service(mocker):
    service = mocker.MagicMock()

    async def _handle(request):
        from src.schemas.api import ChatResponse

        return ChatResponse(
            response="Welcome",
            session_id=request.session_id or "generated-session",
        )

    service.handle_message = _handle
    return service


@pytest.fixture
def client(mock_service):
    from fastapi.testclient import TestClient

    from src.main import app
    from src.routers.chat import get_chat_service

    app.dependency_overrides[get_chat_service] = lambda: mock_service
    yield TestClient(app)
    app.dependency_overrides.clear()


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
    assert data["response"] == "Welcome"
    assert "session_id" in data


def test_chat_should_preserve_session_id_when_provided(client):
    # Arrange
    payload = {"message": "Hello", "session_id": "existing-session"}

    # Act
    actual = client.post("/chat", json=payload)

    # Assert
    assert actual.status_code == 200
    assert actual.json()["session_id"] == "existing-session"
