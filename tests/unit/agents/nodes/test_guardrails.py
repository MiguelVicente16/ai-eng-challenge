"""Tests for the guardrails node."""

import pytest


@pytest.mark.asyncio
async def test_guardrails_node_should_pass_safe_text_unchanged():
    from src.agents.nodes.guardrails import guardrails_node

    # Arrange
    state = {"output_text": "Thank you for contacting DEUS Bank, Lisa"}

    # Act
    actual = await guardrails_node(state)

    # Assert
    assert actual == {}


@pytest.mark.asyncio
async def test_guardrails_node_should_replace_output_when_it_leaks_another_customers_phone():
    from src.agents.nodes.guardrails import guardrails_node

    # Arrange — Marco's phone is in the text but Lisa is verified
    state = {
        "output_text": "Here is Marco's phone: +5566778899",
        "verified_iban": "DE89370400440532013000",  # Lisa
    }

    # Act
    actual = await guardrails_node(state)

    # Assert
    assert "+5566778899" not in actual["output_text"]
    assert "+1999888000" in actual["output_text"]


@pytest.mark.asyncio
async def test_guardrails_node_should_replace_output_when_it_leaks_an_iban():
    from src.agents.nodes.guardrails import guardrails_node

    # Arrange
    state = {
        "output_text": "Your IBAN is DE75512108001245126199",
        "verified_iban": "DE89370400440532013000",
    }

    # Act
    actual = await guardrails_node(state)

    # Assert
    assert "DE75512108001245126199" not in actual["output_text"]


@pytest.mark.asyncio
async def test_guardrails_node_should_allow_verified_customers_own_iban_in_output():
    from src.agents.nodes.guardrails import guardrails_node

    # Arrange
    state = {
        "output_text": "Confirming account ending DE89370400440532013000",
        "verified_iban": "DE89370400440532013000",
    }

    # Act
    actual = await guardrails_node(state)

    # Assert
    assert actual == {}
