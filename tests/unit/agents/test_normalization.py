"""Tests for identity normalization helpers."""

import pytest


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("+1122334455", "1122334455"),
        ("1122334455", "1122334455"),
        ("+1 (122) 334-4455", "11223344455"),
        ("+33 44 55 66 77", "3344556677"),
        ("  3344556677  ", "3344556677"),
    ],
)
def test_normalize_phone_should_return_digits_only_when_valid_phone(raw, expected):
    from src.agents.normalization import normalize_phone

    # Act
    actual = normalize_phone(raw)

    # Assert
    assert actual == expected


@pytest.mark.parametrize("value", [None, ""])
def test_normalize_phone_should_return_none_when_empty(value):
    from src.agents.normalization import normalize_phone

    # Act
    actual = normalize_phone(value)

    # Assert
    assert actual is None


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("DE89370400440532013000", "DE89370400440532013000"),
        ("DE89 3704 0044 0532 0130 00", "DE89370400440532013000"),
        ("de89370400440532013000", "DE89370400440532013000"),
        ("  DE89370400440532013000  ", "DE89370400440532013000"),
        ("de89 3704 0044 0532 0130 00", "DE89370400440532013000"),
    ],
)
def test_normalize_iban_should_uppercase_and_strip_whitespace(raw, expected):
    from src.agents.normalization import normalize_iban

    # Act
    actual = normalize_iban(raw)

    # Assert
    assert actual == expected


@pytest.mark.parametrize("value", [None, ""])
def test_normalize_iban_should_return_none_when_empty(value):
    from src.agents.normalization import normalize_iban

    # Act
    actual = normalize_iban(value)

    # Assert
    assert actual is None
