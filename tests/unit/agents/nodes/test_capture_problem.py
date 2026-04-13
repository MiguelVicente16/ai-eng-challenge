"""Tests for the capture_problem node."""

import pytest


@pytest.fixture(autouse=True)
def clear_cache_between_tests():
    from src.agents.intent_cache import clear

    clear()
    yield
    clear()


@pytest.fixture
def mock_classify(mocker):
    from src.agents.results import ServiceClassification

    async def _fake(_problem: str) -> ServiceClassification:
        return ServiceClassification(decision="route", service="insurance", reasoning="yacht")

    return mocker.patch(
        "src.agents.nodes.capture_problem.classify_service",
        side_effect=_fake,
    )


@pytest.mark.asyncio
async def test_capture_problem_should_store_problem_and_advance_when_message_meaningful(
    mock_classify,
):
    from src.agents.nodes.capture_problem import capture_problem_node

    # Arrange
    state = {"user_message": "I need help with my yacht insurance"}
    config = {"configurable": {"thread_id": "t1"}}

    # Act
    actual = await capture_problem_node(state, config)

    # Assert
    assert actual["user_problem"] == "I need help with my yacht insurance"
    assert actual["stage"] == "collecting_identity"
    assert actual["retry_count"] == 0
    assert actual["response_phrase_key"] == "auth_kickoff_unknown_caller"


@pytest.mark.asyncio
async def test_capture_problem_should_pick_known_caller_kickoff_when_recognized(mock_classify):
    from src.agents.nodes.capture_problem import capture_problem_node

    # Arrange
    state = {"user_message": "yacht insurance help", "caller_recognized": True}
    config = {"configurable": {"thread_id": "t2"}}

    # Act
    actual = await capture_problem_node(state, config)

    # Assert
    assert actual["response_phrase_key"] == "auth_kickoff_known_caller"


@pytest.mark.asyncio
async def test_capture_problem_should_retry_when_message_too_short(mock_classify):
    from src.agents.nodes.capture_problem import capture_problem_node

    # Arrange
    state = {"user_message": "uh", "retry_count": 0}
    config = {"configurable": {"thread_id": "t3"}}

    # Act
    actual = await capture_problem_node(state, config)

    # Assert
    assert actual["response_phrase_key"] == "retry_unclear_problem"
    assert actual["retry_count"] == 1
    assert "stage" not in actual


@pytest.mark.asyncio
async def test_capture_problem_should_fallback_when_retry_count_reaches_max(mock_classify):
    from src.agents.nodes.capture_problem import capture_problem_node

    # Arrange
    state = {"user_message": "", "retry_count": 1}
    config = {"configurable": {"thread_id": "t4"}}

    # Act
    actual = await capture_problem_node(state, config)

    # Assert
    assert actual["stage"] == "failed"
    assert actual["response_phrase_key"] == "fallback_to_general"
    assert actual["retry_count"] == 2


@pytest.mark.asyncio
async def test_capture_problem_should_register_task_in_intent_cache_on_success(mock_classify):
    from src.agents.intent_cache import pop_classification
    from src.agents.nodes.capture_problem import capture_problem_node

    # Arrange
    state = {"user_message": "I want to discuss my investment portfolio"}
    config = {"configurable": {"thread_id": "t5"}}

    # Act
    await capture_problem_node(state, config)
    classification = await pop_classification("t5")

    # Assert
    assert classification is not None
    assert classification.service == "insurance"  # from mock
