"""Tests for the summarizer graph node (fire-and-forget)."""

import asyncio

import pytest


@pytest.mark.asyncio
async def test_summarizer_node_should_return_summary_fired_true_when_stage_completed(mocker):
    from src.agents.nodes import summarizer as node_mod
    from src.agents.summary import summarizer as svc

    # Arrange
    mocker.patch.object(svc, "run_summarization", mocker.AsyncMock())
    state = {"stage": "completed", "tier": "premium"}
    config = {"configurable": {"thread_id": "sess-1"}}

    # Act
    result = await node_mod.summarizer_node(state, config)
    await asyncio.sleep(0)  # let the scheduled task run

    # Assert
    assert result == {"summary_fired": True}
    svc.run_summarization.assert_awaited_once()
    called_thread_id = svc.run_summarization.await_args[0][0]
    assert called_thread_id == "sess-1"


@pytest.mark.asyncio
async def test_summarizer_node_should_return_summary_fired_true_when_stage_failed(mocker):
    from src.agents.nodes import summarizer as node_mod
    from src.agents.summary import summarizer as svc

    # Arrange
    mocker.patch.object(svc, "run_summarization", mocker.AsyncMock())
    state = {"stage": "failed"}
    config = {"configurable": {"thread_id": "sess-2"}}

    # Act
    result = await node_mod.summarizer_node(state, config)
    await asyncio.sleep(0)

    # Assert
    assert result == {"summary_fired": True}
    svc.run_summarization.assert_awaited_once()


@pytest.mark.asyncio
async def test_summarizer_node_should_noop_when_stage_not_terminal(mocker):
    from src.agents.nodes import summarizer as node_mod
    from src.agents.summary import summarizer as svc

    # Arrange
    mocker.patch.object(svc, "run_summarization", mocker.AsyncMock())
    state = {"stage": "collecting_identity"}
    config = {"configurable": {"thread_id": "sess-3"}}

    # Act
    result = await node_mod.summarizer_node(state, config)
    await asyncio.sleep(0)

    # Assert
    assert result == {}
    svc.run_summarization.assert_not_awaited()


@pytest.mark.asyncio
async def test_summarizer_node_should_noop_when_summary_already_fired(mocker):
    from src.agents.nodes import summarizer as node_mod
    from src.agents.summary import summarizer as svc

    # Arrange
    mocker.patch.object(svc, "run_summarization", mocker.AsyncMock())
    state = {"stage": "completed", "summary_fired": True}
    config = {"configurable": {"thread_id": "sess-4"}}

    # Act
    result = await node_mod.summarizer_node(state, config)
    await asyncio.sleep(0)

    # Assert
    assert result == {}
    svc.run_summarization.assert_not_awaited()
