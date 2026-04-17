"""Tests for the Flux streaming adapter."""

import asyncio

import pytest


@pytest.mark.asyncio
async def test_flux_session_should_yield_turn_events_when_deepgram_signals_end_of_turn(mocker):
    from src.agents.deepgram.streaming import FluxSession

    # Arrange — fake Deepgram connection that records the on(...) handlers
    handlers: dict = {}

    class FakeConnection:
        def on(self, event, handler):
            handlers[event] = handler

        def send_media(self, data):
            pass

        def send_close_stream(self):
            pass

        def start_listening(self):
            pass

    fake_conn = FakeConnection()

    class FakeCtx:
        def __enter__(self):
            return fake_conn

        def __exit__(self, *args):
            return None

    listen_v2 = mocker.MagicMock()
    listen_v2.connect = mocker.MagicMock(return_value=FakeCtx())
    client = mocker.MagicMock()
    client.listen.v2 = listen_v2
    mocker.patch("src.agents.deepgram.streaming.get_deepgram_client", return_value=client)

    session = FluxSession()
    await session.start()

    async def drive():
        # Simulate Deepgram firing an EndOfTurn event on the MESSAGE callback.
        from deepgram.core.events import EventType

        result = mocker.MagicMock()
        result.event = "EndOfTurn"
        result.transcript = "I need help with my yacht insurance"
        result.turn_index = 0
        result.end_of_turn_confidence = 0.95
        handlers[EventType.MESSAGE](result)
        await asyncio.sleep(0)
        await session.close()

    # Act
    driver = asyncio.create_task(drive())
    collected = []
    async for event in session.events():
        collected.append(event)
    await driver

    # Assert
    assert any(e["type"] == "turn" and e["transcript"] == "I need help with my yacht insurance" for e in collected)


@pytest.mark.asyncio
async def test_flux_session_should_emit_interim_event_for_non_eot_messages(mocker):
    from src.agents.deepgram.streaming import FluxSession

    # Arrange
    handlers: dict = {}

    class FakeConnection:
        def on(self, event, handler):
            handlers[event] = handler

        def send_media(self, data):
            pass

        def send_close_stream(self):
            pass

        def start_listening(self):
            pass

    class FakeCtx:
        def __enter__(self):
            return FakeConnection()

        def __exit__(self, *args):
            return None

    listen_v2 = mocker.MagicMock()
    listen_v2.connect = mocker.MagicMock(return_value=FakeCtx())
    client = mocker.MagicMock()
    client.listen.v2 = listen_v2
    mocker.patch("src.agents.deepgram.streaming.get_deepgram_client", return_value=client)

    session = FluxSession()
    await session.start()

    async def drive():
        from deepgram.core.events import EventType

        result = mocker.MagicMock()
        result.event = "Update"
        result.transcript = "I need help with my"
        handlers[EventType.MESSAGE](result)
        await asyncio.sleep(0)
        await session.close()

    # Act
    driver = asyncio.create_task(drive())
    collected = []
    async for event in session.events():
        collected.append(event)
    await driver

    # Assert
    assert any(e["type"] == "interim" and e["transcript"] == "I need help with my" for e in collected)


@pytest.mark.asyncio
async def test_flux_session_should_raise_when_deepgram_key_missing(mocker):
    from src.agents.deepgram.streaming import FluxSession

    # Arrange
    mocker.patch("src.agents.deepgram.streaming.get_deepgram_client", return_value=None)

    # Act + Assert
    session = FluxSession()
    with pytest.raises(RuntimeError, match="DEEPGRAM_API_KEY"):
        await session.start()


@pytest.mark.asyncio
async def test_flux_session_send_audio_should_forward_bytes_to_connection(mocker):
    from src.agents.deepgram.streaming import FluxSession

    # Arrange
    sent_frames: list[bytes] = []
    handlers: dict = {}

    class FakeConnection:
        def on(self, event, handler):
            handlers[event] = handler

        def send_media(self, data):
            sent_frames.append(data)

        def send_close_stream(self):
            pass

        def start_listening(self):
            pass

    class FakeCtx:
        def __enter__(self):
            return FakeConnection()

        def __exit__(self, *args):
            return None

    listen_v2 = mocker.MagicMock()
    listen_v2.connect = mocker.MagicMock(return_value=FakeCtx())
    client = mocker.MagicMock()
    client.listen.v2 = listen_v2
    mocker.patch("src.agents.deepgram.streaming.get_deepgram_client", return_value=client)

    session = FluxSession()
    await session.start()

    # Act
    session.send_audio(b"\x00\x00\x01\x02")

    # Assert
    assert sent_frames == [b"\x00\x00\x01\x02"]

    # Cleanup
    await session.close()
