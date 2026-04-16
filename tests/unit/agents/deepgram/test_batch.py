"""Tests for the Deepgram batch STT/TTS adapters."""

import base64

import pytest


@pytest.fixture(autouse=True)
def clear_tts_cache_between_tests():
    from src.agents.deepgram.batch import clear_tts_cache

    clear_tts_cache()
    yield
    clear_tts_cache()


@pytest.mark.asyncio
async def test_transcribe_audio_should_return_empty_string_when_key_missing(mocker):
    from src.agents.deepgram import batch

    # Arrange
    mocker.patch.object(batch, "_get_client", return_value=None)

    # Act
    actual = await batch.transcribe_audio(b"\x00\x01\x02")

    # Assert
    assert actual == ""


@pytest.mark.asyncio
async def test_transcribe_audio_should_return_transcript_from_deepgram_response(mocker):
    from src.agents.deepgram import batch

    # Arrange — fake Deepgram prerecorded response
    response = mocker.MagicMock()
    response.results.channels[0].alternatives[0].transcript = "I need help with my yacht insurance"
    client = mocker.MagicMock()
    client.listen.v1.media.transcribe_file = mocker.MagicMock(return_value=response)
    mocker.patch.object(batch, "_get_client", return_value=client)

    # Act
    actual = await batch.transcribe_audio(b"raw-audio")

    # Assert
    assert actual == "I need help with my yacht insurance"
    client.listen.v1.media.transcribe_file.assert_called_once()


@pytest.mark.asyncio
async def test_transcribe_audio_should_return_empty_string_when_deepgram_errors(mocker):
    from src.agents.deepgram import batch

    # Arrange
    client = mocker.MagicMock()
    client.listen.v1.media.transcribe_file = mocker.MagicMock(side_effect=RuntimeError("boom"))
    mocker.patch.object(batch, "_get_client", return_value=client)

    # Act
    actual = await batch.transcribe_audio(b"raw-audio")

    # Assert
    assert actual == ""


@pytest.mark.asyncio
async def test_transcribe_audio_should_return_empty_string_when_transcript_is_none(mocker):
    from src.agents.deepgram import batch

    # Arrange — Deepgram returned a response but transcript field is None (empty audio)
    response = mocker.MagicMock()
    response.results.channels[0].alternatives[0].transcript = None
    client = mocker.MagicMock()
    client.listen.v1.media.transcribe_file = mocker.MagicMock(return_value=response)
    mocker.patch.object(batch, "_get_client", return_value=client)

    # Act
    actual = await batch.transcribe_audio(b"silence")

    # Assert
    assert actual == ""


@pytest.mark.asyncio
async def test_synthesize_speech_should_return_empty_bytes_when_key_missing(mocker):
    from src.agents.deepgram import batch

    # Arrange
    mocker.patch.object(batch, "_get_client", return_value=None)

    # Act
    actual = await batch.synthesize_speech("Hello there")

    # Assert
    assert actual == b""


@pytest.mark.asyncio
async def test_synthesize_speech_should_return_empty_bytes_when_text_empty(mocker):
    from src.agents.deepgram import batch

    # Arrange — even with a client, empty text should short-circuit
    client = mocker.MagicMock()
    mocker.patch.object(batch, "_get_client", return_value=client)

    # Act
    actual = await batch.synthesize_speech("")

    # Assert
    assert actual == b""
    client.speak.v1.audio.generate.assert_not_called()


@pytest.mark.asyncio
async def test_synthesize_speech_should_return_joined_audio_bytes_from_deepgram_generator(mocker):
    from src.agents.deepgram import batch

    # Arrange — generate() returns an Iterator[bytes]; we join them
    client = mocker.MagicMock()
    client.speak.v1.audio.generate = mocker.MagicMock(return_value=iter([b"chunk1", b"chunk2"]))
    mocker.patch.object(batch, "_get_client", return_value=client)

    # Act
    actual = await batch.synthesize_speech("Hello there")

    # Assert
    assert actual == b"chunk1chunk2"


@pytest.mark.asyncio
async def test_synthesize_speech_should_return_empty_bytes_when_deepgram_errors(mocker):
    from src.agents.deepgram import batch

    # Arrange
    client = mocker.MagicMock()
    client.speak.v1.audio.generate = mocker.MagicMock(side_effect=RuntimeError("boom"))
    mocker.patch.object(batch, "_get_client", return_value=client)

    # Act
    actual = await batch.synthesize_speech("Hello there")

    # Assert
    assert actual == b""


def test_decode_base64_audio_should_return_bytes_when_valid():
    from src.agents.deepgram.batch import decode_base64_audio

    # Arrange
    encoded = base64.b64encode(b"audio").decode("ascii")

    # Act
    actual = decode_base64_audio(encoded)

    # Assert
    assert actual == b"audio"


def test_decode_base64_audio_should_raise_value_error_when_invalid():
    from src.agents.deepgram.batch import decode_base64_audio

    # Act + Assert
    with pytest.raises(ValueError):
        decode_base64_audio("***not-base64***")


def test_encode_base64_audio_should_encode_bytes_to_string():
    from src.agents.deepgram.batch import encode_base64_audio

    # Arrange + Act
    actual = encode_base64_audio(b"audio")

    # Assert
    assert actual == base64.b64encode(b"audio").decode("ascii")
