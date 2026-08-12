"""Access service managing door check-in / check-out verification logic."""

import logging
from datetime import date, datetime
from typing import Any, Dict
from app.models.check_log import CheckLog, AccessAction, AccessStatus
from app.models.member import MemberStatus
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class AccessService:
    """Handles door card scan verification, duration calculation, and logging."""

    def __init__(self, repository: BaseRepository):
        self.repository = repository

    async def verify_card_scan(self, card_id: str) -> Dict[str, Any]:
        """Process door card scan request from ESP32.

        Args:
            card_id: RFID card string scan.

        Returns:
            Dict containing result data for MQTT response:
            {
                "card_id": str,
                "status": "granted" | "denied",
                "action": "checkin" | "checkout",
                "member_name": str,
                "reason": str,
                "duration_minutes": float or None
            }
        """
        logger.info(f"Processing door scan for card_id: {card_id}")
        member = await self.repository.get_member(card_id)

        # 1. Member not found
        if not member:
            logger.warning(f"Card scan failed: card_id {card_id} not found.")
            await self.repository.add_check_log(
                CheckLog(
                    card_id=card_id,
                    member_name="Unknown",
                    action=AccessAction.CHECKIN,
                    status=AccessStatus.DENIED,
                    reason="Card ID not registered in database",
                )
            )
            return {
                "card_id": card_id,
                "status": AccessStatus.DENIED.value,
                "action": AccessAction.CHECKIN.value,
                "member_name": "Unknown",
                "reason": "Card not found",
                "duration_minutes": None,
            }

        # 2. Member inactive
        if not member.is_active:
            logger.warning(f"Card scan failed: member {member.name} ({card_id}) account inactive.")
            await self.repository.add_check_log(
                CheckLog(
                    card_id=card_id,
                    member_name=member.name,
                    action=AccessAction.CHECKIN,
                    status=AccessStatus.DENIED,
                    reason="Member account is inactive",
                )
            )
            return {
                "card_id": card_id,
                "status": AccessStatus.DENIED.value,
                "action": AccessAction.CHECKIN.value,
                "member_name": member.name,
                "reason": "Account inactive",
                "duration_minutes": None,
            }

        # 3. Membership expired check
        today = date.today()
        if member.membership_expiry < today:
            logger.warning(
                f"Card scan failed: member {member.name} ({card_id}) membership expired on {member.membership_expiry}."
            )
            await self.repository.add_check_log(
                CheckLog(
                    card_id=card_id,
                    member_name=member.name,
                    action=AccessAction.CHECKIN,
                    status=AccessStatus.DENIED,
                    reason=f"Membership expired on {member.membership_expiry}",
                )
            )
            return {
                "card_id": card_id,
                "status": AccessStatus.DENIED.value,
                "action": AccessAction.CHECKIN.value,
                "member_name": member.name,
                "reason": f"Membership expired ({member.membership_expiry})",
                "duration_minutes": None,
            }

        # 4. Check active session (determines Check-in vs Check-out)
        active_checkin = await self.repository.get_active_checkin_for_card(card_id)
        now = datetime.now()

        if active_checkin is None:
            # First scan -> CHECK-IN
            log = CheckLog(
                card_id=card_id,
                member_name=member.name,
                action=AccessAction.CHECKIN,
                status=AccessStatus.GRANTED,
                reason="Check-in successful",
                timestamp=now.isoformat(),
            )
            await self.repository.add_check_log(log)
            logger.info(f"Check-in granted for {member.name} ({card_id})")
            return {
                "card_id": card_id,
                "status": AccessStatus.GRANTED.value,
                "action": AccessAction.CHECKIN.value,
                "member_name": member.name,
                "reason": "Check-in granted",
                "duration_minutes": None,
            }
        else:
            # Second scan -> CHECK-OUT
            duration_minutes = 0.0
            if active_checkin.timestamp:
                try:
                    checkin_dt = datetime.fromisoformat(active_checkin.timestamp)
                    delta = now - checkin_dt
                    duration_minutes = round(delta.total_seconds() / 60.0, 2)
                except Exception as e:
                    logger.error(f"Error calculating session duration: {e}")

            log = CheckLog(
                card_id=card_id,
                member_name=member.name,
                action=AccessAction.CHECKOUT,
                status=AccessStatus.GRANTED,
                reason="Check-out successful",
                duration_minutes=duration_minutes,
                timestamp=now.isoformat(),
            )
            await self.repository.add_check_log(log)
            logger.info(f"Check-out granted for {member.name} ({card_id}), duration: {duration_minutes} mins")
            return {
                "card_id": card_id,
                "status": AccessStatus.GRANTED.value,
                "action": AccessAction.CHECKOUT.value,
                "member_name": member.name,
                "reason": "Check-out granted",
                "duration_minutes": duration_minutes,
            }
