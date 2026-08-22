"""Occupancy tracking service."""

import logging
from app.repositories.firebase_repo import FirebaseRepository

logger = logging.getLogger(__name__)


class OccupancyService:
    """Calculates real-time occupancy within the gym facility."""

    def __init__(self, repository: FirebaseRepository):
        self.repository = repository

    async def get_current_occupancy(self) -> int:
        """Get number of people currently checked into the gym.

        Returns:
            int: Current occupant count.
        """
        occupancy = await self.repository.get_current_occupancy_count()
        logger.debug(f"Current gym occupancy count: {occupancy}")
        return occupancy
