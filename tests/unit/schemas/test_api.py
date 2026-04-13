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
