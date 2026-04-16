"""Tests for the summary metrics config loader and dynamic model builder."""

import pytest


@pytest.fixture(autouse=True)
def _reset_metrics_caches():
    from src.agents.summary import metrics as m

    m.load_summary_config.cache_clear()
    m.build_summary_model.cache_clear()
    m.build_summary_prompt.cache_clear()
    yield
    m.load_summary_config.cache_clear()
    m.build_summary_model.cache_clear()
    m.build_summary_prompt.cache_clear()


def test_load_summary_config_should_return_list_of_metric_dicts():
    from src.agents.summary.metrics import load_summary_config

    # Act
    actual = load_summary_config()

    # Assert
    names = [m["name"] for m in actual]
    assert "summary" in names
    assert "sentiment" in names
    assert "topics" in names
    assert "resolved" in names


def test_build_summary_model_should_include_all_metric_names_as_pydantic_fields():
    from src.agents.summary.metrics import build_summary_model

    # Act
    model = build_summary_model()

    # Assert
    assert set(model.model_fields.keys()) == {"summary", "sentiment", "topics", "resolved"}


def test_build_summary_model_should_accept_valid_instance_with_defaults():
    from src.agents.summary.metrics import build_summary_model

    # Act
    instance = build_summary_model()(
        summary="Customer called about yacht insurance and was routed.",
        sentiment="neutral",
        topics=["yacht insurance"],
        resolved=True,
    )

    # Assert
    assert instance.sentiment == "neutral"
    assert instance.topics == ["yacht insurance"]
    assert instance.resolved is True


def test_build_summary_model_should_reject_invalid_enum_value():
    from pydantic import ValidationError

    from src.agents.summary.metrics import build_summary_model

    # Act + Assert
    with pytest.raises(ValidationError):
        build_summary_model()(
            summary="x",
            sentiment="ecstatic",
            topics=["x"],
            resolved=True,
        )


def test_build_summary_model_should_reject_string_over_max_length():
    from pydantic import ValidationError

    from src.agents.summary.metrics import build_summary_model

    # Act + Assert
    with pytest.raises(ValidationError):
        build_summary_model()(
            summary="x" * 501,
            sentiment="neutral",
            topics=["x"],
            resolved=True,
        )


def test_build_summary_prompt_should_describe_all_metrics():
    from src.agents.summary.metrics import build_summary_prompt

    # Act
    prompt = build_summary_prompt()

    # Assert
    assert "summary" in prompt
    assert "sentiment" in prompt
    assert "positive" in prompt and "neutral" in prompt and "negative" in prompt
    assert "topics" in prompt
    assert "resolved" in prompt


def test_build_summary_model_should_support_integer_type(mocker):
    from src.agents.summary import metrics as m

    # Arrange — swap the config loader to return an integer metric
    mocker.patch.object(
        m,
        "load_summary_config",
        return_value=[
            {
                "name": "urgency",
                "type": "integer",
                "min": 1,
                "max": 5,
                "description": "Urgency score from 1 to 5.",
            }
        ],
    )
    m.build_summary_model.cache_clear()

    # Act
    model = m.build_summary_model()

    # Assert
    assert model(urgency=3).urgency == 3


def test_build_summary_model_should_support_number_type(mocker):
    from src.agents.summary import metrics as m

    # Arrange
    mocker.patch.object(
        m,
        "load_summary_config",
        return_value=[{"name": "satisfaction", "type": "number", "min": 0.0, "max": 1.0, "description": "x"}],
    )
    m.build_summary_model.cache_clear()

    # Act
    model = m.build_summary_model()

    # Assert
    assert model(satisfaction=0.75).satisfaction == 0.75


def test_build_summary_model_should_raise_when_metric_type_unsupported(mocker):
    from src.agents.summary import metrics as m

    # Arrange
    mocker.patch.object(
        m,
        "load_summary_config",
        return_value=[{"name": "bad", "type": "dict", "description": "x"}],
    )
    m.build_summary_model.cache_clear()

    # Act + Assert
    with pytest.raises(ValueError, match="unsupported metric type"):
        m.build_summary_model()


def test_build_summary_model_should_raise_when_enum_values_empty(mocker):
    from src.agents.summary import metrics as m

    # Arrange
    mocker.patch.object(
        m,
        "load_summary_config",
        return_value=[{"name": "bad", "type": "enum", "values": [], "description": "x"}],
    )
    m.build_summary_model.cache_clear()

    # Act + Assert
    with pytest.raises(ValueError, match="non-empty 'values'"):
        m.build_summary_model()
