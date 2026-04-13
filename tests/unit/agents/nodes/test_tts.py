"""Tests for the tts placeholder node."""

import pytest


@pytest.mark.asyncio
async def test_tts_node_should_return_empty_dict_when_invoked():
    from src.agents.nodes.tts import tts_node

    # Arrange
    state = {"output_text": "Welcome to DEUS Bank"}

    # Act
    actual = await tts_node(state)

    # Assert
    assert actual == {}
