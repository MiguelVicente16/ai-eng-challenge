"""Tests for admin API pydantic shapes."""

import pytest


def test_services_config_should_accept_valid_routing_shape():
    from src.schemas.admin import ServicesConfig

    # Arrange
    data = {
        "services": {
            "investments": {
                "label": "Investments",
                "dept_phone": "+1999888001",
                "yes_rules": ["rule A"],
                "no_rules": [],
            }
        }
    }

    # Act
    parsed = ServicesConfig.model_validate(data)

    # Assert
    assert parsed.services["investments"].label == "Investments"


def test_services_config_should_reject_missing_dept_phone():
    from pydantic import ValidationError

    from src.schemas.admin import ServicesConfig

    # Arrange
    bad = {"services": {"x": {"label": "X", "yes_rules": [], "no_rules": []}}}

    # Act + Assert
    with pytest.raises(ValidationError):
        ServicesConfig.model_validate(bad)


def test_phrases_config_should_accept_mapping_of_strings():
    from src.schemas.admin import PhrasesConfig

    # Arrange + Act
    parsed = PhrasesConfig.model_validate({"phrases": {"opener_known_caller": "Hi {name}"}})

    # Assert
    assert parsed.phrases["opener_known_caller"] == "Hi {name}"


def test_metrics_config_should_accept_all_six_types():
    from src.schemas.admin import MetricsConfig

    # Arrange
    data = {
        "metrics": [
            {"name": "summary", "type": "string", "max_length": 500, "description": "d"},
            {"name": "sentiment", "type": "enum", "values": ["positive", "neutral"], "description": "d"},
            {"name": "topics", "type": "list", "item_type": "string", "max_items": 5, "description": "d"},
            {"name": "resolved", "type": "boolean", "description": "d"},
            {"name": "score", "type": "integer", "min": 0, "max": 10, "description": "d"},
            {"name": "confidence", "type": "number", "min": 0, "max": 1, "description": "d"},
        ]
    }

    # Act
    parsed = MetricsConfig.model_validate(data)

    # Assert
    assert len(parsed.metrics) == 6


def test_metrics_config_should_reject_enum_without_values():
    from pydantic import ValidationError

    from src.schemas.admin import MetricsConfig

    # Arrange
    bad = {"metrics": [{"name": "x", "type": "enum", "description": "d"}]}

    # Act + Assert
    with pytest.raises(ValidationError):
        MetricsConfig.model_validate(bad)
