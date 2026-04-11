"""Tests for LLM structured output schemas."""


def test_extracted_identity_should_default_all_fields_to_none():
    from src.schemas.llm import ExtractedIdentity

    # Act
    actual = ExtractedIdentity()

    # Assert
    assert actual.name is None
    assert actual.phone is None
    assert actual.iban is None


def test_extracted_identity_should_store_partial_fields_when_provided():
    from src.schemas.llm import ExtractedIdentity

    # Act
    actual = ExtractedIdentity(name="Lisa", phone="+1122334455")

    # Assert
    assert actual.name == "Lisa"
    assert actual.phone == "+1122334455"
    assert actual.iban is None


def test_extracted_secret_should_default_answer_to_none():
    from src.schemas.llm import ExtractedSecret

    # Act
    actual = ExtractedSecret()

    # Assert
    assert actual.answer is None


def test_extracted_secret_should_store_answer_when_provided():
    from src.schemas.llm import ExtractedSecret

    # Act
    actual = ExtractedSecret(answer="Yoda")

    # Assert
    assert actual.answer == "Yoda"


def test_user_intent_should_store_intent_and_summary():
    from src.schemas.llm import UserIntent

    # Act
    actual = UserIntent(intent="provide_identity", summary="User gave their name and phone")

    # Assert
    assert actual.intent == "provide_identity"
    assert actual.summary == "User gave their name and phone"
