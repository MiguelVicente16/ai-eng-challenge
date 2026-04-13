"""Tests for routing rules loader."""

import pytest


def test_load_routing_rules_should_return_all_five_services():
    from src.agents.config.routing import load_routing_rules

    # Arrange
    expected = {"investments", "insurance", "loans", "cards", "general"}

    # Act
    actual = set(load_routing_rules().keys())

    # Assert
    assert actual == expected


def test_load_routing_rules_should_include_label_and_dept_phone_for_each_service():
    from src.agents.config.routing import load_routing_rules

    # Act
    actual = load_routing_rules()

    # Assert
    for name, meta in actual.items():
        assert "label" in meta, f"{name} missing label"
        assert "dept_phone" in meta, f"{name} missing dept_phone"


def test_get_service_metadata_should_return_label_and_dept_phone_when_known():
    from src.agents.config.routing import get_service_metadata

    # Act
    actual = get_service_metadata("investments")

    # Assert
    assert actual["label"] == "Investments"
    assert actual["dept_phone"].startswith("+")


def test_get_service_metadata_should_raise_when_unknown():
    from src.agents.config.routing import get_service_metadata

    # Act / Assert
    with pytest.raises(KeyError):
        get_service_metadata("spaceships")  # type: ignore[arg-type]


def test_build_rules_prompt_should_include_all_service_names():
    from src.agents.config.routing import build_rules_prompt

    # Act
    actual = build_rules_prompt()

    # Assert
    for service in ("investments", "insurance", "loans", "cards", "general"):
        assert service in actual


def test_build_rules_prompt_should_include_yes_and_no_rule_markers():
    from src.agents.config.routing import build_rules_prompt

    # Act
    actual = build_rules_prompt()

    # Assert
    assert "Route HERE when:" in actual
    assert "Do NOT route here when:" in actual
