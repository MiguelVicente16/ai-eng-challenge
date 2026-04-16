"""Tests for the summarizer service (transcript builder + LLM call + persist)."""

import pytest


@pytest.fixture
def fake_summary_instance(mocker):
    """Return a pydantic-like object with model_dump(mode='json') producing stable output."""
    instance = mocker.MagicMock()
    instance.model_dump.return_value = {
        "summary": "Customer called about yacht insurance and was routed.",
        "sentiment": "neutral",
        "topics": ["yacht insurance"],
        "resolved": True,
    }
    return instance


def test_build_transcript_should_include_caller_name_and_tier_and_problem():
    from src.agents.summary.summarizer import build_transcript

    # Arrange
    state = {
        "caller_recognized": True,
        "known_name_hint": "Lisa",
        "tier": "premium",
        "user_problem": "I need help with my yacht insurance",
        "matched_service": "insurance",
        "stage": "completed",
    }

    # Act
    transcript = build_transcript(state)

    # Assert
    assert "Lisa" in transcript
    assert "premium" in transcript
    assert "yacht insurance" in transcript
    assert "insurance" in transcript
    assert "completed" in transcript


def test_build_transcript_should_fall_back_to_extracted_name_when_not_recognized():
    from src.agents.summary.summarizer import build_transcript

    # Arrange
    state = {
        "caller_recognized": False,
        "extracted_name": "Marco",
        "tier": "regular",
        "user_problem": "card issue",
    }

    # Act
    transcript = build_transcript(state)

    # Assert
    assert "Marco" in transcript


def test_build_transcript_should_mark_caller_as_unidentified_when_no_name():
    from src.agents.summary.summarizer import build_transcript

    # Arrange
    state = {"stage": "failed"}

    # Act
    transcript = build_transcript(state)

    # Assert
    assert "not identified" in transcript.lower()


def test_build_transcript_should_append_clarify_answer_when_different_from_problem():
    from src.agents.summary.summarizer import build_transcript

    # Arrange
    state = {
        "user_problem": "I need some credit",
        "user_message": "I want a new credit card",
        "stage": "completed",
    }

    # Act
    transcript = build_transcript(state)

    # Assert
    assert "I need some credit" in transcript
    assert "I want a new credit card" in transcript


def test_build_transcript_should_not_duplicate_message_when_same_as_problem():
    from src.agents.summary.summarizer import build_transcript

    # Arrange
    state = {
        "user_problem": "I need help",
        "user_message": "I need help",
        "stage": "completed",
    }

    # Act
    transcript = build_transcript(state)

    # Assert — problem appears exactly once
    assert transcript.count("I need help") == 1


def test_build_transcript_should_include_retry_and_clarification_signals():
    from src.agents.summary.summarizer import build_transcript

    # Arrange — a frustrated customer who hit retries and needed clarification
    state = {
        "caller_recognized": False,
        "extracted_name": "Marco",
        "tier": "regular",
        "user_problem": "credit thing",
        "user_message": "a card",
        "clarification_question": "loan or card?",
        "retry_count": 2,
        "clarify_retry_count": 1,
        "verified_iban": "DE89370400440532013000",
        "stage": "completed",
    }

    # Act
    transcript = build_transcript(state)

    # Assert — all friction signals must be visible to the LLM
    assert "loan or card?" in transcript
    assert "retry count: 2" in transcript.lower()
    assert "clarification retries: 1" in transcript.lower()
    assert "Authenticated: True" in transcript


def test_build_transcript_should_mark_unauthenticated_when_verified_iban_absent():
    from src.agents.summary.summarizer import build_transcript

    # Arrange
    state = {"stage": "failed", "extracted_name": "Alex"}

    # Act
    transcript = build_transcript(state)

    # Assert
    assert "Authenticated: False" in transcript


def test_build_record_should_mask_caller_phone_when_present(fake_summary_instance):
    from src.agents.summary.summarizer import build_record

    # Arrange
    state = {
        "tier": "premium",
        "matched_service": "insurance",
        "stage": "completed",
        "caller_phone": "+1122334455",
        "user_problem": "yacht insurance",
    }

    # Act
    record = build_record(
        thread_id="sess-1",
        state=state,
        summary=fake_summary_instance,
    )

    # Assert
    assert record["session_id"] == "sess-1"
    assert record["tier"] == "premium"
    assert record["matched_service"] == "insurance"
    assert record["stage"] == "completed"
    assert record["user_problem"] == "yacht insurance"
    assert record["metrics"] == {
        "summary": "Customer called about yacht insurance and was routed.",
        "sentiment": "neutral",
        "topics": ["yacht insurance"],
        "resolved": True,
    }
    # Phone must be masked (not the raw number)
    assert record["caller_phone_masked"] != "+1122334455"
    assert record["caller_phone_masked"] is not None
    # Timestamp is ISO-8601 UTC
    assert "T" in record["timestamp"]


