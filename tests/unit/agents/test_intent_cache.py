"""Tests for the intent classification cache."""

import asyncio

import pytest


@pytest.fixture(autouse=True)
def clear_cache_between_tests():
    from src.agents.intent_cache import clear

    clear()
    yield
    clear()


@pytest.mark.asyncio
async def test_pop_classification_should_return_none_when_no_task_registered():
    from src.agents.intent_cache import pop_classification

    # Act
    actual = await pop_classification("missing-thread")

    # Assert
    assert actual is None


@pytest.mark.asyncio
async def test_pop_classification_should_return_result_when_task_completes_successfully():
    from src.agents.intent_cache import pop_classification, start_classification
    from src.agents.results import ServiceClassification

    # Arrange
    async def _classify() -> ServiceClassification:
        return ServiceClassification(decision="route", service="insurance", reasoning="yacht")

    start_classification("t1", asyncio.create_task(_classify()))

    # Act
    actual = await pop_classification("t1")

    # Assert
    assert actual is not None
    assert actual.service == "insurance"


@pytest.mark.asyncio
async def test_pop_classification_should_return_none_when_task_raises():
    from src.agents.intent_cache import pop_classification, start_classification

    # Arrange
    async def _broken() -> None:
        raise RuntimeError("boom")

    start_classification("t2", asyncio.create_task(_broken()))

    # Act
    actual = await pop_classification("t2")

    # Assert
    assert actual is None


@pytest.mark.asyncio
async def test_pop_classification_should_remove_task_from_cache_after_pop():
    from src.agents.intent_cache import pop_classification, start_classification
    from src.agents.results import ServiceClassification

    # Arrange
    async def _classify() -> ServiceClassification:
        return ServiceClassification(decision="route", service="cards", reasoning="card stuff")

    start_classification("t3", asyncio.create_task(_classify()))

    # Act
    first = await pop_classification("t3")
    second = await pop_classification("t3")

    # Assert
    assert first is not None
    assert second is None
