"""Tests for domain data models."""

import pytest


def test_customer_should_store_all_fields_when_all_provided():
    from src.models import Customer

    # Arrange / Act
    actual = Customer(
        name="Lisa",
        phone="+1122334455",
        iban="DE89370400440532013000",
        secret="Which is the name of my dog?",
        answer="Yoda",
    )

    # Assert
    assert actual.name == "Lisa"
    assert actual.phone == "+1122334455"
    assert actual.iban == "DE89370400440532013000"
    assert actual.secret == "Which is the name of my dog?"
    assert actual.answer == "Yoda"


@pytest.mark.parametrize(
    "field",
    ["name", "phone", "iban", "secret", "answer"],
)
def test_customer_should_raise_when_required_field_missing(field):
    from pydantic import ValidationError

    from src.models import Customer

    # Arrange
    fields = {
        "name": "Lisa",
        "phone": "+1122334455",
        "iban": "DE89370400440532013000",
        "secret": "Which is the name of my dog?",
        "answer": "Yoda",
    }
    del fields[field]

    # Act / Assert
    with pytest.raises(ValidationError):
        Customer(**fields)


def test_account_should_default_premium_to_false_when_not_provided():
    from src.models import Account

    # Act
    actual = Account(iban="DE89370400440532013000")

    # Assert
    assert actual.premium is False


def test_account_should_accept_premium_true_when_provided():
    from src.models import Account

    # Act
    actual = Account(iban="DE89370400440532013000", premium=True)

    # Assert
    assert actual.premium is True
