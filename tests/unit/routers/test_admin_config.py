"""Tests for /api/config/* routes."""

import pytest
import yaml
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def client_with_temp_configs(tmp_path, monkeypatch):
    """Spin a FastAPI app with the admin_config router pointed at a temp dir."""
    # Arrange — temp copies of the three YAML files
    routing = tmp_path / "routing_rules.yaml"
    phrases = tmp_path / "phrases.yaml"
    metrics = tmp_path / "summary_metrics.yaml"

    routing.write_text(
        yaml.safe_dump(
            {"services": {"general": {"label": "General", "dept_phone": "+1999", "yes_rules": ["a"], "no_rules": []}}}
        )
    )
    phrases.write_text(yaml.safe_dump({"opener": "Hi"}))
    metrics.write_text(yaml.safe_dump({"metrics": [{"name": "summary", "type": "string", "description": "d"}]}))

    monkeypatch.setattr("src.routers.admin_config.ROUTING_PATH", routing)
    monkeypatch.setattr("src.routers.admin_config.PHRASES_PATH", phrases)
    monkeypatch.setattr("src.routers.admin_config.METRICS_PATH", metrics)

    from src.routers.admin_config import router

    app = FastAPI()
    app.include_router(router, prefix="/api")
    return TestClient(app), routing, phrases, metrics


def test_get_routing_should_return_current_yaml_as_json(client_with_temp_configs):
    # Arrange
    client, _, _, _ = client_with_temp_configs

    # Act
    response = client.get("/api/config/routing")

    # Assert
    assert response.status_code == 200
    assert response.json()["services"]["general"]["label"] == "General"


def test_put_routing_should_write_yaml_and_return_updated_shape(client_with_temp_configs):
    # Arrange
    client, routing_path, _, _ = client_with_temp_configs
    payload = {"services": {"cards": {"label": "Cards", "dept_phone": "+1555", "yes_rules": ["r1"], "no_rules": []}}}

    # Act
    response = client.put("/api/config/routing", json=payload)

    # Assert
    assert response.status_code == 200
    assert "cards" in response.json()["services"]
    on_disk = yaml.safe_load(routing_path.read_text())
    assert "cards" in on_disk["services"]


def test_put_routing_should_reject_invalid_shape(client_with_temp_configs):
    # Arrange
    client, _, _, _ = client_with_temp_configs
    bad = {"services": {"x": {"label": "X"}}}  # missing dept_phone

    # Act
    response = client.put("/api/config/routing", json=bad)

    # Assert
    assert response.status_code == 422


def test_put_routing_should_bust_load_routing_rules_cache(client_with_temp_configs, mocker):
    # Arrange
    client, _, _, _ = client_with_temp_configs
    bust = mocker.patch("src.routers.admin_config.load_routing_rules")

    # Act
    client.put(
        "/api/config/routing",
        json={"services": {"x": {"label": "X", "dept_phone": "+1", "yes_rules": [], "no_rules": []}}},
    )

    # Assert
    bust.cache_clear.assert_called_once()


def test_get_phrases_should_return_current_yaml(client_with_temp_configs):
    # Arrange
    client, _, _, _ = client_with_temp_configs

    # Act
    response = client.get("/api/config/phrases")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"phrases": {"opener": "Hi"}}


def test_put_phrases_should_write_and_bust_cache(client_with_temp_configs, mocker):
    # Arrange
    client, _, phrases_path, _ = client_with_temp_configs
    bust = mocker.patch("src.routers.admin_config.load_phrases")
    payload = {"phrases": {"opener": "Welcome, {name}"}}

    # Act
    response = client.put("/api/config/phrases", json=payload)

    # Assert
    assert response.status_code == 200
    on_disk = yaml.safe_load(phrases_path.read_text())
    assert on_disk == {"opener": "Welcome, {name}"}  # flat mapping on disk
    bust.cache_clear.assert_called_once()


def test_get_metrics_should_return_current_yaml(client_with_temp_configs):
    # Arrange
    client, _, _, _ = client_with_temp_configs

    # Act
    response = client.get("/api/config/metrics")

    # Assert
    assert response.status_code == 200
    assert response.json()["metrics"][0]["name"] == "summary"


def test_put_metrics_should_write_and_bust_all_three_caches(client_with_temp_configs, mocker):
    # Arrange
    client, _, _, metrics_path = client_with_temp_configs
    bust_cfg = mocker.patch("src.routers.admin_config.load_summary_config")
    bust_model = mocker.patch("src.routers.admin_config.build_summary_model")
    bust_prompt = mocker.patch("src.routers.admin_config.build_summary_prompt")
    payload = {
        "metrics": [{"name": "sentiment", "type": "enum", "values": ["positive", "negative"], "description": "d"}]
    }

    # Act
    response = client.put("/api/config/metrics", json=payload)

    # Assert
    assert response.status_code == 200
    on_disk = yaml.safe_load(metrics_path.read_text())
    assert on_disk["metrics"][0]["name"] == "sentiment"
    bust_cfg.cache_clear.assert_called_once()
    bust_model.cache_clear.assert_called_once()
    bust_prompt.cache_clear.assert_called_once()
