"""Unit tests for LockerService allocation and release logic."""

import pytest
import pytest_asyncio
from datetime import date, timedelta
from app.models.member import Member
from tests.in_memory_repo import InMemoryRepository
from app.services.locker_service import LockerService


@pytest_asyncio.fixture
async def test_repo():
    """Provide clean InMemoryRepository with 2 lockers for testing."""
    repo = InMemoryRepository(default_locker_count=2)
    await repo.initialize()
    return repo


async def add_member(repo, card_id: str, name: str = "Test Member"):
    await repo.save_member(Member(
        card_id=card_id,
        name=name,
        membership_expiry=date.today() + timedelta(days=30),
    ))


@pytest.mark.asyncio
async def test_locker_assignment_and_release(test_repo):
    """Test assigning locker #1, assigning locker #2, full error on 3rd card, and releasing locker #1."""
    locker_service = LockerService(repository=test_repo)

    card1 = "CARD_USER_1"
    card2 = "CARD_USER_2"
    card3 = "CARD_USER_3"
    for card_id in (card1, card2, card3):
        await add_member(test_repo, card_id)

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

    # 4. Repeated scan opens the same locker without releasing ownership.
    res_access = await locker_service.process_locker_scan(card1)
    assert res_access["action"] == "access"
    assert res_access["locker_number"] == 1
    assert (await test_repo.get_locker(1)).is_occupied is True

    # 5. Explicit release validates ownership and makes locker #1 vacant.
    res_release = await locker_service.release_locker(card1, 1)
    assert res_release["action"] == "release"

    # 6. User 3 scans again -> Gets now-vacant locker #1
    res3_retry = await locker_service.process_locker_scan(card3)
    assert res3_retry["action"] == "assign"
    assert res3_retry["locker_number"] == 1


@pytest.mark.asyncio
async def test_broken_locker_skipped_during_assignment(test_repo):
    """Test that lockers marked BROKEN are skipped when assigning via card scan."""
    from app.models.locker import LockerStatus

    locker_service = LockerService(repository=test_repo)
    await add_member(test_repo, "CARD_USER_1")

    # Mark locker #1 as BROKEN
    await locker_service.set_locker_status(1, LockerStatus.BROKEN)

    # Scan card -> should get locker #2 (since #1 is broken)
    res = await locker_service.process_locker_scan("CARD_USER_1")
    assert res["action"] == "assign"
    assert res["locker_number"] == 2


@pytest.mark.asyncio
async def test_admin_force_operations(test_repo):
    """Test admin force_assign, force_release, and set_locker_status operations."""
    from app.models.locker import LockerStatus

    locker_service = LockerService(repository=test_repo)
    await add_member(test_repo, "CARD_ADMIN")

    # 1. Force assign CARD_ADMIN to locker #1
    assigned = await locker_service.force_assign_locker(1, "CARD_ADMIN")
    assert assigned.is_occupied is True
    assert assigned.status == LockerStatus.OCCUPIED
    assert assigned.card_id == "CARD_ADMIN"

    # 2. Force release locker #1
    released = await locker_service.force_release_locker(1)
    assert released.is_occupied is False
    assert released.status == LockerStatus.VACANT
    assert released.card_id is None

    # 3. Mark locker #1 BROKEN
    broken = await locker_service.set_locker_status(1, LockerStatus.BROKEN)
    assert broken.status == LockerStatus.BROKEN
    assert broken.is_occupied is False


@pytest.mark.asyncio
async def test_release_rejects_mismatched_locker(test_repo):
    locker_service = LockerService(repository=test_repo)
    await add_member(test_repo, "CARD_OWNER", "Locker Owner")
    assigned = await locker_service.process_locker_scan("CARD_OWNER")
    assert assigned["locker_number"] == 1

    denied = await locker_service.release_locker("CARD_OWNER", 2)
    assert denied["action"] == "denied"
    assert (await test_repo.get_locker(1)).is_occupied is True


@pytest.mark.asyncio
async def test_unknown_card_is_denied(test_repo):
    locker_service = LockerService(repository=test_repo)
    result = await locker_service.process_locker_scan("UNKNOWN_CARD")
    assert result["action"] == "denied"
    assert result["locker_number"] is None

