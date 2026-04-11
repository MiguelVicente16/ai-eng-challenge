"""Tests for the ChatService."""


def test_handle_message_should_return_response_with_new_session_when_no_session_id():
    from src.schemas.api import ChatRequest
    from src.services.chat import ChatService

    # Arrange
    service = ChatService()
    request = ChatRequest(message="Hello")

    # Act
    actual = service.handle_message(request)

    # Assert
    assert actual.response is not None
    assert len(actual.response) > 0
    assert actual.session_id is not None
    assert len(actual.session_id) > 0


def test_handle_message_should_preserve_session_id_when_provided():
    from src.schemas.api import ChatRequest
    from src.services.chat import ChatService

    # Arrange
    service = ChatService()
    request = ChatRequest(message="Hello", session_id="my-session")

    # Act
    actual = service.handle_message(request)

    # Assert
    assert actual.session_id == "my-session"


def test_handle_message_should_track_messages_in_session():
    from src.schemas.api import ChatRequest
    from src.services.chat import ChatService

    # Arrange
    service = ChatService()
    r1 = ChatRequest(message="Hi", session_id="sess-1")
    r2 = ChatRequest(message="My name is Lisa", session_id="sess-1")

    # Act
    service.handle_message(r1)
    service.handle_message(r2)
    actual = service._sessions["sess-1"]["messages"]

    # Assert
    assert len(actual) == 4  # 2 user + 2 assistant
    assert actual[0]["role"] == "user"
    assert actual[0]["content"] == "Hi"
    assert actual[2]["role"] == "user"
    assert actual[2]["content"] == "My name is Lisa"
