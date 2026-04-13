"""Tests for the session_ended node."""

import pytest


@pytest.mark.asyncio
async def test_session_ended_node_should_emit_session_ended_phrase_when_stage_completed():
    from src.agents.nodes.session_ended import session_ended_node

    # Arrange
    state = {"stage": "completed"}

    # Act
    actual = await session_ended_node(state)

    # Assert
    assert actual["response_phrase_key"] == "session_ended"
    assert actual["response_variables"] == {}


@pytest.mark.asyncio
async def test_session_ended_node_should_emit_session_ended_phrase_when_stage_failed():
    from src.agents.nodes.session_ended import session_ended_node

    # Arrange
    state = {"stage": "failed"}

    # Act
    actual = await session_ended_node(state)

    # Assert
    assert actual["response_phrase_key"] == "session_ended"
