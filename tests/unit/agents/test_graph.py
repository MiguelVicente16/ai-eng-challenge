"""Integration tests for the full LangGraph assembly."""

import pytest


@pytest.fixture(autouse=True)
def clear_build_graph_cache_and_intent_cache():
    from src.agents.graph import build_graph
    from src.agents.intent_cache import clear

    build_graph.cache_clear()
    clear()
    yield
    build_graph.cache_clear()
    clear()


@pytest.fixture
def mock_all_llms(mocker):
    """Mock get_llm() in every node that uses it."""
    from src.agents.results import IdentityExtraction, SecretAnswer, ServiceClassification

    identity_mock = mocker.AsyncMock()
    identity_mock.ainvoke = mocker.AsyncMock(return_value=IdentityExtraction())
    identity_chain = mocker.MagicMock()
    identity_chain.with_structured_output = mocker.MagicMock(return_value=identity_mock)

    secret_mock = mocker.AsyncMock()
    secret_mock.ainvoke = mocker.AsyncMock(return_value=SecretAnswer())
    secret_chain = mocker.MagicMock()
    secret_chain.with_structured_output = mocker.MagicMock(return_value=secret_mock)

    service_mock = mocker.AsyncMock()
    service_mock.ainvoke = mocker.AsyncMock(
        return_value=ServiceClassification(decision="route", service="general", reasoning="default")
    )
    service_chain = mocker.MagicMock()
    service_chain.with_structured_output = mocker.MagicMock(return_value=service_mock)

    mocker.patch("src.agents.nodes.greeter.get_llm", return_value=identity_chain)
    mocker.patch("src.agents.nodes.verifier.get_llm", return_value=secret_chain)
    mocker.patch("src.agents.nodes.specialist.get_llm", return_value=service_chain)

    return {"identity": identity_mock, "secret": secret_mock, "service": service_mock}


@pytest.mark.asyncio
async def test_build_graph_should_compile_without_error():
    from src.agents.graph import build_graph

    # Act
    actual = build_graph()

    # Assert
    assert actual is not None


@pytest.mark.asyncio
async def test_graph_should_emit_unknown_opener_on_new_session(mock_all_llms):
    from src.agents.graph import build_graph

    # Arrange
    graph = build_graph()
    config = {"configurable": {"thread_id": "t-new"}}

    # Act
    actual = await graph.ainvoke(
        {"input_text": "", "stage": "new_session"},
        config=config,
    )

    # Assert
    assert "DEUS Bank" in actual["output_text"]
    assert "how can i help" in actual["output_text"].lower()


@pytest.mark.asyncio
async def test_graph_should_personalize_opener_when_caller_recognized(mock_all_llms):
    from src.agents.graph import build_graph

    # Arrange
    graph = build_graph()
    config = {"configurable": {"thread_id": "t-known"}}

    # Act
    actual = await graph.ainvoke(
        {
            "input_text": "",
            "stage": "new_session",
            "caller_recognized": True,
            "known_name_hint": "Lisa",
        },
        config=config,
    )

    # Assert
    assert "Lisa" in actual["output_text"]


@pytest.mark.asyncio
async def test_graph_should_reach_premium_response_for_lisa_across_turns(mock_all_llms):
    from src.agents.graph import build_graph
    from src.agents.results import IdentityExtraction, SecretAnswer, ServiceClassification

    # Arrange
    graph = build_graph()
    config = {"configurable": {"thread_id": "t-premium"}}

    # Turn 1: opener (new_session)
    await graph.ainvoke({"input_text": "", "stage": "new_session"}, config=config)

    # Turn 2: capture problem
    mock_all_llms["service"].ainvoke.return_value = ServiceClassification(
        decision="route", service="investments", reasoning="portfolio"
    )
    await graph.ainvoke({"input_text": "I want to talk about my portfolio"}, config=config)

    # Turn 3: greeter extracts Lisa + phone → ask_secret
    mock_all_llms["identity"].ainvoke.return_value = IdentityExtraction(name="Lisa", phone="+1122334455")
    await graph.ainvoke({"input_text": "Hi I'm Lisa, +1122334455"}, config=config)

    # Turn 4: verifier confirms secret → bouncer → specialist
    mock_all_llms["secret"].ainvoke.return_value = SecretAnswer(answer="Yoda")
    actual = await graph.ainvoke({"input_text": "Yoda"}, config=config)

    # Assert
    assert actual["tier"] == "premium"
    assert actual["matched_service"] == "investments"
    assert "Lisa" in actual["output_text"]
    assert "+1999888001" in actual["output_text"]


