"""Tests for the LangGraph ↔ Pipecat bridge."""

import pytest
from pipecat.frames.frames import (
    InterimTranscriptionFrame,
    LLMFullResponseEndFrame,
    LLMFullResponseStartFrame,
    LLMTextFrame,
    TranscriptionFrame,
)
from pipecat.processors.frame_processor import FrameDirection

from src.schemas.api import ChatResponse
from src.voice.langgraph_bridge import LangGraphBridge


def _transcription(text: str) -> TranscriptionFrame:
    return TranscriptionFrame(text=text, user_id="u1", timestamp="2026-04-18T00:00:00Z")


async def test_should_emit_llm_frame_trio_for_finalized_transcription(mocker):
    # Arrange
    chat_service = mocker.MagicMock()
    chat_service.handle_message = mocker.AsyncMock(
        return_value=ChatResponse(response="I can help with that.", session_id="abc")
    )
    bridge = LangGraphBridge(chat_service)
    push = mocker.patch.object(bridge, "push_frame", new_callable=mocker.AsyncMock)

    # Act
    await bridge.process_frame(_transcription("I need yacht insurance"), FrameDirection.DOWNSTREAM)

    # Assert — three downstream frames in order: start, text, end
    emitted_frames = [call.args[0] for call in push.await_args_list]
    assert len(emitted_frames) == 3
    assert isinstance(emitted_frames[0], LLMFullResponseStartFrame)
    assert isinstance(emitted_frames[1], LLMTextFrame)
    assert emitted_frames[1].text == "I can help with that."
    assert isinstance(emitted_frames[2], LLMFullResponseEndFrame)


async def test_should_thread_session_id_across_turns(mocker):
    # Arrange
    chat_service = mocker.MagicMock()
    chat_service.handle_message = mocker.AsyncMock(
        side_effect=[
            ChatResponse(response="first", session_id="s-1"),
            ChatResponse(response="second", session_id="s-1"),
        ]
    )
    bridge = LangGraphBridge(chat_service)
    mocker.patch.object(bridge, "push_frame", new_callable=mocker.AsyncMock)

    # Act — two turns back-to-back
    await bridge.process_frame(_transcription("hello"), FrameDirection.DOWNSTREAM)
    await bridge.process_frame(_transcription("another question"), FrameDirection.DOWNSTREAM)

    # Assert — second call passes the session_id returned by the first
    first_call = chat_service.handle_message.await_args_list[0].args[0]
    second_call = chat_service.handle_message.await_args_list[1].args[0]
    assert first_call.session_id is None
    assert second_call.session_id == "s-1"
    assert bridge.session_id == "s-1"


async def test_should_drop_interim_transcriptions_without_calling_graph(mocker):
    # Arrange
    chat_service = mocker.MagicMock()
    chat_service.handle_message = mocker.AsyncMock()
    bridge = LangGraphBridge(chat_service)
    push = mocker.patch.object(bridge, "push_frame", new_callable=mocker.AsyncMock)

    # Act
    interim = InterimTranscriptionFrame(text="I need yach", user_id="u1", timestamp="2026-04-18T00:00:00Z")
    await bridge.process_frame(interim, FrameDirection.DOWNSTREAM)

    # Assert — interim is forwarded but the graph is NOT invoked
    chat_service.handle_message.assert_not_awaited()
    push.assert_awaited_once()
    assert push.await_args.args[0] is interim


async def test_should_skip_empty_final_transcriptions(mocker):
    # Arrange — VAD can produce an empty final when a silent window closes.
    chat_service = mocker.MagicMock()
    chat_service.handle_message = mocker.AsyncMock()
    bridge = LangGraphBridge(chat_service)
    push = mocker.patch.object(bridge, "push_frame", new_callable=mocker.AsyncMock)

    # Act
    await bridge.process_frame(_transcription("   "), FrameDirection.DOWNSTREAM)

    # Assert — no graph call, no frames emitted downstream
    chat_service.handle_message.assert_not_awaited()
    push.assert_not_awaited()


async def test_emit_assistant_text_should_push_llm_frame_trio(mocker):
    # Arrange — used by the pipeline to fire the opener without routing through STT.
    chat_service = mocker.MagicMock()
    bridge = LangGraphBridge(chat_service)
    push = mocker.patch.object(bridge, "push_frame", new_callable=mocker.AsyncMock)

    # Act
    await bridge.emit_assistant_text("Welcome to DEUS Bank.")

    # Assert
    frames = [call.args[0] for call in push.await_args_list]
    assert isinstance(frames[0], LLMFullResponseStartFrame)
    assert isinstance(frames[1], LLMTextFrame)
    assert frames[1].text == "Welcome to DEUS Bank."
    assert isinstance(frames[2], LLMFullResponseEndFrame)


async def test_emit_assistant_text_should_skip_empty_string(mocker):
    # Arrange
    chat_service = mocker.MagicMock()
    bridge = LangGraphBridge(chat_service)
    push = mocker.patch.object(bridge, "push_frame", new_callable=mocker.AsyncMock)

    # Act
    await bridge.emit_assistant_text("")

    # Assert
    push.assert_not_awaited()


@pytest.mark.parametrize(
    "text",
    ["", "  ", "\t\n"],
)
async def test_should_skip_blank_final_transcriptions(mocker, text):
    # Arrange — parametrized across empty / whitespace variants.
    chat_service = mocker.MagicMock()
    chat_service.handle_message = mocker.AsyncMock()
    bridge = LangGraphBridge(chat_service)
    mocker.patch.object(bridge, "push_frame", new_callable=mocker.AsyncMock)

    # Act
    await bridge.process_frame(_transcription(text), FrameDirection.DOWNSTREAM)

    # Assert
    chat_service.handle_message.assert_not_awaited()
