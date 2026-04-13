"""Tests for agent flag literal types."""


def test_stage_should_include_all_expected_stages_when_imported():
    from src.agents.flags import Stage

    # Arrange
    expected = {
        "new_session",
        "awaiting_problem",
        "collecting_identity",
        "ask_secret",
        "verifying_secret",
        "routing",
        "completed",
        "failed",
    }

    # Act
    actual = set(Stage.__args__)

    # Assert
    assert actual == expected


def test_tier_should_include_three_values_when_imported():
    from src.agents.flags import Tier

    # Act
    actual = set(Tier.__args__)

    # Assert
    assert actual == {"premium", "regular", "non_customer"}


def test_service_should_include_five_values_when_imported():
    from src.agents.flags import Service

    # Act
    actual = set(Service.__args__)

    # Assert
    assert actual == {"investments", "insurance", "loans", "cards", "general"}
