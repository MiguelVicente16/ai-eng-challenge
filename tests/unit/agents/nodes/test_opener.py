"""Tests for the opener node."""

import pytest


@pytest.mark.asyncio
async def test_opener_node_should_pick_known_caller_phrase_when_recognized():
    from src.agents.nodes.opener import opener_node

    # Arrange
    state = {"caller_recognized": True, "known_name_hint": "Lisa"}

    # Act
    actual = await opener_node(state)

    # Assert
    assert actual["response_phrase_key"] == "opener_known_caller"
    assert actual["response_variables"] == {"name": "Lisa"}
    assert actual["stage"] == "awaiting_problem"
    assert actual["retry_count"] == 0


@pytest.mark.asyncio
async def test_opener_node_should_pick_unknown_caller_phrase_when_not_recognized():
    from src.agents.nodes.opener import opener_node

    # Arrange
    state = {}

    # Act
    actual = await opener_node(state)

    # Assert
    assert actual["response_phrase_key"] == "opener_unknown_caller"
    assert actual["response_variables"] == {}
    assert actual["stage"] == "awaiting_problem"


@pytest.mark.asyncio
async def test_opener_node_should_pick_unknown_phrase_when_recognized_but_name_missing():
    from src.agents.nodes.opener import opener_node

    # Arrange
    state = {"caller_recognized": True}

    # Act
    actual = await opener_node(state)

    # Assert
    assert actual["response_phrase_key"] == "opener_unknown_caller"
