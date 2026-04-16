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


def test_chat_endpoint_should_return_audio_base64_when_graph_produces_audio(mocker):
    import base64

    from fastapi.testclient import TestClient

    from src.main import app
    from src.routers.chat import get_chat_service
    from src.services.chat import ChatService

    # Arrange
    graph = mocker.AsyncMock()
    graph.ainvoke = mocker.AsyncMock(return_value={"output_text": "Welcome", "output_audio": b"mp3-bytes"})
    snapshot = mocker.MagicMock()
    snapshot.values = {}
    graph.aget_state = mocker.AsyncMock(return_value=snapshot)
    mocker.patch("src.services.chat.build_graph", return_value=graph)

    service = ChatService()
    app.dependency_overrides[get_chat_service] = lambda: service

    try:
        client = TestClient(app)
        response = client.post("/chat", json={"message": "hi"})
    finally:
        app.dependency_overrides.clear()

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert body["audio_base64"] == base64.b64encode(b"mp3-bytes").decode("ascii")
