"""Unit tests for AccessService and membership verification."""

import pytest
import pytest_asyncio
from datetime import date, timedelta
from app.models.member import Member
from app.models.check_log import AccessStatus, AccessAction
from tests.in_memory_repo import InMemoryRepository
from app.services.access_service import AccessService
from app.services.occupancy_service import OccupancyService


@pytest_asyncio.fixture
async def test_repo():
    """Provide clean InMemoryRepository for testing."""
    repo = InMemoryRepository(default_locker_count=5)
    await repo.initialize()
    return repo


@pytest.mark.asyncio
async def test_access_service_valid_checkin_checkout(test_repo):
    """Test full valid member check-in, occupancy increment, checkout, and workout duration calculation."""
    access_service = AccessService(repository=test_repo)
    occupancy_service = OccupancyService(repository=test_repo)

    # 1. Seed valid member
    card_id = "CARD_VALID_01"
    future_date = date.today() + timedelta(days=30)
    member = Member(
        card_id=card_id,
        name="Nguyen Van A",
        email="a@example.com",
        membership_expiry=future_date,
        is_active=True,
    )
    await test_repo.save_member(member)

    # Occupancy before scan should be 0
    occ = await occupancy_service.get_current_occupancy()
    assert occ == 0

    # 2. First scan -> Check-in
    res1 = await access_service.verify_card_scan(card_id)
    assert res1["status"] == AccessStatus.GRANTED.value
    assert res1["action"] == AccessAction.CHECKIN.value
    assert res1["member_name"] == "Nguyen Van A"

    # Occupancy after check-in should be 1
    occ = await occupancy_service.get_current_occupancy()
    assert occ == 1

    # 3. Second scan -> Check-out
    res2 = await access_service.verify_card_scan(card_id)
    assert res2["status"] == AccessStatus.GRANTED.value
    assert res2["action"] == AccessAction.CHECKOUT.value
    assert res2["duration_minutes"] is not None
    assert res2["duration_minutes"] >= 0.0

    # Occupancy after check-out should return to 0
    occ = await occupancy_service.get_current_occupancy()
    assert occ == 0


@pytest.mark.asyncio
async def test_access_service_expired_member(test_repo):
    """Test expired membership card scan returns DENIED."""
    access_service = AccessService(repository=test_repo)

    card_id = "CARD_EXPIRED_01"
    past_date = date.today() - timedelta(days=5)
    member = Member(
        card_id=card_id,
        name="Tran Van B",
        membership_expiry=past_date,
        is_active=True,
    )
    await test_repo.save_member(member)

    res = await access_service.verify_card_scan(card_id)
    assert res["status"] == AccessStatus.DENIED.value
    assert "expired" in res["reason"].lower()


@pytest.mark.asyncio
async def test_access_service_unknown_card(test_repo):
    """Test unknown card scan returns DENIED."""
    access_service = AccessService(repository=test_repo)

    res = await access_service.verify_card_scan("CARD_UNKNOWN_99")
    assert res["status"] == AccessStatus.DENIED.value
    assert res["member_name"] == "Unknown"
