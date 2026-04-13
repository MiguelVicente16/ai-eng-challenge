"""Tests for the bouncer node."""

import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "iban, expected_tier",
    [
        ("DE89370400440532013000", "premium"),  # Lisa
        ("DE75512108001245126199", "regular"),  # Marco
        ("DE12500105170648489890", "premium"),  # Sophie
    ],
)
async def test_bouncer_node_should_classify_known_customer_correctly(iban, expected_tier):
    from src.agents.nodes.bouncer import bouncer_node

    # Arrange
    state = {"verified_iban": iban}

    # Act
    actual = await bouncer_node(state)

    # Assert
    assert actual["tier"] == expected_tier


@pytest.mark.asyncio
async def test_bouncer_node_should_return_non_customer_when_iban_missing():
    from src.agents.nodes.bouncer import bouncer_node

    # Arrange
    state = {}

    # Act
    actual = await bouncer_node(state)

    # Assert
    assert actual["tier"] == "non_customer"


@pytest.mark.asyncio
async def test_bouncer_node_should_return_non_customer_when_iban_unknown():
    from src.agents.nodes.bouncer import bouncer_node

    # Arrange
    state = {"verified_iban": "DE99999999999999999999"}

    # Act
    actual = await bouncer_node(state)

    # Assert
    assert actual["tier"] == "non_customer"
