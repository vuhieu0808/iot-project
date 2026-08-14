"""InMemoryRepository for fast, isolated unit testing without external database dependencies."""

import uuid
from datetime import datetime
from typing import List, Optional, Dict

from app.models.member import Member
from app.models.locker import Locker
from app.models.environment import EnvironmentReading
from app.models.check_log import CheckLog, AccessAction, AccessStatus
from app.repositories.base import BaseRepository


class InMemoryRepository(BaseRepository):
    """In-memory implementation of BaseRepository for testing."""

    def __init__(self, default_locker_count: int = 5):
        self.default_locker_count = default_locker_count
        self.members: Dict[str, Member] = {}
        self.lockers: Dict[int, Locker] = {}
        self.check_logs: List[CheckLog] = []
        self.environment_readings: List[EnvironmentReading] = []

    async def initialize(self) -> None:
        """Seed default lockers."""
        for i in range(1, self.default_locker_count + 1):
            if i not in self.lockers:
                self.lockers[i] = Locker(locker_number=i, is_occupied=False)

    async def get_member(self, card_id: str) -> Optional[Member]:
        return self.members.get(card_id)

    async def get_all_members(self) -> List[Member]:
        return list(self.members.values())

    async def save_member(self, member: Member) -> Member:
        now_str = member.created_at or datetime.now().isoformat()
        saved = member.model_copy(update={"created_at": now_str})
        self.members[member.card_id] = saved
        return saved

    async def delete_member(self, card_id: str) -> bool:
        if card_id in self.members:
            del self.members[card_id]
            return True
        return False

    async def get_locker(self, locker_number: int) -> Optional[Locker]:
        return self.lockers.get(locker_number)

    async def get_all_lockers(self) -> List[Locker]:
        return sorted(list(self.lockers.values()), key=lambda x: x.locker_number)

    async def save_locker(self, locker: Locker) -> Locker:
        self.lockers[locker.locker_number] = locker
        return locker

    async def get_locker_by_card(self, card_id: str) -> Optional[Locker]:
        for locker in self.lockers.values():
            if locker.is_occupied and locker.card_id == card_id:
                return locker
        return None

    async def add_check_log(self, log: CheckLog) -> CheckLog:
        log_id = log.id or str(uuid.uuid4())
        timestamp_str = log.timestamp or datetime.now().isoformat()
        saved = log.model_copy(update={"id": log_id, "timestamp": timestamp_str})
        self.check_logs.append(saved)
        return saved

    async def get_check_logs(self, limit: int = 50, card_id: Optional[str] = None) -> List[CheckLog]:
        logs = [l for l in self.check_logs if not card_id or l.card_id == card_id]
        logs.sort(key=lambda x: x.timestamp or "", reverse=True)
        return logs[:limit]

    async def get_active_checkin_for_card(self, card_id: str) -> Optional[CheckLog]:
        logs = await self.get_check_logs(limit=100, card_id=card_id)
        granted_logs = [l for l in logs if l.status == AccessStatus.GRANTED]
        if not granted_logs:
            return None
        latest = granted_logs[0]
        if latest.action == AccessAction.CHECKOUT:
            return None
        return latest

    async def get_current_occupancy_count(self) -> int:
        logs = await self.get_check_logs(limit=500)
        granted_logs = [l for l in logs if l.status == AccessStatus.GRANTED]
        latest_by_card = {}
        for log in granted_logs:
            if log.card_id not in latest_by_card:
                latest_by_card[log.card_id] = log
        count = sum(1 for log in latest_by_card.values() if log.action == AccessAction.CHECKIN)
        return max(0, count)

    async def add_environment_reading(self, reading: EnvironmentReading) -> EnvironmentReading:
        timestamp_str = reading.timestamp or datetime.now().isoformat()
        saved = reading.model_copy(update={"timestamp": timestamp_str})
        self.environment_readings.append(saved)
        return saved

    async def get_environment_readings(self, limit: int = 50) -> List[EnvironmentReading]:
        readings = sorted(self.environment_readings, key=lambda x: x.timestamp or "", reverse=True)
        return readings[:limit]

    async def get_latest_reading(self) -> Optional[EnvironmentReading]:
        readings = await self.get_environment_readings(limit=1)
        return readings[0] if readings else None

    async def get_environment_thresholds(self) -> Optional[dict]:
        return getattr(self, "_thresholds", None)

    async def save_environment_thresholds(self, temp_threshold: float, humidity_threshold: float) -> dict:
        self._thresholds = {
            "temp_threshold": temp_threshold,
            "humidity_threshold": humidity_threshold,
        }
        return self._thresholds
