"""Tests for the /voice WebSocket router.

The router itself is a thin shim: accept, gate on Deepgram key, hand off to
`run_voice_pipeline`. Pipeline internals (Pipecat wiring, Deepgram, LangGraph
bridge) are covered in `tests/unit/voice/` — here we only prove the shim's
two branches.
"""

import pytest
from fastapi.testclient import TestClient


def test_voice_endpoint_should_close_with_1011_when_deepgram_key_missing(mocker):
    # Arrange
    from src.main import app
    from src.routers import voice

    mocker.patch.object(voice, "get_deepgram_client", return_value=None)

    # Act + Assert — the server closes the socket after accept; reading raises.
    client = TestClient(app)
    with pytest.raises(Exception):  # noqa: B017 — starlette raises WebSocketDisconnect
        with client.websocket_connect("/voice") as ws:
            ws.receive_text()


def test_voice_endpoint_should_delegate_to_run_voice_pipeline_when_configured(mocker):
    # Arrange
    from src.main import app
    from src.routers import voice
    from src.routers.chat import get_chat_service

    mocker.patch.object(voice, "get_deepgram_client", return_value=object())

    # Close the socket from inside the stub so the client-side context manager
    # can exit cleanly instead of hanging on an open WS.
    async def _close_ws(ws, _cs):
        await ws.close()

    run_pipeline = mocker.patch.object(
        voice,
        "run_voice_pipeline",
        new_callable=mocker.AsyncMock,
        side_effect=_close_ws,
    )

    chat_service = mocker.MagicMock()
    app.dependency_overrides[get_chat_service] = lambda: chat_service

    try:
        client = TestClient(app)
        with client.websocket_connect("/voice"):
            pass
    finally:
        app.dependency_overrides.clear()

    # Assert — the shim calls run_voice_pipeline once with our chat_service.
    run_pipeline.assert_awaited_once()
    _ws_arg, cs_arg = run_pipeline.await_args.args
    assert cs_arg is chat_service


def test_voice_endpoint_should_log_and_swallow_pipeline_failures(mocker, caplog):
    # Arrange
    from src.main import app
    from src.routers import voice
    from src.routers.chat import get_chat_service

    mocker.patch.object(voice, "get_deepgram_client", return_value=object())
    mocker.patch.object(
        voice,
        "run_voice_pipeline",
        new_callable=mocker.AsyncMock,
        side_effect=RuntimeError("boom"),
    )

    chat_service = mocker.MagicMock()
    app.dependency_overrides[get_chat_service] = lambda: chat_service

    try:
        client = TestClient(app)
        # The server swallows the RuntimeError and the WS is torn down.
        with pytest.raises(Exception):  # noqa: B017
            with client.websocket_connect("/voice") as ws:
                ws.receive_text()
    finally:
        app.dependency_overrides.clear()

    assert any("pipeline failed" in record.message for record in caplog.records)
