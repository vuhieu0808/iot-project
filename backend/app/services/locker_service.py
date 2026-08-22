"""Locker management service handling assignment, release logic, and admin force controls."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from app.models.locker import Locker, LockerStatus, LockerAction, LockerLogStatus, LockerLog
from app.repositories.firebase_repo import FirebaseRepository

logger = logging.getLogger(__name__)


class LockerService:
    """Manages locker allocation and release operations."""

    def __init__(self, repository: FirebaseRepository):
        self.repository = repository

    async def process_locker_scan(self, card_id: str) -> Dict[str, Any]:
        """Assign a locker or return the card's existing locker for access.

        Args:
            card_id: RFID card string.

        Returns:
            Dict containing response for MQTT topic:
            {
                "card_id": str,
                "action": "assign" | "access" | "denied",
                "locker_number": int or None,
                "member_name": str or None,
                "reason": str
            }
        """
        logger.info(f"Processing locker scan for card_id: {card_id}")

        member = await self.repository.get_member(card_id)
        if not member:
            logger.warning(f"Locker access denied: card_id {card_id} is not registered.")
            await self.repository.add_locker_log(
                LockerLog(
                    card_id=card_id,
                    member_name="Unknown",
                    action=LockerAction.DENIED,
                    status=LockerLogStatus.DENIED,
                    reason="RFID card is not registered",
                )
            )
            return {
                "card_id": card_id,
                "action": "denied",
                "locker_number": None,
                "member_name": None,
                "reason": "RFID card is not registered",
            }

        # A repeated scan opens the existing locker without changing ownership.
        existing_locker = await self.repository.get_locker_by_card(card_id)

        if existing_locker:
            logger.info(f"Granted access to locker #{existing_locker.locker_number} for card_id: {card_id}")
            await self.repository.add_locker_log(
                LockerLog(
                    locker_number=existing_locker.locker_number,
                    card_id=card_id,
                    member_name=member.name,
                    action=LockerAction.ACCESS,
                    status=LockerLogStatus.GRANTED,
                    reason=f"Locker #{existing_locker.locker_number} opened",
                )
            )
            return {
                "card_id": card_id,
                "action": "access",
                "locker_number": existing_locker.locker_number,
                "member_name": member.name,
                "reason": f"Locker #{existing_locker.locker_number} opened",
            }
        else:
            # ASSIGN LOCKER (Find first empty locker slot that is VACANT, not BROKEN)
            all_lockers = await self.repository.get_all_lockers()
            empty_lockers = [l for l in all_lockers if l.status == LockerStatus.VACANT]

            if not empty_lockers:
                logger.warning(f"Locker assignment failed for {card_id}: No vacant lockers available.")
                await self.repository.add_locker_log(
                    LockerLog(
                        card_id=card_id,
                        member_name=member.name,
                        action=LockerAction.DENIED,
                        status=LockerLogStatus.DENIED,
                        reason="No vacant lockers available",
                    )
                )
                return {
                    "card_id": card_id,
                    "action": "denied",
                    "locker_number": None,
                    "member_name": member.name,
                    "reason": "No vacant lockers available",
                }

            # Select lowest available locker number
            target_locker = min(empty_lockers, key=lambda l: l.locker_number)
            now_str = datetime.now().isoformat()

            updated_locker = Locker(
                locker_number=target_locker.locker_number,
                status=LockerStatus.OCCUPIED,
                is_occupied=True,
                card_id=card_id,
                assigned_at=now_str,
            )
            await self.repository.save_locker(updated_locker)
            logger.info(f"Assigned locker #{target_locker.locker_number} to card_id: {card_id}")

            await self.repository.add_locker_log(
                LockerLog(
                    locker_number=target_locker.locker_number,
                    card_id=card_id,
                    member_name=member.name,
                    action=LockerAction.ASSIGN,
                    status=LockerLogStatus.GRANTED,
                    reason=f"Locker #{target_locker.locker_number} assigned successfully",
                )
            )

            return {
                "card_id": card_id,
                "action": "assign",
                "locker_number": target_locker.locker_number,
                "member_name": member.name,
                "reason": f"Locker #{target_locker.locker_number} assigned successfully",
            }

    async def release_locker(self, card_id: str, locker_number: int) -> Dict[str, Any]:
        """Release a locker only when the requesting card currently owns it."""
        member = await self.repository.get_member(card_id)
        if not member:
            await self.repository.add_locker_log(
                LockerLog(
                    locker_number=locker_number,
                    card_id=card_id,
                    member_name="Unknown",
                    action=LockerAction.DENIED,
                    status=LockerLogStatus.DENIED,
                    reason="RFID card is not registered",
                )
            )
            return {
                "card_id": card_id,
                "action": "denied",
                "locker_number": None,
                "member_name": None,
                "reason": "RFID card is not registered",
            }

        existing_locker = await self.repository.get_locker_by_card(card_id)
        if not existing_locker:
            await self.repository.add_locker_log(
                LockerLog(
                    locker_number=locker_number,
                    card_id=card_id,
                    member_name=member.name,
                    action=LockerAction.DENIED,
                    status=LockerLogStatus.DENIED,
                    reason="Card does not own a locker",
                )
            )
            return {
                "card_id": card_id,
                "action": "denied",
                "locker_number": None,
                "member_name": member.name,
                "reason": "Card does not own a locker",
            }

        if existing_locker.locker_number != locker_number:
            await self.repository.add_locker_log(
                LockerLog(
                    locker_number=locker_number,
                    card_id=card_id,
                    member_name=member.name,
                    action=LockerAction.DENIED,
                    status=LockerLogStatus.DENIED,
                    reason="Requested locker does not match the card's assigned locker",
                )
            )
            return {
                "card_id": card_id,
                "action": "denied",
                "locker_number": existing_locker.locker_number,
                "member_name": member.name,
                "reason": "Requested locker does not match the card's assigned locker",
            }

        if existing_locker.status != LockerStatus.OCCUPIED or not existing_locker.is_occupied:
            await self.repository.add_locker_log(
                LockerLog(
                    locker_number=existing_locker.locker_number,
                    card_id=card_id,
                    member_name=member.name,
                    action=LockerAction.DENIED,
                    status=LockerLogStatus.DENIED,
                    reason="Assigned locker is not occupied",
                )
            )
            return {
                "card_id": card_id,
                "action": "denied",
                "locker_number": existing_locker.locker_number,
                "member_name": member.name,
                "reason": "Assigned locker is not occupied",
            }

        released = Locker(
            locker_number=existing_locker.locker_number,
            status=LockerStatus.VACANT,
            is_occupied=False,
            card_id=None,
            assigned_at=None,
        )
        await self.repository.save_locker(released)
        logger.info(f"Released locker #{locker_number} for card_id: {card_id}")

        await self.repository.add_locker_log(
            LockerLog(
                locker_number=locker_number,
                card_id=card_id,
                member_name=member.name,
                action=LockerAction.RELEASE,
                status=LockerLogStatus.GRANTED,
                reason=f"Locker #{locker_number} released successfully",
            )
        )

        return {
            "card_id": card_id,
            "action": "release",
            "locker_number": locker_number,
            "member_name": member.name,
            "reason": f"Locker #{locker_number} released successfully",
        }

    async def get_all_lockers(self) -> List[Locker]:
        """Retrieve all locker states."""
        return await self.repository.get_all_lockers()

    async def get_locker_logs(
        self,
        limit: int = 50,
        locker_number: Optional[int] = None,
        card_id: Optional[str] = None,
    ) -> List[LockerLog]:
        """Retrieve locker activity logs."""
        return await self.repository.get_locker_logs(
            limit=limit,
            locker_number=locker_number,
            card_id=card_id,
        )

    async def force_release_locker(self, locker_number: int) -> Locker:
        """Admin force release a locker."""
        locker = await self.repository.get_locker(locker_number)
        if not locker:
            raise ValueError(f"Locker #{locker_number} not found.")

        prev_card_id = locker.card_id
        prev_member_name = "Admin"
        if prev_card_id:
            member = await self.repository.get_member(prev_card_id)
            if member:
                prev_member_name = member.name

        updated_locker = Locker(
            locker_number=locker_number,
            status=LockerStatus.VACANT,
            is_occupied=False,
            card_id=None,
            assigned_at=None,
        )
        saved = await self.repository.save_locker(updated_locker)
        logger.info(f"Admin force released locker #{locker_number}")

        await self.repository.add_locker_log(
            LockerLog(
                locker_number=locker_number,
                card_id=prev_card_id,
                member_name=prev_member_name,
                action=LockerAction.FORCE_RELEASE,
                status=LockerLogStatus.GRANTED,
                reason=f"Admin force released locker #{locker_number}",
            )
        )

        return saved

    async def force_assign_locker(self, locker_number: int, card_id: str) -> Locker:
        """Admin force assign a specific card_id to a locker."""
        locker = await self.repository.get_locker(locker_number)
        if not locker:
            raise ValueError(f"Locker #{locker_number} not found.")

        # If card already holds another locker, release it first
        existing_locker = await self.repository.get_locker_by_card(card_id)
        if existing_locker and existing_locker.locker_number != locker_number:
            await self.force_release_locker(existing_locker.locker_number)

        member = await self.repository.get_member(card_id)
        member_name = member.name if member else "Unknown"

        now_str = datetime.now().isoformat()
        updated_locker = Locker(
            locker_number=locker_number,
            status=LockerStatus.OCCUPIED,
            is_occupied=True,
            card_id=card_id,
            assigned_at=now_str,
        )
        saved = await self.repository.save_locker(updated_locker)
        logger.info(f"Admin force assigned locker #{locker_number} to card_id {card_id}")

        await self.repository.add_locker_log(
            LockerLog(
                locker_number=locker_number,
                card_id=card_id,
                member_name=member_name,
                action=LockerAction.FORCE_ASSIGN,
                status=LockerLogStatus.GRANTED,
                reason=f"Admin force assigned locker #{locker_number} to {card_id}",
            )
        )

        return saved

    async def set_locker_status(self, locker_number: int, status: LockerStatus) -> Locker:
        """Admin change status of a locker (vacant / broken / occupied)."""
        locker = await self.repository.get_locker(locker_number)
        if not locker:
            raise ValueError(f"Locker #{locker_number} not found.")

        if status == LockerStatus.BROKEN:
            # If set to broken, clear user allocation
            updated_locker = Locker(
                locker_number=locker_number,
                status=LockerStatus.BROKEN,
                is_occupied=False,
                card_id=None,
                assigned_at=None,
            )
        elif status == LockerStatus.VACANT:
            updated_locker = Locker(
                locker_number=locker_number,
                status=LockerStatus.VACANT,
                is_occupied=False,
                card_id=None,
                assigned_at=None,
            )
        elif status == LockerStatus.OCCUPIED:
            updated_locker = Locker(
                locker_number=locker_number,
                status=LockerStatus.OCCUPIED,
                is_occupied=True,
                card_id=locker.card_id,
                assigned_at=locker.assigned_at or datetime.now().isoformat(),
            )

        saved = await self.repository.save_locker(updated_locker)
        logger.info(f"Admin updated locker #{locker_number} status to {status.value}")

        await self.repository.add_locker_log(
            LockerLog(
                locker_number=locker_number,
                card_id=locker.card_id,
                member_name="Admin",
                action=LockerAction.STATUS_CHANGE,
                status=LockerLogStatus.GRANTED,
                reason=f"Admin updated locker #{locker_number} status to {status.value}",
            )
        )

        return saved

