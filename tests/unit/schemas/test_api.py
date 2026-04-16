"""Tests for API request/response schemas."""


def test_chat_request_should_store_message_and_session_id_when_provided():
    from src.schemas.api import ChatRequest

    # Act
    actual = ChatRequest(message="Hello", session_id="abc-123")

    # Assert
    assert actual.message == "Hello"
    assert actual.session_id == "abc-123"


def test_chat_request_should_default_session_id_to_none_when_omitted():
    from src.schemas.api import ChatRequest

    # Act
    actual = ChatRequest(message="Hello")

    # Assert
    assert actual.session_id is None


def test_chat_response_should_store_response_and_session_id_when_provided():
    from src.schemas.api import ChatResponse

    # Act
    actual = ChatResponse(response="Hi there!", session_id="sess-42")

    # Assert
    assert actual.response == "Hi there!"
    assert actual.session_id == "sess-42"


def test_chat_request_should_accept_caller_phone_when_provided():
    from src.schemas.api import ChatRequest

    # Act
    actual = ChatRequest(message="Hi", caller_phone="+1122334455")

    # Assert
    assert actual.caller_phone == "+1122334455"


def test_chat_request_should_default_caller_phone_to_none_when_omitted():
    from src.schemas.api import ChatRequest

    # Act
    actual = ChatRequest(message="Hi")

    # Assert
    assert actual.caller_phone is None


def test_chat_request_should_accept_audio_base64_field():
    from src.schemas.api import ChatRequest

    # Act
    actual = ChatRequest(message="", audio_base64="YWJjZA==")

    # Assert
    assert actual.audio_base64 == "YWJjZA=="


def test_chat_response_should_accept_optional_audio_base64_field():
    from src.schemas.api import ChatResponse

    # Act
    actual = ChatResponse(response="Hello", session_id="s1", audio_base64="YWJjZA==")

    # Assert
    assert actual.audio_base64 == "YWJjZA=="


def test_chat_response_should_default_audio_base64_to_none():
    from src.schemas.api import ChatResponse

    # Act
    actual = ChatResponse(response="Hello", session_id="s1")

    # Assert
    assert actual.audio_base64 is None


def test_chat_request_should_default_message_to_empty_string():
    from src.schemas.api import ChatRequest

    # Act — client sending only audio
    actual = ChatRequest(audio_base64="YWJjZA==")

    # Assert
    assert actual.message == ""
