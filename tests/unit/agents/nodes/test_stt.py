"""Tests for the stt node."""

import pytest


@pytest.mark.asyncio
async def test_stt_node_should_pass_through_input_text_when_no_audio():
    from src.agents.nodes.stt import stt_node

    # Arrange
    state = {"input_text": "Hello, my name is Lisa"}

    # Act
    actual = await stt_node(state)

    # Assert
    assert actual == {"user_message": "Hello, my name is Lisa"}


@pytest.mark.asyncio
async def test_stt_node_should_return_empty_user_message_when_nothing_provided():
    from src.agents.nodes.stt import stt_node

    # Act
    actual = await stt_node({})

    # Assert
    assert actual == {"user_message": ""}


@pytest.mark.asyncio
async def test_stt_node_should_transcribe_audio_when_input_audio_present(mocker):
    from src.agents.nodes import stt

    # Arrange
    mocker.patch.object(stt, "transcribe_audio", mocker.AsyncMock(return_value="yacht insurance"))

    # Act
    actual = await stt.stt_node({"input_audio": b"raw-audio-bytes"})

    # Assert
    assert actual == {"user_message": "yacht insurance"}
    stt.transcribe_audio.assert_awaited_once_with(b"raw-audio-bytes")


@pytest.mark.asyncio
async def test_stt_node_should_prefer_transcription_over_input_text_when_both_given(mocker):
    from src.agents.nodes import stt

    # Arrange
    mocker.patch.object(stt, "transcribe_audio", mocker.AsyncMock(return_value="spoken words"))

    # Act
    actual = await stt.stt_node({"input_audio": b"audio", "input_text": "typed words"})

    # Assert — audio wins when both are present
    assert actual == {"user_message": "spoken words"}


@pytest.mark.asyncio
async def test_stt_node_should_fall_back_to_input_text_when_deepgram_returns_empty(mocker):
    from src.agents.nodes import stt

    # Arrange
    mocker.patch.object(stt, "transcribe_audio", mocker.AsyncMock(return_value=""))

    # Act
    actual = await stt.stt_node({"input_audio": b"audio", "input_text": "fallback text"})

    # Assert
    assert actual == {"user_message": "fallback text"}
