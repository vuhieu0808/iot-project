"""Abstract Repository Interface for GymTag system."""

from abc import ABC, abstractmethod
from typing import List, Optional
from app.models.member import Member
from app.models.locker import Locker, LockerLog
from app.models.environment import EnvironmentReading
from app.models.check_log import CheckLog


class BaseRepository(ABC):
    """Abstract Repository interface providing data persistence abstraction."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize data storage schemas or connections."""
        pass

    # --- Member Repository Methods ---
    @abstractmethod
    async def get_member(self, card_id: str) -> Optional[Member]:
        """Fetch member by RFID card_id."""
        pass

    @abstractmethod
    async def get_all_members(self) -> List[Member]:
        """Fetch all registered members."""
        pass

    @abstractmethod
    async def save_member(self, member: Member) -> Member:
        """Save or update member data."""
        pass

    @abstractmethod
    async def delete_member(self, card_id: str) -> bool:
        """Delete member by card_id."""
        pass

    # --- Locker Repository Methods ---
    @abstractmethod
    async def get_locker(self, locker_number: int) -> Optional[Locker]:
        """Get locker state by locker number."""
        pass

    @abstractmethod
    async def get_all_lockers(self) -> List[Locker]:
        """Get states of all lockers."""
        pass

    @abstractmethod
    async def save_locker(self, locker: Locker) -> Locker:
        """Save or update locker state."""
        pass

    @abstractmethod
    async def get_locker_by_card(self, card_id: str) -> Optional[Locker]:
        """Find locker assigned to specific card_id."""
        pass

    @abstractmethod
    async def add_locker_log(self, log: LockerLog) -> LockerLog:
        """Add locker activity event log entry."""
        pass

    @abstractmethod
    async def get_locker_logs(
        self,
        limit: int = 50,
        locker_number: Optional[int] = None,
        card_id: Optional[str] = None
    ) -> List[LockerLog]:
        """Get locker activity logs."""
        pass

    # --- Check Log / Occupancy Repository Methods ---
    @abstractmethod
    async def add_check_log(self, log: CheckLog) -> CheckLog:
        """Add check-in / check-out event log entry."""
        pass

    @abstractmethod
    async def get_check_logs(self, limit: int = 50, card_id: Optional[str] = None) -> List[CheckLog]:
        """Get check-in / check-out history logs."""
        pass

    @abstractmethod
    async def get_active_checkin_for_card(self, card_id: str) -> Optional[CheckLog]:
        """Get open check-in event for card_id without a corresponding checkout."""
        pass

    @abstractmethod
    async def get_current_occupancy_count(self) -> int:
        """Calculate count of members currently inside the gym."""
        pass

    # --- Environment Repository Methods ---
    @abstractmethod
    async def add_environment_reading(self, reading: EnvironmentReading) -> EnvironmentReading:
        """Save sensor reading entry."""
        pass

    @abstractmethod
    async def get_environment_readings(self, limit: int = 50) -> List[EnvironmentReading]:
        """Get historical environment readings."""
        pass

    @abstractmethod
    async def get_latest_reading(self) -> Optional[EnvironmentReading]:
        """Get most recent temperature and humidity reading."""
        pass

    # --- Environment Threshold Settings Methods ---
    @abstractmethod
    async def get_environment_thresholds(self) -> Optional[dict]:
        """Get saved environment thresholds."""
        pass

    @abstractmethod
    async def save_environment_thresholds(self, temp_threshold: float, humidity_threshold: float) -> dict:
        """Save environment thresholds."""
        pass
