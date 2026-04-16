"""Tests for the ChatService."""

import pytest


@pytest.fixture
def mock_graph(mocker):
    graph = mocker.AsyncMock()
    graph.ainvoke = mocker.AsyncMock(return_value={"output_text": "Welcome to DEUS Bank"})

    snapshot = mocker.MagicMock()
    snapshot.values = {}
    graph.aget_state = mocker.AsyncMock(return_value=snapshot)

    mocker.patch("src.services.chat.build_graph", return_value=graph)
    return graph


@pytest.mark.asyncio
async def test_handle_message_should_return_response_with_new_session_id_when_not_provided(
    mock_graph,
):
    from src.schemas.api import ChatRequest
    from src.services.chat import ChatService

    # Arrange
    service = ChatService()
    request = ChatRequest(message="Hello")

    # Act
    actual = await service.handle_message(request)

    # Assert
    assert actual.response == "Welcome to DEUS Bank"
    assert actual.session_id is not None
    assert len(actual.session_id) > 0


@pytest.mark.asyncio
async def test_handle_message_should_preserve_session_id_when_provided(mock_graph):
    from src.schemas.api import ChatRequest
    from src.services.chat import ChatService

    # Arrange
    service = ChatService()
    request = ChatRequest(message="Hello", session_id="sess-42")

    # Act
    actual = await service.handle_message(request)

    # Assert
    assert actual.session_id == "sess-42"


@pytest.mark.asyncio
async def test_handle_message_should_seed_new_session_stage_when_no_prior_state(mock_graph):
    from src.schemas.api import ChatRequest
    from src.services.chat import ChatService

    # Arrange
    service = ChatService()

    # Act
    await service.handle_message(ChatRequest(message="Hi"))

    # Assert
    inputs = mock_graph.ainvoke.await_args[0][0]
    assert inputs["stage"] == "new_session"
    assert inputs["input_text"] == "Hi"


@pytest.mark.asyncio
async def test_handle_message_should_pre_fill_state_when_caller_phone_matches_customer(
    mock_graph,
):
    from src.schemas.api import ChatRequest
    from src.services.chat import ChatService

    # Arrange
    service = ChatService()

    # Act
    await service.handle_message(ChatRequest(message="", caller_phone="+1122334455"))

    # Assert
    inputs = mock_graph.ainvoke.await_args[0][0]
    assert inputs["caller_recognized"] is True
    assert inputs["extracted_phone"] == "+1122334455"
    assert inputs["known_name_hint"] == "Lisa"


@pytest.mark.asyncio
async def test_handle_message_should_mark_caller_unrecognized_when_phone_unknown(mock_graph):
    from src.schemas.api import ChatRequest
    from src.services.chat import ChatService

    # Arrange
    service = ChatService()

    # Act
    await service.handle_message(ChatRequest(message="", caller_phone="+9999999999"))

    # Assert
    inputs = mock_graph.ainvoke.await_args[0][0]
    assert inputs["caller_recognized"] is False
    assert "extracted_phone" not in inputs
    assert "known_name_hint" not in inputs


@pytest.mark.asyncio
async def test_handle_message_should_not_override_state_on_existing_session(mock_graph, mocker):
    from src.schemas.api import ChatRequest
    from src.services.chat import ChatService

    # Arrange — snapshot has existing state
    snapshot = mocker.MagicMock()
    snapshot.values = {"stage": "ask_secret"}
    mock_graph.aget_state = mocker.AsyncMock(return_value=snapshot)
    service = ChatService()

    # Act
    await service.handle_message(ChatRequest(message="Yoda", session_id="s1"))

    # Assert — inputs contain only input_text
    inputs = mock_graph.ainvoke.await_args[0][0]
    assert "stage" not in inputs
    assert "caller_phone" not in inputs
    assert inputs["input_text"] == "Yoda"


@pytest.mark.asyncio
async def test_handle_message_should_pass_decoded_audio_bytes_to_graph(mock_graph):
    import base64

    from src.schemas.api import ChatRequest
    from src.services.chat import ChatService

    # Arrange
    service = ChatService()
    encoded = base64.b64encode(b"raw-audio").decode("ascii")

    # Act
    await service.handle_message(ChatRequest(message="", audio_base64=encoded))

    # Assert — graph received decoded bytes under input_audio
    inputs = mock_graph.ainvoke.await_args[0][0]
    assert inputs["input_audio"] == b"raw-audio"


@pytest.mark.asyncio
async def test_handle_message_should_encode_output_audio_as_base64_in_response(mock_graph, mocker):
    import base64

    from src.schemas.api import ChatRequest
    from src.services.chat import ChatService

    # Arrange — graph returns output_audio bytes
    mock_graph.ainvoke = mocker.AsyncMock(return_value={"output_text": "Hello", "output_audio": b"mp3-bytes"})
    service = ChatService()

    # Act
    actual = await service.handle_message(ChatRequest(message="Hi"))

    # Assert
    assert actual.audio_base64 == base64.b64encode(b"mp3-bytes").decode("ascii")


@pytest.mark.asyncio
async def test_handle_message_should_return_none_audio_when_graph_produces_no_audio(mock_graph):
    from src.schemas.api import ChatRequest
    from src.services.chat import ChatService

    # Arrange — default mock_graph returns only output_text
    service = ChatService()

    # Act
    actual = await service.handle_message(ChatRequest(message="Hi"))

    # Assert
    assert actual.audio_base64 is None


@pytest.mark.asyncio
async def test_handle_message_should_raise_http_400_when_audio_base64_invalid(mock_graph):
    from fastapi import HTTPException

    from src.schemas.api import ChatRequest
    from src.services.chat import ChatService

    # Arrange
    service = ChatService()

    # Act + Assert
    with pytest.raises(HTTPException) as exc_info:
        await service.handle_message(ChatRequest(message="", audio_base64="***bad***"))
    assert exc_info.value.status_code == 400
