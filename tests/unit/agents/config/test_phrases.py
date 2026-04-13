"""Tests for phrase catalog loader and renderer."""

import pytest


def test_load_phrases_should_return_dict_with_opener_when_loaded():
    from src.agents.config.phrases import load_phrases

    # Act
    actual = load_phrases()

    # Assert
    assert isinstance(actual, dict)
    assert "opener_unknown_caller" in actual
    assert "DEUS Bank" in actual["opener_unknown_caller"]


def test_load_phrases_should_include_all_expected_keys():
    from src.agents.config.phrases import load_phrases

    # Arrange
    expected_keys = {
        "opener_known_caller",
        "opener_unknown_caller",
        "auth_kickoff_known_caller",
        "auth_kickoff_unknown_caller",
        "greeter_need_more_info",
        "greeter_identity_not_found",
        "verifier_ask_secret",
        "verifier_success",
        "retry_unclear_problem",
        "retry_unclear_identity",
        "retry_unclear_secret",
        "fallback_to_general",
        "premium_response",
        "regular_response",
        "non_customer_response",
        "guardrails_fallback",
        "session_ended",
    }

    # Act
    actual = set(load_phrases().keys())

    # Assert
    assert expected_keys.issubset(actual)


def test_render_should_interpolate_variables_when_provided():
    from src.agents.config.phrases import render

    # Act
    actual = render(
        "premium_response",
        {"name": "Lisa", "service_label": "investments", "dept_phone": "+1999888999"},
    )

    # Assert
    assert "Lisa" in actual
    assert "+1999888999" in actual
    assert "investments" in actual


def test_render_should_raise_key_error_when_phrase_unknown():
    from src.agents.config.phrases import render

    # Act / Assert
    with pytest.raises(KeyError):
        render("nonexistent_key", {})


def test_render_should_raise_key_error_when_variable_missing():
    from src.agents.config.phrases import render

    # Act / Assert
    with pytest.raises(KeyError):
        render("premium_response", {"name": "Lisa"})


def test_render_should_work_without_variables_when_phrase_has_none():
    from src.agents.config.phrases import render

    # Act
    actual = render("opener_unknown_caller", None)

    # Assert
    assert "DEUS Bank" in actual
