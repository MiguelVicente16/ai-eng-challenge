"""Tests for the responder node."""

import pytest


@pytest.mark.asyncio
async def test_responder_node_should_render_greeter_welcome_when_key_set():
    from src.agents.nodes.responder import responder_node

    # Arrange
    state = {"response_phrase_key": "greeter_welcome", "response_variables": {}}

    # Act
    actual = await responder_node(state)

    # Assert
    assert "DEUS Bank" in actual["output_text"]


@pytest.mark.asyncio
async def test_responder_node_should_interpolate_variables_into_premium_response():
    from src.agents.nodes.responder import responder_node

    # Arrange
    state = {
        "response_phrase_key": "premium_response",
        "response_variables": {
            "name": "Lisa",
            "service_label": "Investments",
            "dept_phone": "+1999888001",
        },
    }

    # Act
    actual = await responder_node(state)

    # Assert
    assert "Lisa" in actual["output_text"]
    assert "Investments" in actual["output_text"]
    assert "+1999888001" in actual["output_text"]


@pytest.mark.asyncio
async def test_responder_node_should_return_empty_text_when_no_phrase_key():
    from src.agents.nodes.responder import responder_node

    # Arrange
    state = {}

    # Act
    actual = await responder_node(state)

    # Assert
    assert actual["output_text"] == ""


@pytest.mark.asyncio
async def test_responder_node_should_fall_back_when_variables_missing():
    from src.agents.nodes.responder import responder_node

    # Arrange — premium_response needs name/service_label/dept_phone
    state = {
        "response_phrase_key": "premium_response",
        "response_variables": {},
    }

    # Act
    actual = await responder_node(state)

    # Assert — fallback phrase uses dept_phone
    assert "+1999888000" in actual["output_text"]
