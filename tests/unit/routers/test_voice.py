"""Tests for the /voice WebSocket router."""

import json

import pytest
from fastapi.testclient import TestClient


def test_voice_endpoint_should_close_with_1011_when_deepgram_key_missing(mocker):
    from src.main import app
    from src.routers import voice

    # Arrange
    mocker.patch.object(voice, "_flux_available", return_value=False)

    # Act + Assert — the server closes the socket after accept, which raises on receive
    client = TestClient(app)
    with pytest.raises(Exception):  # noqa: B017 — starlette raises WebSocketDisconnect
        with client.websocket_connect("/voice") as ws:
            ws.receive_text()


def test_voice_endpoint_should_run_chat_service_on_each_end_of_turn(mocker):
    from src.main import app
    from src.routers import voice
    from src.routers.chat import get_chat_service
    from src.schemas.api import ChatResponse

    # Arrange — stub FluxSession to yield one turn then close
    class FakeSession:
        def __init__(self, **kwargs):
            self.closed = False

        async def start(self):
            return None

        def send_audio(self, chunk):
            pass

        async def events(self):
            yield {"type": "turn", "transcript": "I need yacht insurance"}

        async def close(self):
            self.closed = True

    mocker.patch.object(voice, "FluxSession", FakeSession)
    mocker.patch.object(voice, "_flux_available", return_value=True)
    mocker.patch.object(voice, "synthesize_speech", mocker.AsyncMock(return_value=b""))

    chat_service = mocker.MagicMock()
    chat_service.handle_message = mocker.AsyncMock(
        return_value=ChatResponse(
            response="Routing you to Insurance",
            session_id="s-1",
            audio_base64=None,
        )
    )
    app.dependency_overrides[get_chat_service] = lambda: chat_service

    try:
        client = TestClient(app)
        with client.websocket_connect("/voice") as ws:
            ws.send_bytes(b"\x00\x00")  # a fake audio frame
            ws.send_text("__end__")
            frame = ws.receive_text()
            # Drain until the server closes
            try:
                while True:
                    ws.receive_text()
            except Exception:  # noqa: BLE001
                pass
    finally:
        app.dependency_overrides.clear()

    # Assert
    payload = json.loads(frame)
    assert payload["type"] == "turn"
    assert payload["transcript"] == "I need yacht insurance"
    assert payload["response"] == "Routing you to Insurance"
    chat_service.handle_message.assert_awaited_once()


def test_voice_endpoint_should_stream_tts_audio_binary_frame_when_synthesized(mocker):
    from src.main import app
    from src.routers import voice
    from src.routers.chat import get_chat_service
    from src.schemas.api import ChatResponse

    # Arrange
    class FakeSession:
        def __init__(self, **kwargs):
            pass

        async def start(self):
            return None

        def send_audio(self, chunk):
            pass

        async def events(self):
            yield {"type": "turn", "transcript": "help"}

        async def close(self):
            return None

    mocker.patch.object(voice, "FluxSession", FakeSession)
    mocker.patch.object(voice, "_flux_available", return_value=True)
    mocker.patch.object(voice, "synthesize_speech", mocker.AsyncMock(return_value=b"mp3-chunk"))

    chat_service = mocker.MagicMock()
    chat_service.handle_message = mocker.AsyncMock(return_value=ChatResponse(response="hello", session_id="s-2"))
    app.dependency_overrides[get_chat_service] = lambda: chat_service

    try:
        client = TestClient(app)
        with client.websocket_connect("/voice") as ws:
            ws.send_text("__end__")
            ws.receive_text()  # JSON turn payload
            audio_frame = ws.receive_bytes()  # MP3 binary frame
            try:
                while True:
                    ws.receive_text()
            except Exception:  # noqa: BLE001
                pass
    finally:
        app.dependency_overrides.clear()

    assert audio_frame == b"mp3-chunk"