def test_build_record_should_omit_caller_phone_masked_when_phone_absent(fake_summary_instance):
    from src.agents.summary.summarizer import build_record

    # Arrange
    state = {"tier": "non_customer", "stage": "completed"}

    # Act
    record = build_record(thread_id="sess-2", state=state, summary=fake_summary_instance)

    # Assert
    assert record.get("caller_phone_masked") is None


def test_build_record_should_include_metrics_schema_version(fake_summary_instance):
    from src.agents.summary.summarizer import build_record

    # Arrange
    state = {"stage": "completed"}

    # Act
    record = build_record(thread_id="sess-3", state=state, summary=fake_summary_instance)

    # Assert
    assert record["metrics_schema_version"] == 1


def test_build_record_should_call_model_dump_with_mode_json(fake_summary_instance):
    from src.agents.summary.summarizer import build_record

    # Arrange
    state = {"stage": "completed"}

    # Act
    build_record(thread_id="sess-4", state=state, summary=fake_summary_instance)

    # Assert — ensures datetimes/enums serialize safely through the JSONL writer
    fake_summary_instance.model_dump.assert_called_with(mode="json")


@pytest.mark.asyncio
async def test_generate_summary_should_invoke_llm_with_structured_output(mocker, fake_summary_instance):
    from src.agents.summary import summarizer as s

    # Arrange
    structured_llm = mocker.AsyncMock()
    structured_llm.ainvoke = mocker.AsyncMock(return_value=fake_summary_instance)
    llm = mocker.MagicMock()
    llm.with_structured_output = mocker.MagicMock(return_value=structured_llm)

    mocker.patch.object(s, "get_llm", return_value=llm)
    mocker.patch.object(s, "build_summary_prompt", return_value="SYSTEM PROMPT")
    mocker.patch.object(s, "build_summary_model", return_value=mocker.MagicMock())

    state = {
        "caller_recognized": True,
        "known_name_hint": "Lisa",
        "tier": "premium",
        "user_problem": "yacht insurance",
        "stage": "completed",
    }

    # Act
    result = await s.generate_summary(state)

    # Assert
    assert result is fake_summary_instance
    messages = structured_llm.ainvoke.await_args[0][0]
    # First message is the system prompt
    assert messages[0] == ("system", "SYSTEM PROMPT")
    # Second message is the human transcript — must mention Lisa
    assert "Lisa" in messages[1][1]


@pytest.mark.asyncio
async def test_generate_summary_should_return_none_when_llm_raises(mocker):
    from src.agents.summary import summarizer as s

    # Arrange
    structured_llm = mocker.AsyncMock()
    structured_llm.ainvoke = mocker.AsyncMock(side_effect=RuntimeError("boom"))
    llm = mocker.MagicMock()
    llm.with_structured_output = mocker.MagicMock(return_value=structured_llm)

    mocker.patch.object(s, "get_llm", return_value=llm)
    mocker.patch.object(s, "build_summary_prompt", return_value="P")
    mocker.patch.object(s, "build_summary_model", return_value=mocker.MagicMock())

    # Act
    result = await s.generate_summary({"stage": "completed"})

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_run_summarization_should_call_store_save_with_built_record(mocker, fake_summary_instance):
    from src.agents.summary import summarizer as s

    # Arrange
    mocker.patch.object(s, "generate_summary", mocker.AsyncMock(return_value=fake_summary_instance))
    store = mocker.MagicMock()
    store.save = mocker.AsyncMock()
    mocker.patch.object(s, "get_summary_store", return_value=store)

    state = {"tier": "premium", "matched_service": "insurance", "stage": "completed"}

    # Act
    await s.run_summarization("sess-1", state)

    # Assert
    store.save.assert_awaited_once()
    saved = store.save.await_args[0][0]
    assert saved["session_id"] == "sess-1"
    assert saved["metrics"]["sentiment"] == "neutral"


@pytest.mark.asyncio
async def test_run_summarization_should_not_call_store_when_llm_returned_none(mocker):
    from src.agents.summary import summarizer as s

    # Arrange
    mocker.patch.object(s, "generate_summary", mocker.AsyncMock(return_value=None))
    store = mocker.MagicMock()
    store.save = mocker.AsyncMock()
    mocker.patch.object(s, "get_summary_store", return_value=store)

    # Act
    await s.run_summarization("sess-1", {"stage": "completed"})

    # Assert
    store.save.assert_not_awaited()


@pytest.mark.asyncio
async def test_run_summarization_should_swallow_store_errors(mocker, fake_summary_instance):
    from src.agents.summary import summarizer as s

    # Arrange
    mocker.patch.object(s, "generate_summary", mocker.AsyncMock(return_value=fake_summary_instance))
    store = mocker.MagicMock()
    store.save = mocker.AsyncMock(side_effect=RuntimeError("disk full"))
    mocker.patch.object(s, "get_summary_store", return_value=store)

    # Act — should not raise
    await s.run_summarization("sess-1", {"stage": "completed"})

    # Assert
    store.save.assert_awaited_once()