@pytest.mark.asyncio
async def test_graph_should_fallback_on_retry_exhaustion_in_capture_problem(mock_all_llms):
    from src.agents.graph import build_graph

    # Arrange
    graph = build_graph()
    config = {"configurable": {"thread_id": "t-fail"}}

    # Turn 1: opener
    await graph.ainvoke({"input_text": "", "stage": "new_session"}, config=config)

    # Turn 2: unclear problem (retry 1)
    first = await graph.ainvoke({"input_text": "uh"}, config=config)
    assert "didn't catch" in first["output_text"]

    # Turn 3: still unclear → retry exhausted → fallback
    second = await graph.ainvoke({"input_text": ""}, config=config)

    # Assert
    assert second["stage"] == "failed"
    assert "general support" in second["output_text"].lower()


@pytest.mark.asyncio
async def test_graph_should_emit_session_ended_phrase_on_new_turn_after_completion(mock_all_llms):
    from src.agents.graph import build_graph
    from src.agents.results import IdentityExtraction, SecretAnswer, ServiceClassification

    # Arrange — walk through a full successful flow for Lisa
    graph = build_graph()
    config = {"configurable": {"thread_id": "t-aftercomplete"}}

    await graph.ainvoke({"input_text": "", "stage": "new_session"}, config=config)

    mock_all_llms["service"].ainvoke.return_value = ServiceClassification(
        decision="route", service="investments", reasoning="portfolio"
    )
    await graph.ainvoke({"input_text": "I want to talk about my portfolio"}, config=config)

    mock_all_llms["identity"].ainvoke.return_value = IdentityExtraction(name="Lisa", phone="+1122334455")
    await graph.ainvoke({"input_text": "Hi I'm Lisa, +1122334455"}, config=config)

    mock_all_llms["secret"].ainvoke.return_value = SecretAnswer(answer="Yoda")
    completion = await graph.ainvoke({"input_text": "Yoda"}, config=config)
    assert completion["stage"] == "completed"

    # Act — new turn on a completed session
    actual = await graph.ainvoke({"input_text": "thanks!"}, config=config)

    # Assert
    assert "This call has ended" in actual["output_text"]


@pytest.mark.asyncio
async def test_graph_should_route_clarifying_stage_directly_to_specialist(mocker):
    from src.agents.graph import build_graph
    from src.agents.intent_cache import clear
    from src.agents.results import ServiceClassification

    # Arrange — force a route on the second classification
    clear()
    build_graph.cache_clear()

    classify = mocker.AsyncMock(
        return_value=ServiceClassification(decision="route", service="cards", reasoning="credit card")
    )
    mocker.patch("src.agents.nodes.specialist.classify_service", classify)

    graph = build_graph()
    config = {"configurable": {"thread_id": "t-clar-graph"}}
    await graph.aupdate_state(
        config,
        {
            "stage": "clarifying",
            "tier": "regular",
            "extracted_name": "Marco",
            "user_problem": "I need some credit",
            "clarification_question": "loan or card?",
            "clarify_retry_count": 1,
        },
    )

    # Act
    result = await graph.ainvoke({"input_text": "I want a new credit card"}, config=config)

    # Assert
    assert result["matched_service"] == "cards"
    assert result["stage"] == "completed"


@pytest.mark.asyncio
async def test_graph_should_ask_clarify_and_route_on_answer(mocker):
    from src.agents.graph import build_graph
    from src.agents.intent_cache import clear
    from src.agents.results import ServiceClassification

    # Arrange — two classify calls: first clarifies, second routes
    clear()
    build_graph.cache_clear()

    classify = mocker.AsyncMock(
        side_effect=[
            ServiceClassification(
                decision="clarify",
                clarification="Are you asking about a loan or a credit card?",
                reasoning="ambiguous",
            ),
            ServiceClassification(decision="route", service="cards", reasoning="card"),
        ]
    )
    mocker.patch("src.agents.nodes.specialist.classify_service", classify)
    mocker.patch("src.agents.nodes.capture_problem.classify_service", classify)

    graph = build_graph()
    config = {"configurable": {"thread_id": "t-clar-e2e"}}

    # Seed a verified premium session directly at the routing stage
    await graph.aupdate_state(
        config,
        {
            "stage": "routing",
            "tier": "premium",
            "verified_iban": "DE89370400440532013000",
            "extracted_name": "Lisa",
            "user_problem": "I need some credit",
            "clarify_retry_count": 0,
        },
    )

    # Act — turn A: specialist emits clarify
    turn_a = await graph.ainvoke({"input_text": ""}, config=config)

    # Assert — turn A
    assert turn_a["response_phrase_key"] == "specialist_clarify"
    assert "loan or a credit card" in turn_a["output_text"]

    # Act — turn B: user answers, specialist routes to cards
    turn_b = await graph.ainvoke({"input_text": "I want a new credit card"}, config=config)

    # Assert — turn B
    assert turn_b["matched_service"] == "cards"
    assert turn_b["stage"] == "completed"
