"""Tests for agent structured output result models."""

import pytest


def test_identity_extraction_should_default_all_fields_to_none():
    from src.agents.results import IdentityExtraction

    # Act
    actual = IdentityExtraction()

    # Assert
    assert actual.name is None
    assert actual.phone is None
    assert actual.iban is None


def test_identity_extraction_should_store_fields_when_provided():
    from src.agents.results import IdentityExtraction

    # Act
    actual = IdentityExtraction(name="Lisa", phone="+1122334455", iban=None)

    # Assert
    assert actual.name == "Lisa"
    assert actual.phone == "+1122334455"
    assert actual.iban is None


def test_secret_answer_should_default_answer_to_none():
    from src.agents.results import SecretAnswer

    # Act
    actual = SecretAnswer()

    # Assert
    assert actual.answer is None


def test_secret_answer_should_store_answer_when_provided():
    from src.agents.results import SecretAnswer

    # Act
    actual = SecretAnswer(answer="Yoda")

    # Assert
    assert actual.answer == "Yoda"


def test_service_classification_should_store_route_decision_with_service():
    from src.agents.results import ServiceClassification

    # Act
    actual = ServiceClassification(
        decision="route",
        service="investments",
        reasoning="portfolio question",
    )

    # Assert
    assert actual.decision == "route"
    assert actual.service == "investments"
    assert "portfolio" in actual.reasoning


def test_service_classification_should_default_service_to_none_when_omitted():
    from src.agents.results import ServiceClassification

    # Act
    actual = ServiceClassification(decision="escalate", reasoning="wants human")

    # Assert
    assert actual.decision == "escalate"
    assert actual.service is None


@pytest.mark.parametrize("decision", ["escalate", "none"])
def test_service_classification_should_accept_non_route_decision_without_service(decision):
    from src.agents.results import ServiceClassification

    # Act
    actual = ServiceClassification(decision=decision, reasoning="needs routing to general")

    # Assert
    assert actual.decision == decision
    assert actual.service is None


@pytest.mark.parametrize("bad_decision", ["maybe", "", "unclear", "clarify"])
def test_service_classification_should_raise_when_decision_not_in_literal(bad_decision):
    from pydantic import ValidationError

    from src.agents.results import ServiceClassification

    # Act / Assert
    with pytest.raises(ValidationError):
        ServiceClassification(decision=bad_decision, reasoning="x")


def test_service_classification_should_raise_when_reasoning_exceeds_max_length():
    from pydantic import ValidationError

    from src.agents.results import ServiceClassification

    # Arrange — 101 chars, one over the limit
    too_long = "x" * 101

    # Act / Assert
    with pytest.raises(ValidationError):
        ServiceClassification(decision="none", reasoning=too_long)
