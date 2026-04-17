"""Tests for app-level wiring: CORS, health, admin routers mounted."""

from fastapi.testclient import TestClient


def test_health_should_include_deepgram_and_mongo_flags():
    # Arrange
    from src.main import app

    client = TestClient(app)

    # Act
    response = client.get("/api/health")

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "deepgram" in body
    assert "mongo" in body


def test_cors_should_allow_vite_dev_origin():
    # Arrange
    from src.main import app

    client = TestClient(app)

    # Act
    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    # Assert
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_admin_routers_should_be_mounted_under_api():
    # Arrange
    from src.main import app

    paths = {r.path for r in app.routes}

    # Assert
    assert "/api/config/routing" in paths
    assert "/api/config/phrases" in paths
    assert "/api/config/metrics" in paths
    assert "/api/summaries" in paths
    assert "/api/summaries/{session_id}" in paths
    assert "/api/sessions/{session_id}/state" in paths
    assert "/api/health" in paths
