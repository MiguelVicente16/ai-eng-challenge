"""Tests for the checkpointer factory."""

import pytest


@pytest.fixture(autouse=True)
def clear_factory_cache():
    from src.agents.checkpointer import get_checkpointer

    get_checkpointer.cache_clear()
    yield
    get_checkpointer.cache_clear()


def test_get_checkpointer_should_return_in_memory_saver_when_mongodb_url_not_set(mocker):
    from langgraph.checkpoint.memory import InMemorySaver

    from src.agents.checkpointer import get_checkpointer

    # Arrange
    fake_settings = mocker.MagicMock()
    fake_settings.mongodb_url = None
    fake_settings.mongodb_db_name = "deus_bank"
    mocker.patch("src.agents.checkpointer.get_settings", return_value=fake_settings)

    # Act
    actual = get_checkpointer()

    # Assert
    assert isinstance(actual, InMemorySaver)


def test_get_checkpointer_should_return_mongodb_saver_when_mongodb_url_set(mocker):
    from src.agents.checkpointer import get_checkpointer

    # Arrange
    fake_settings = mocker.MagicMock()
    fake_settings.mongodb_url = "mongodb://fake:27017"
    fake_settings.mongodb_db_name = "deus_bank"
    mocker.patch("src.agents.checkpointer.get_settings", return_value=fake_settings)

    fake_client = mocker.MagicMock()
    client_mock = mocker.patch(
        "src.agents.checkpointer.MongoClient",
        return_value=fake_client,
    )
    fake_saver = mocker.MagicMock()
    saver_mock = mocker.patch(
        "src.agents.checkpointer.MongoDBSaver",
        return_value=fake_saver,
    )

    # Act
    actual = get_checkpointer()

    # Assert
    client_mock.assert_called_once_with("mongodb://fake:27017")
    saver_mock.assert_called_once()
    assert actual is fake_saver


def test_get_checkpointer_should_pass_db_name_to_mongodb_saver(mocker):
    from src.agents.checkpointer import get_checkpointer

    # Arrange
    fake_settings = mocker.MagicMock()
    fake_settings.mongodb_url = "mongodb://fake:27017"
    fake_settings.mongodb_db_name = "my_custom_db"
    mocker.patch("src.agents.checkpointer.get_settings", return_value=fake_settings)

    mocker.patch("src.agents.checkpointer.MongoClient")
    saver_mock = mocker.patch("src.agents.checkpointer.MongoDBSaver")

    # Act
    get_checkpointer()

    # Assert — verify db_name is passed somehow (positional or kwarg)
    call = saver_mock.call_args
    passed_db_name = call.kwargs.get("db_name") if call.kwargs else None
    if passed_db_name is None and len(call.args) >= 2:
        passed_db_name = call.args[1]
    assert passed_db_name == "my_custom_db"
