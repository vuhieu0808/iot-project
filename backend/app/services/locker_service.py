"""Locker management service handling assignment and release logic."""

import logging
from datetime import datetime
from typing import Any, Dict
from app.models.locker import Locker
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class LockerService:
    """Manages locker allocation and release operations."""

    def __init__(self, repository: BaseRepository):
        self.repository = repository

    async def process_locker_scan(self, card_id: str) -> Dict[str, Any]:
        """Process locker card scan from ESP32.

        Args:
            card_id: RFID card string.

        Returns:
            Dict containing response for MQTT topic:
            {
                "card_id": str,
                "action": "assign" | "release" | "denied",
                "locker_number": int or None,
                "reason": str
            }
        """
        logger.info(f"Processing locker scan for card_id: {card_id}")

        # Check if card currently holds a locker
        existing_locker = await self.repository.get_locker_by_card(card_id)

        if existing_locker:
            # RELEASE LOCKER
            locker_num = existing_locker.locker_number
            updated_locker = Locker(
                locker_number=locker_num,
                is_occupied=False,
                card_id=None,
                assigned_at=None,
            )
            await self.repository.save_locker(updated_locker)
            logger.info(f"Released locker #{locker_num} for card_id: {card_id}")

            return {
                "card_id": card_id,
                "action": "release",
                "locker_number": locker_num,
                "reason": f"Locker #{locker_num} released successfully",
            }
        else:
            # ASSIGN LOCKER (Find first empty locker slot)
            all_lockers = await self.repository.get_all_lockers()
            empty_lockers = [l for l in all_lockers if not l.is_occupied]

            if not empty_lockers:
                logger.warning(f"Locker assignment failed for {card_id}: All lockers occupied.")
                return {
                    "card_id": card_id,
                    "action": "denied",
                    "locker_number": None,
                    "reason": "No lockers available",
                }

            # Select lowest available locker number
            target_locker = min(empty_lockers, key=lambda l: l.locker_number)
            now_str = datetime.now().isoformat()

            updated_locker = Locker(
                locker_number=target_locker.locker_number,
                is_occupied=True,
                card_id=card_id,
                assigned_at=now_str,
            )
            await self.repository.save_locker(updated_locker)
            logger.info(f"Assigned locker #{target_locker.locker_number} to card_id: {card_id}")

            return {
                "card_id": card_id,
                "action": "assign",
                "locker_number": target_locker.locker_number,
                "reason": f"Locker #{target_locker.locker_number} assigned successfully",
            }

    async def get_all_lockers(self):
        """Retrieve all locker states."""
        return await self.repository.get_all_lockers()
