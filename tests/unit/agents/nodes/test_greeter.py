"""Tests for the greeter node."""

import pytest


@pytest.fixture
def mock_llm(mocker):
    from src.agents.results import IdentityExtraction

    extraction_mock = mocker.AsyncMock()
    extraction_mock.ainvoke = mocker.AsyncMock(return_value=IdentityExtraction())

    chain = mocker.MagicMock()
    chain.with_structured_output = mocker.MagicMock(return_value=extraction_mock)

    mocker.patch("src.agents.nodes.greeter.get_llm", return_value=chain)
    return extraction_mock


@pytest.mark.asyncio
async def test_greeter_node_should_advance_to_ask_secret_when_two_fields_match(mock_llm):
    from src.agents.nodes.greeter import greeter_node
    from src.agents.results import IdentityExtraction

    # Arrange
    mock_llm.ainvoke.return_value = IdentityExtraction(name="Lisa", phone="+1122334455", iban=None)
    state = {"user_message": "Hi I'm Lisa, +1122334455"}

    # Act
    actual = await greeter_node(state)

    # Assert
    assert actual["stage"] == "ask_secret"
    assert actual["verified_iban"] == "DE89370400440532013000"
    assert actual["response_phrase_key"] == "verifier_ask_secret"
    assert actual["secret_question"] == "Which is the name of my dog?"
    assert actual["retry_count"] == 0


@pytest.mark.asyncio
async def test_greeter_node_should_ask_for_more_when_only_name_provided(mock_llm):
    from src.agents.nodes.greeter import greeter_node
    from src.agents.results import IdentityExtraction

    # Arrange
    mock_llm.ainvoke.return_value = IdentityExtraction(name="Lisa")
    state = {"user_message": "I am Lisa"}

    # Act
    actual = await greeter_node(state)

    # Assert
    assert actual["response_phrase_key"] == "greeter_need_more_info"
    assert "stage" not in actual


@pytest.mark.asyncio
async def test_greeter_node_should_retry_when_nothing_extracted(mock_llm):
    from src.agents.nodes.greeter import greeter_node
    from src.agents.results import IdentityExtraction

    # Arrange
    mock_llm.ainvoke.return_value = IdentityExtraction()
    state = {"user_message": "uh...", "retry_count": 0}

    # Act
    actual = await greeter_node(state)

    # Assert
    assert actual["response_phrase_key"] == "retry_unclear_identity"
    assert actual["retry_count"] == 1
    assert "stage" not in actual


@pytest.mark.asyncio
async def test_greeter_node_should_fallback_when_retry_count_exhausted(mock_llm):
    from src.agents.nodes.greeter import greeter_node
    from src.agents.results import IdentityExtraction

    # Arrange
    mock_llm.ainvoke.return_value = IdentityExtraction()
    state = {"user_message": "", "retry_count": 1}

    # Act
    actual = await greeter_node(state)

    # Assert
    assert actual["stage"] == "failed"
    assert actual["response_phrase_key"] == "fallback_to_general"
    assert actual["retry_count"] == 2


@pytest.mark.asyncio
async def test_greeter_node_should_retry_when_two_fields_provided_but_no_match_on_first_try(
    mock_llm,
):
    from src.agents.nodes.greeter import greeter_node
    from src.agents.results import IdentityExtraction

    # Arrange — first mismatch attempt (retry_count starts at 0)
    mock_llm.ainvoke.return_value = IdentityExtraction(name="Unknown", phone="+0000000000", iban=None)
    state = {"user_message": "I'm Unknown at +0000000000"}

    # Act
    actual = await greeter_node(state)

    # Assert — give them another chance, don't advance stage
    assert actual["response_phrase_key"] == "greeter_identity_not_found"
    assert actual["retry_count"] == 1
    assert "stage" not in actual


@pytest.mark.asyncio
async def test_greeter_node_should_respond_non_customer_when_two_fields_still_dont_match_on_second_try(
    mock_llm,
):
    from src.agents.nodes.greeter import greeter_node
    from src.agents.results import IdentityExtraction

    # Arrange — second mismatch attempt
    mock_llm.ainvoke.return_value = IdentityExtraction(name="Unknown", phone="+0000000000", iban=None)
    state = {"user_message": "I'm Unknown at +0000000000", "retry_count": 1}

    # Act
    actual = await greeter_node(state)

    # Assert — non-customer response
    assert actual["stage"] == "completed"
    assert actual["response_phrase_key"] == "non_customer_response"
    assert actual["retry_count"] == 2


@pytest.mark.asyncio
async def test_greeter_node_should_accumulate_fields_across_turns(mock_llm):
    from src.agents.nodes.greeter import greeter_node
    from src.agents.results import IdentityExtraction

    # Arrange — this turn extracts phone; name was extracted previously
    mock_llm.ainvoke.return_value = IdentityExtraction(phone="+1122334455")
    state = {
        "user_message": "my number is +1122334455",
        "extracted_name": "Lisa",
    }

    # Act
    actual = await greeter_node(state)

    # Assert
    assert actual["stage"] == "ask_secret"
    assert actual["verified_iban"] == "DE89370400440532013000"


@pytest.mark.asyncio
async def test_greeter_node_should_reach_verification_with_caller_id_prefilled_phone(mock_llm):
    from src.agents.nodes.greeter import greeter_node
    from src.agents.results import IdentityExtraction

    # Arrange — phone pre-filled from caller ID; user says name
    mock_llm.ainvoke.return_value = IdentityExtraction(name="Lisa")
    state = {
        "user_message": "My name is Lisa",
        "extracted_phone": "+1122334455",
    }

    # Act
    actual = await greeter_node(state)

    # Assert
    assert actual["stage"] == "ask_secret"
    assert actual["verified_iban"] == "DE89370400440532013000"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "extracted_phone",
    [
        "3344556677",  # no + prefix (the Sophie bug)
        "+3344556677",  # canonical
        "+33 44 55 66 77",  # with spaces
        "+33-44-55-66-77",  # with dashes
        "(334) 455-6677",  # US-style formatting
    ],
)
async def test_greeter_node_should_match_sophie_regardless_of_phone_format(mock_llm, extracted_phone):
    from src.agents.nodes.greeter import greeter_node
    from src.agents.results import IdentityExtraction

    # Arrange
    mock_llm.ainvoke.return_value = IdentityExtraction(name="Sophie", phone=extracted_phone)
    state = {"user_message": f"Sophie, {extracted_phone}"}

    # Act
    actual = await greeter_node(state)

    # Assert
    assert actual["stage"] == "ask_secret"
    assert actual["verified_iban"] == "DE12500105170648489890"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "extracted_iban",
    [
        "DE89370400440532013000",  # canonical
        "DE89 3704 0044 0532 0130 00",  # with spaces (real-world format)
        "de89370400440532013000",  # lowercase
        "  DE89370400440532013000  ",  # extra whitespace
    ],
)
async def test_greeter_node_should_match_lisa_regardless_of_iban_format(mock_llm, extracted_iban):
    from src.agents.nodes.greeter import greeter_node
    from src.agents.results import IdentityExtraction

    # Arrange — name + IBAN gives 2-of-3 match
    mock_llm.ainvoke.return_value = IdentityExtraction(name="Lisa", iban=extracted_iban)
    state = {"user_message": f"I am Lisa, IBAN {extracted_iban}"}

    # Act
    actual = await greeter_node(state)

    # Assert
    assert actual["stage"] == "ask_secret"
    assert actual["verified_iban"] == "DE89370400440532013000"
