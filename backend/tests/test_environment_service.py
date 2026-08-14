"""Unit tests for EnvironmentService threshold checking and fan commands."""

import pytest
import pytest_asyncio
from tests.in_memory_repo import InMemoryRepository
from app.services.environment_service import EnvironmentService
from app.services.notification_service import NotificationService


class MockNotificationService(NotificationService):
    """Mock notification service for capturing sent Telegram alerts during unit tests."""

    def __init__(self):
        super().__init__()
        self.sent_alerts = []

    async def send_alert(self, message: str, force: bool = False) -> bool:
        self.sent_alerts.append(message)
        return True


@pytest_asyncio.fixture
async def test_repo():
    """Provide clean InMemoryRepository."""
    repo = InMemoryRepository()
    await repo.initialize()
    return repo


@pytest.mark.asyncio
async def test_environment_thresholds_and_fan_control(test_repo):
    """Test environment reading analysis, fan command trigger, and telegram alert generation."""
    mock_notifier = MockNotificationService()
    env_service = EnvironmentService(
        repository=test_repo,
        notification_service=mock_notifier,
        temp_threshold=32.0,
        humidity_threshold=80.0,
    )

    # 1. Normal reading (Temp: 28C, Humidity: 60%)
    res1 = await env_service.process_reading(28.0, 60.0)
    assert res1["fan_control_needed"] is False
    assert res1["fan_command"] is None
    assert env_service.fan_currently_on is False
    assert len(mock_notifier.sent_alerts) == 0

    # 2. Temperature exceeds threshold (Temp: 35C > 32C)
    res2 = await env_service.process_reading(35.0, 65.0)
    assert res2["fan_control_needed"] is True
    assert res2["fan_command"] == "on"
    assert env_service.fan_currently_on is True
    assert len(mock_notifier.sent_alerts) == 1

    # 3. Duplicate high reading -> Fan already ON, no duplicate command needed
    res3 = await env_service.process_reading(34.5, 68.0)
    assert res3["fan_control_needed"] is False
    assert res3["fan_command"] is None
    assert env_service.fan_currently_on is True

    # 4. Temperature drops back to normal (Temp: 29C <= 32C)
    res4 = await env_service.process_reading(29.0, 55.0)
    assert res4["fan_control_needed"] is True
    assert res4["fan_command"] == "off"
    assert env_service.fan_currently_on is False
    assert len(mock_notifier.sent_alerts) == 2

    # 5. Test manual set_fan_state override
    manual_reading = await env_service.set_fan_state(True, reason="Manual admin override")
    assert env_service.fan_currently_on is True
    assert manual_reading.fan_on is True


@pytest.mark.asyncio
async def test_dynamic_threshold_update(test_repo):
    """Test dynamically modifying environment thresholds and verifying new trigger points."""
    mock_notifier = MockNotificationService()
    env_service = EnvironmentService(
        repository=test_repo,
        notification_service=mock_notifier,
        temp_threshold=32.0,
        humidity_threshold=80.0,
    )

    # Initially at 30°C / 70% -> normal, fan off
    res1 = await env_service.process_reading(30.0, 70.0)
    assert res1["fan_control_needed"] is False
    assert env_service.fan_currently_on is False

    # Admin updates thresholds to 28°C / 65%
    updated = env_service.update_thresholds(temp_threshold=28.0, humidity_threshold=65.0)
    assert updated["temp_threshold"] == 28.0
    assert updated["humidity_threshold"] == 65.0
    assert env_service.get_thresholds() == {"temp_threshold": 28.0, "humidity_threshold": 65.0}

    # Now 30°C / 70% exceeds the new threshold (30 > 28) -> Fan should turn ON!
    res2 = await env_service.process_reading(30.0, 70.0)
    assert res2["fan_control_needed"] is True
    assert res2["fan_command"] == "on"
    assert env_service.fan_currently_on is True
    assert len(mock_notifier.sent_alerts) == 1

    # Admin increases threshold to 35°C / 85%
    env_service.update_thresholds(temp_threshold=35.0, humidity_threshold=85.0)

    # Next reading at 30°C / 70% is now below the new threshold (30 <= 35, 70 <= 85) -> Fan should turn OFF!
    res3 = await env_service.process_reading(30.0, 70.0)
    assert res3["fan_control_needed"] is True
    assert res3["fan_command"] == "off"
    assert env_service.fan_currently_on is False

