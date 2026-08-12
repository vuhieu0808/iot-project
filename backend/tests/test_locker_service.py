"""Unit tests for LockerService allocation and release logic."""

import pytest
import pytest_asyncio
from tests.in_memory_repo import InMemoryRepository
from app.services.locker_service import LockerService


@pytest_asyncio.fixture
async def test_repo():
    """Provide clean InMemoryRepository with 2 lockers for testing."""
    repo = InMemoryRepository(default_locker_count=2)
    await repo.initialize()
    return repo


@pytest.mark.asyncio
async def test_locker_assignment_and_release(test_repo):
    """Test assigning locker #1, assigning locker #2, full error on 3rd card, and releasing locker #1."""
    locker_service = LockerService(repository=test_repo)

    card1 = "CARD_USER_1"
    card2 = "CARD_USER_2"
    card3 = "CARD_USER_3"

    # 1. Assign first locker (should get locker #1)
    res1 = await locker_service.process_locker_scan(card1)
    assert res1["action"] == "assign"
    assert res1["locker_number"] == 1

    # 2. Assign second locker (should get locker #2)
    res2 = await locker_service.process_locker_scan(card2)
    assert res2["action"] == "assign"
    assert res2["locker_number"] == 2

    # 3. Third card scan -> No lockers left (capacity is 2)
    res3 = await locker_service.process_locker_scan(card3)
    assert res3["action"] == "denied"
    assert res3["locker_number"] is None

    # 4. User 1 scans card at locker area again -> Release locker #1
    res_release = await locker_service.process_locker_scan(card1)
    assert res_release["action"] == "release"
    assert res_release["locker_number"] == 1

    # 5. User 3 scans again -> Gets now-vacant locker #1
    res3_retry = await locker_service.process_locker_scan(card3)
    assert res3_retry["action"] == "assign"
    assert res3_retry["locker_number"] == 1
