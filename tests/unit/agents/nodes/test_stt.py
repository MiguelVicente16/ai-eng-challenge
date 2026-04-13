"""Tests for the stt placeholder node."""

import pytest


@pytest.mark.asyncio
async def test_stt_node_should_copy_input_text_to_user_message():
    from src.agents.nodes.stt import stt_node

    # Arrange
    state = {"input_text": "Hello, my name is Lisa"}

    # Act
    actual = await stt_node(state)

    # Assert
    assert actual == {"user_message": "Hello, my name is Lisa"}


@pytest.mark.asyncio
async def test_stt_node_should_return_empty_user_message_when_input_text_missing():
    from src.agents.nodes.stt import stt_node

    # Arrange
    state = {}

    # Act
    actual = await stt_node(state)

    # Assert
    assert actual == {"user_message": ""}
