"""Tests for the tts node."""

import pytest


@pytest.mark.asyncio
async def test_tts_node_should_return_empty_update_when_output_text_missing(mocker):
    from src.agents.nodes import tts

    # Arrange
    synth = mocker.patch.object(tts, "synthesize_speech", mocker.AsyncMock(return_value=b""))

    # Act
    actual = await tts.tts_node({})

    # Assert
    assert actual == {}
    synth.assert_not_awaited()


@pytest.mark.asyncio
async def test_tts_node_should_populate_output_audio_when_deepgram_returns_bytes(mocker):
    from src.agents.nodes import tts

    # Arrange
    mocker.patch.object(tts, "synthesize_speech", mocker.AsyncMock(return_value=b"mp3-bytes"))

    # Act
    actual = await tts.tts_node({"output_text": "Welcome to DEUS Bank"})

    # Assert
    assert actual == {"output_audio": b"mp3-bytes"}


@pytest.mark.asyncio
async def test_tts_node_should_return_empty_update_when_deepgram_returns_empty(mocker):
    from src.agents.nodes import tts

    # Arrange
    mocker.patch.object(tts, "synthesize_speech", mocker.AsyncMock(return_value=b""))

    # Act
    actual = await tts.tts_node({"output_text": "Welcome"})

    # Assert — no output_audio, text-only flow unchanged
    assert actual == {}
