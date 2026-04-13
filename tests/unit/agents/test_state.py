"""Tests for the AgentState TypedDict."""


def test_agent_state_should_accept_empty_dict_when_initialized():
    from src.agents.state import AgentState

    # Act
    actual: AgentState = {}

    # Assert
    assert actual == {}


def test_agent_state_should_store_stage_when_set():
    from src.agents.state import AgentState

    # Act
    actual: AgentState = {"stage": "need_identity"}

    # Assert
    assert actual["stage"] == "need_identity"


def test_agent_state_should_store_identity_fields_when_set():
    from src.agents.state import AgentState

    # Act
    actual: AgentState = {
        "extracted_name": "Lisa",
        "extracted_phone": "+1122334455",
        "extracted_iban": None,
    }

    # Assert
    assert actual["extracted_name"] == "Lisa"
    assert actual["extracted_phone"] == "+1122334455"
    assert actual["extracted_iban"] is None


def test_agent_state_should_store_response_phrase_key_and_variables():
    from src.agents.state import AgentState

    # Act
    actual: AgentState = {
        "response_phrase_key": "premium_response",
        "response_variables": {"name": "Lisa", "dept_phone": "+1999888001"},
    }

    # Assert
    assert actual["response_phrase_key"] == "premium_response"
    assert actual["response_variables"]["name"] == "Lisa"


def test_agent_state_should_store_user_problem_and_caller_fields_when_set():
    from src.agents.state import AgentState

    # Act
    actual: AgentState = {
        "user_problem": "I need help with my yacht insurance",
        "caller_phone": "+1122334455",
        "known_name_hint": "Lisa",
        "caller_recognized": True,
    }

    # Assert
    assert actual["user_problem"] == "I need help with my yacht insurance"
    assert actual["caller_phone"] == "+1122334455"
    assert actual["known_name_hint"] == "Lisa"
    assert actual["caller_recognized"] is True


def test_agent_state_should_store_retry_count_when_set():
    from src.agents.state import AgentState

    # Act
    actual: AgentState = {"retry_count": 2}

    # Assert
    assert actual["retry_count"] == 2
