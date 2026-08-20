"""Unit tests for Admin Environment Threshold API endpoints."""

import pytest
from starlette.testclient import TestClient
from fastapi import FastAPI
from app.api.routes_admin import router as admin_router
from app.services.environment_service import EnvironmentService
from app.services.notification_service import NotificationService
from app.api.auth import create_admin_token
from tests.in_memory_repo import InMemoryRepository


@pytest.fixture
def test_app():
    """Create test FastAPI app with in-memory state."""
    app = FastAPI()
    app.include_router(admin_router)

    repo = InMemoryRepository()
    notif = NotificationService()
    env_service = EnvironmentService(
        repository=repo,
        notification_service=notif,
        temp_threshold=32.0,
        humidity_threshold=80.0,
    )

    class MockMQTTClient:
        def __init__(self):
            self.published = []
        def publish(self, topic, payload):
            self.published.append((topic, payload))

    app.state.repository = repo
    app.state.environment_service = env_service
    app.state.mqtt_client = MockMQTTClient()
    return app


@pytest.fixture
def auth_headers():
    token = create_admin_token("admin")
    return {"Authorization": f"Bearer {token}"}


def test_get_thresholds_endpoint(test_app, auth_headers):
    client = TestClient(test_app)
    response = client.get("/api/admin/environment/thresholds", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["temp_threshold"] == 32.0
    assert data["humidity_threshold"] == 80.0


def test_update_thresholds_endpoint(test_app, auth_headers):
    client = TestClient(test_app)
    payload = {
        "temp_threshold": 30.5,
        "humidity_threshold": 70.0
    }
    response = client.put("/api/admin/environment/thresholds", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["temp_threshold"] == 30.5
    assert data["humidity_threshold"] == 70.0

    # Verify service state updated
    env_service = test_app.state.environment_service
    assert env_service.temp_threshold == 30.5
    assert env_service.humidity_threshold == 70.0

    # Verify GET returns updated values
    get_res = client.get("/api/admin/environment/thresholds", headers=auth_headers)
    assert get_res.status_code == 200
    assert get_res.json()["temp_threshold"] == 30.5
    assert get_res.json()["humidity_threshold"] == 70.0


def test_threshold_unauthorized(test_app):
    client = TestClient(test_app)
    response = client.get("/api/admin/environment/thresholds")
    assert response.status_code == 401


def test_telegram_test_endpoint_unconfigured(test_app, auth_headers):
    """Test that telegram test endpoint returns 400 when bot token/chat_id are not set."""
    test_app.state.notification_service = NotificationService(bot_token=None, chat_id=None)
    client = TestClient(test_app)
    response = client.post("/api/admin/telegram/test", headers=auth_headers)
    assert response.status_code == 400
    assert "chưa được cấu hình" in response.json()["detail"]


def test_admin_fan_control_modes(test_app, auth_headers):
    """Test fan control endpoints for on, off, and auto mode."""
    client = TestClient(test_app)
    env_service = test_app.state.environment_service

    # 1. Admin turns fan ON manually
    res_on = client.post("/api/admin/environment/fan", json={"command": "on"}, headers=auth_headers)
    assert res_on.status_code == 200
    assert res_on.json()["fan_on"] is True
    assert res_on.json()["manual_mode"] is True
    assert env_service.manual_mode is True
    assert env_service.fan_currently_on is True

    # 2. Admin turns fan OFF manually
    res_off = client.post("/api/admin/environment/fan", json={"command": "off"}, headers=auth_headers)
    assert res_off.status_code == 200
    assert res_off.json()["fan_on"] is False
    assert res_off.json()["manual_mode"] is True
    assert env_service.manual_mode is True

    # 3. Admin switches to AUTO mode
    res_auto = client.post("/api/admin/environment/fan", json={"command": "auto"}, headers=auth_headers)
    assert res_auto.status_code == 200
    assert res_auto.json()["manual_mode"] is False
    assert env_service.manual_mode is False


