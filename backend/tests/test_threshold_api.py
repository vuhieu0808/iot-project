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

    app.state.repository = repo
    app.state.environment_service = env_service
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
