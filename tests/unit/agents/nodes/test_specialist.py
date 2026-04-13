"""Tests for the specialist node."""

import pytest


@pytest.fixture(autouse=True)
def clear_cache():
    from src.agents.intent_cache import clear

    clear()
    yield
    clear()


@pytest.fixture
def mock_llm(mocker):
    from src.agents.results import ServiceClassification

    classify_mock = mocker.AsyncMock()
    classify_mock.ainvoke = mocker.AsyncMock(
        return_value=ServiceClassification(
            decision="route",
            service="investments",
            reasoning="Customer asked about portfolio",
        )
    )

    chain = mocker.MagicMock()
    chain.with_structured_output = mocker.MagicMock(return_value=classify_mock)

    mocker.patch("src.agents.nodes.specialist.get_llm", return_value=chain)
    return classify_mock


@pytest.mark.asyncio
async def test_specialist_node_should_return_non_customer_response_when_tier_is_non_customer(
    mock_llm,
):
    from src.agents.nodes.specialist import specialist_node

    # Arrange
    state = {"tier": "non_customer"}
    config = {"configurable": {"thread_id": "t-nc"}}

    # Act
    actual = await specialist_node(state, config)

    # Assert
    assert actual["response_phrase_key"] == "non_customer_response"
    assert actual["stage"] == "completed"


@pytest.mark.asyncio
async def test_specialist_node_should_use_cached_classification_when_present():
    import asyncio

    from src.agents.intent_cache import start_classification
    from src.agents.nodes.specialist import specialist_node
    from src.agents.results import ServiceClassification

    # Arrange
    async def _cached() -> ServiceClassification:
        return ServiceClassification(decision="route", service="insurance", reasoning="yacht")

    start_classification("t-cache", asyncio.create_task(_cached()))

    state = {
        "tier": "premium",
        "extracted_name": "Lisa",
        "user_problem": "yacht insurance help",
    }
    config = {"configurable": {"thread_id": "t-cache"}}

    # Act
    actual = await specialist_node(state, config)

    # Assert
    assert actual["matched_service"] == "insurance"
    assert actual["response_phrase_key"] == "premium_response"
    assert actual["response_variables"]["service_label"] == "Insurance"


@pytest.mark.asyncio
async def test_specialist_node_should_fall_back_to_sync_classification_when_cache_empty(mock_llm):
    from src.agents.nodes.specialist import specialist_node

    # Arrange
    state = {
        "tier": "regular",
        "extracted_name": "Marco",
        "user_problem": "I need help with my portfolio",
    }
    config = {"configurable": {"thread_id": "t-sync"}}

    # Act
    actual = await specialist_node(state, config)

    # Assert
    assert actual["matched_service"] == "investments"
    assert actual["response_phrase_key"] == "regular_response"
    mock_llm.ainvoke.assert_awaited_once()


@pytest.mark.asyncio
async def test_specialist_node_should_use_user_problem_not_user_message_when_classifying(mock_llm):
    from src.agents.nodes.specialist import specialist_node

    # Arrange — user_message is the secret answer; user_problem is the real problem
    state = {
        "tier": "premium",
        "extracted_name": "Lisa",
        "user_message": "Yoda",
        "user_problem": "I need help with a mortgage",
    }
    config = {"configurable": {"thread_id": "t-prob"}}

    # Act
    await specialist_node(state, config)

    # Assert — the LLM was called with user_problem, not user_message
    messages = mock_llm.ainvoke.await_args[0][0]
    human_content = messages[1][1]
    assert human_content == "I need help with a mortgage"


@pytest.mark.asyncio
async def test_specialist_node_should_route_to_general_when_decision_is_escalate():
    import asyncio

    from src.agents.intent_cache import start_classification
    from src.agents.nodes.specialist import specialist_node
    from src.agents.results import ServiceClassification

    # Arrange — user asked for a human operator
    async def _cached() -> ServiceClassification:
        return ServiceClassification(decision="escalate", reasoning="wants human")

    start_classification("t-esc", asyncio.create_task(_cached()))

    state = {
        "tier": "premium",
        "extracted_name": "Lisa",
        "user_problem": "I want to talk to a person",
    }
    config = {"configurable": {"thread_id": "t-esc"}}

    # Act
    actual = await specialist_node(state, config)

    # Assert
    assert actual["matched_service"] == "general"
    assert actual["response_phrase_key"] == "premium_response"
    assert actual["response_variables"]["service_label"] == "General Support"


@pytest.mark.asyncio
async def test_specialist_node_should_route_to_general_when_decision_is_none():
    import asyncio

    from src.agents.intent_cache import start_classification
    from src.agents.nodes.specialist import specialist_node
    from src.agents.results import ServiceClassification

    # Arrange — off-topic request
    async def _cached() -> ServiceClassification:
        return ServiceClassification(decision="none", reasoning="off topic")

    start_classification("t-none", asyncio.create_task(_cached()))

    state = {
        "tier": "regular",
        "extracted_name": "Marco",
        "user_problem": "What's the weather?",
    }
    config = {"configurable": {"thread_id": "t-none"}}

    # Act
    actual = await specialist_node(state, config)

    # Assert
    assert actual["matched_service"] == "general"
    assert actual["response_phrase_key"] == "regular_response"
