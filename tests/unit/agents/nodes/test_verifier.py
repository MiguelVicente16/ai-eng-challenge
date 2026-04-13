"""Tests for the verifier node."""

import pytest


@pytest.fixture
def mock_llm(mocker):
    from src.agents.results import SecretAnswer

    answer_mock = mocker.AsyncMock()
    answer_mock.ainvoke = mocker.AsyncMock(return_value=SecretAnswer())

    chain = mocker.MagicMock()
    chain.with_structured_output = mocker.MagicMock(return_value=answer_mock)

    mocker.patch("src.agents.nodes.verifier.get_llm", return_value=chain)
    return answer_mock


@pytest.mark.asyncio
async def test_verifier_node_should_advance_to_routing_when_answer_matches(mock_llm):
    from src.agents.nodes.verifier import verifier_node
    from src.agents.results import SecretAnswer

    # Arrange
    mock_llm.ainvoke.return_value = SecretAnswer(answer="Yoda")
    state = {
        "verified_iban": "DE89370400440532013000",
        "user_message": "Yoda",
    }

    # Act
    actual = await verifier_node(state)

    # Assert
    assert actual["stage"] == "routing"
    assert actual["response_phrase_key"] == "verifier_success"
    assert actual["retry_count"] == 0


@pytest.mark.asyncio
async def test_verifier_node_should_retry_when_answer_wrong(mock_llm):
    from src.agents.nodes.verifier import verifier_node
    from src.agents.results import SecretAnswer

    # Arrange
    mock_llm.ainvoke.return_value = SecretAnswer(answer="Rex")
    state = {
        "verified_iban": "DE89370400440532013000",
        "user_message": "Rex",
        "retry_count": 0,
    }

    # Act
    actual = await verifier_node(state)

    # Assert
    assert actual["response_phrase_key"] == "retry_unclear_secret"
    assert actual["retry_count"] == 1
    assert "stage" not in actual


@pytest.mark.asyncio
async def test_verifier_node_should_fallback_when_retry_exhausted(mock_llm):
    from src.agents.nodes.verifier import verifier_node
    from src.agents.results import SecretAnswer

    # Arrange
    mock_llm.ainvoke.return_value = SecretAnswer(answer="Rex")
    state = {
        "verified_iban": "DE89370400440532013000",
        "user_message": "Rex again",
        "retry_count": 1,
    }

    # Act
    actual = await verifier_node(state)

    # Assert
    assert actual["stage"] == "failed"
    assert actual["response_phrase_key"] == "fallback_to_general"
    assert actual["retry_count"] == 2


@pytest.mark.asyncio
async def test_verifier_node_should_accept_case_and_whitespace_variations(mock_llm):
    from src.agents.nodes.verifier import verifier_node
    from src.agents.results import SecretAnswer

    # Arrange
    mock_llm.ainvoke.return_value = SecretAnswer(answer="  yoda  ")
    state = {
        "verified_iban": "DE89370400440532013000",
        "user_message": "yoda",
    }

    # Act
    actual = await verifier_node(state)

    # Assert
    assert actual["stage"] == "routing"


@pytest.mark.asyncio
async def test_verifier_node_should_fallback_when_customer_not_found(mock_llm):
    from src.agents.nodes.verifier import verifier_node

    # Arrange
    state = {
        "verified_iban": "DE99999999999999999999",
        "user_message": "whatever",
    }

    # Act
    actual = await verifier_node(state)

    # Assert
    assert actual["stage"] == "failed"
    assert actual["response_phrase_key"] == "fallback_to_general"


@pytest.mark.asyncio
async def test_verifier_node_should_find_customer_when_verified_iban_has_spaces(mock_llm):
    from src.agents.nodes.verifier import verifier_node
    from src.agents.results import SecretAnswer

    # Arrange — verified_iban stored with spaces
    mock_llm.ainvoke.return_value = SecretAnswer(answer="Yoda")
    state = {
        "verified_iban": "DE89 3704 0044 0532 0130 00",
        "user_message": "Yoda",
    }

    # Act
    actual = await verifier_node(state)

    # Assert
    assert actual["stage"] == "routing"
