"""Firebase Realtime Database implementation of BaseRepository."""

import asyncio
import logging
import uuid
from datetime import datetime, date
from typing import List, Optional

from app.models.member import Member
from app.models.locker import Locker, LockerStatus, LockerAction, LockerLogStatus, LockerLog
from app.models.environment import EnvironmentReading
from app.models.check_log import CheckLog, AccessAction, AccessStatus
from app.repositories.base import BaseRepository

import firebase_admin
from firebase_admin import credentials, db

logger = logging.getLogger(__name__)


class FirebaseRepository(BaseRepository):
    """Firebase Realtime Database repository implementation."""

    def __init__(
        self,
        credentials_path: str = "firebase-admin-sdk.json",
        database_url: Optional[str] = None,
        default_locker_count: int = 5,
    ):
        self.credentials_path = credentials_path
        self.database_url = database_url
        self.default_locker_count = default_locker_count
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize Firebase Admin SDK and default locker records."""
        def _init_sdk():
            if not firebase_admin._apps:
                cred = credentials.Certificate(self.credentials_path)
                firebase_admin.initialize_app(cred, {"databaseURL": self.database_url})
            self.initialized = True
            logger.info("Firebase Realtime Database initialized successfully.")

        await asyncio.to_thread(_init_sdk)

        # Initialize default lockers if missing
        # Initialize default lockers if missing
        lockers = await self.get_all_lockers()
        if len(lockers) < self.default_locker_count:
            for i in range(1, self.default_locker_count + 1):
                if not any(l.locker_number == i for l in lockers):
                    await self.save_locker(Locker(locker_number=i, status=LockerStatus.VACANT, is_occupied=False))

    # --- Helper methods for Firebase refs ---
    def _ref(self, path: str):
        return db.reference(path)

    @staticmethod
    def _extract_items(data):
        if not data:
            return []
        if isinstance(data, dict):
            return [v for v in data.values() if isinstance(v, dict)]
        elif isinstance(data, list):
            return [v for v in data if isinstance(v, dict)]
        return []

    @staticmethod
    def _parse_locker_data(data: dict) -> Locker:
        status_str = data.get("status")
        if status_str in [s.value for s in LockerStatus]:
            status = LockerStatus(status_str)
        elif bool(data.get("is_occupied")):
            status = LockerStatus.OCCUPIED
        else:
            status = LockerStatus.VACANT

        card_id = str(data["card_id"]) if data.get("card_id") is not None else None

        return Locker(
            locker_number=data["locker_number"],
            status=status,
            is_occupied=(status == LockerStatus.OCCUPIED),
            card_id=card_id,
            assigned_at=data.get("assigned_at"),
        )

    # --- Member Methods ---
    async def get_member(self, card_id: str) -> Optional[Member]:
        def _get():
            data = self._ref(f"members/{card_id}").get()
            if not data:
                return None
            return Member(
                card_id=str(data["card_id"]),
                name=data["name"],
                email=data.get("email"),
                phone=data.get("phone"),
                membership_expiry=date.fromisoformat(data["membership_expiry"]),
                is_active=bool(data.get("is_active", True)),
                created_at=data.get("created_at"),
                password_hash=data.get("password_hash"),
            )
        return await asyncio.to_thread(_get)

    async def get_all_members(self) -> List[Member]:
        def _get():
            data = self._ref("members").get()
            result = []
            for item in self._extract_items(data):
                if "card_id" in item:
                    result.append(
                        Member(
                            card_id=str(item["card_id"]),
                            name=item["name"],
                            email=item.get("email"),
                            phone=item.get("phone"),
                            membership_expiry=date.fromisoformat(item["membership_expiry"]),
                            is_active=bool(item.get("is_active", True)),
                            created_at=item.get("created_at"),
                            password_hash=item.get("password_hash"),
                        )
                    )
            return result
        return await asyncio.to_thread(_get)

    async def save_member(self, member: Member) -> Member:
        now_str = member.created_at or datetime.now().isoformat()
        member_to_save = member.model_copy(update={"created_at": now_str})

        def _save():
            # If password_hash is not set on member_to_save, preserve existing password_hash if found
            existing_ref = self._ref(f"members/{member_to_save.card_id}")
            existing_data = existing_ref.get() or {}
            pw_hash = member_to_save.password_hash or existing_data.get("password_hash")

            data = {
                "card_id": str(member_to_save.card_id),
                "name": member_to_save.name,
                "email": member_to_save.email,
                "phone": member_to_save.phone,
                "membership_expiry": member_to_save.membership_expiry.isoformat(),
                "is_active": member_to_save.is_active,
                "created_at": member_to_save.created_at,
                "password_hash": pw_hash,
            }
            existing_ref.set(data)

        await asyncio.to_thread(_save)
        return member_to_save

    async def delete_member(self, card_id: str) -> bool:
        def _delete():
            ref = self._ref(f"members/{card_id}")
            if ref.get() is not None:
                ref.delete()
                return True
            return False
        return await asyncio.to_thread(_delete)

    # --- Locker Methods ---
    async def get_locker(self, locker_number: int) -> Optional[Locker]:
        def _get():
            data = self._ref(f"lockers/{locker_number}").get()
            if not data:
                return None
            return self._parse_locker_data(data)
        return await asyncio.to_thread(_get)

    async def get_all_lockers(self) -> List[Locker]:
        def _get():
            data = self._ref("lockers").get()
            result = []
            for item in self._extract_items(data):
                if "locker_number" in item:
                    result.append(self._parse_locker_data(item))
            return sorted(result, key=lambda x: x.locker_number)
        return await asyncio.to_thread(_get)

    async def save_locker(self, locker: Locker) -> Locker:
        def _save():
            data = {
                "locker_number": locker.locker_number,
                "status": locker.status.value,
                "is_occupied": locker.is_occupied,
                "card_id": str(locker.card_id) if locker.card_id is not None else None,
                "assigned_at": locker.assigned_at,
            }
            self._ref(f"lockers/{locker.locker_number}").set(data)
        await asyncio.to_thread(_save)
        return locker

    async def get_locker_by_card(self, card_id: str) -> Optional[Locker]:
        lockers = await self.get_all_lockers()
        for locker in lockers:
            if locker.is_occupied and str(locker.card_id) == str(card_id):
                return locker
        return None

    # --- Locker Activity Logs Methods ---
    async def add_locker_log(self, log: LockerLog) -> LockerLog:
        log_id = log.id or str(uuid.uuid4())
        timestamp_str = log.timestamp or datetime.now().isoformat()
        log_to_save = log.model_copy(update={"id": log_id, "timestamp": timestamp_str})

        def _save():
            data = {
                "id": log_to_save.id,
                "locker_number": log_to_save.locker_number,
                "card_id": str(log_to_save.card_id) if log_to_save.card_id is not None else None,
                "member_name": log_to_save.member_name,
                "action": log_to_save.action.value if hasattr(log_to_save.action, "value") else str(log_to_save.action),
                "status": log_to_save.status.value if hasattr(log_to_save.status, "value") else str(log_to_save.status),
                "reason": log_to_save.reason,
                "timestamp": log_to_save.timestamp,
            }
            self._ref(f"locker_logs/{log_to_save.id}").set(data)

        await asyncio.to_thread(_save)
        return log_to_save

    async def get_locker_logs(
        self,
        limit: int = 50,
        locker_number: Optional[int] = None,
        card_id: Optional[str] = None
    ) -> List[LockerLog]:
        def _get():
            data = self._ref("locker_logs").get()
            logs = []
            for item in self._extract_items(data):
                if isinstance(item, dict) and "action" in item:
                    item_locker_num = item.get("locker_number")
                    if locker_number is not None:
                        if item_locker_num is None or str(item_locker_num) != str(locker_number):
                            continue
                    if card_id:
                        if str(item.get("card_id", "")).strip().lower() != str(card_id).strip().lower():
                            continue

                    action_str = str(item.get("action", "")).lower()
                    action = LockerAction(action_str) if action_str in [a.value for a in LockerAction] else LockerAction.ASSIGN
                    status_str = str(item.get("status", "")).lower()
                    status = LockerLogStatus(status_str) if status_str in [s.value for s in LockerLogStatus] else LockerLogStatus.GRANTED

                    parsed_locker_num = None
                    if item_locker_num is not None:
                        try:
                            parsed_locker_num = int(item_locker_num)
                        except (ValueError, TypeError):
                            parsed_locker_num = None

                    logs.append(
                        LockerLog(
                            id=item.get("id"),
                            locker_number=parsed_locker_num,
                            card_id=str(item["card_id"]) if item.get("card_id") is not None else None,
                            member_name=item.get("member_name", "Unknown"),
                            action=action,
                            status=status,
                            reason=item.get("reason"),
                            timestamp=item.get("timestamp"),
                        )
                    )
            logs.sort(key=lambda x: x.timestamp or "", reverse=True)
            return logs[:limit]

        return await asyncio.to_thread(_get)

    # --- Check Log / Occupancy Methods ---
    async def add_check_log(self, log: CheckLog) -> CheckLog:
        log_id = log.id or str(uuid.uuid4())
        timestamp_str = log.timestamp or datetime.now().isoformat()
        log_to_save = log.model_copy(update={"id": log_id, "timestamp": timestamp_str})

        def _save():
            data = {
                "id": log_to_save.id,
                "card_id": log_to_save.card_id,
                "member_name": log_to_save.member_name,
                "action": log_to_save.action.value,
                "status": log_to_save.status.value,
                "reason": log_to_save.reason,
                "duration_minutes": log_to_save.duration_minutes,
                "timestamp": log_to_save.timestamp,
            }
            self._ref(f"check_logs/{log_to_save.id}").set(data)
        await asyncio.to_thread(_save)
        return log_to_save

    async def get_check_logs(self, limit: int = 50, card_id: Optional[str] = None) -> List[CheckLog]:
        def _get():
            data = self._ref("check_logs").get()
            logs = []
            for item in self._extract_items(data):
                if "card_id" in item:
                    if card_id and item["card_id"] != card_id:
                        continue
                    logs.append(
                        CheckLog(
                            id=item["id"],
                            card_id=item["card_id"],
                            member_name=item.get("member_name", "Unknown"),
                            action=AccessAction(item["action"]),
                            status=AccessStatus(item["status"]),
                            reason=item.get("reason"),
                            duration_minutes=item.get("duration_minutes"),
                            timestamp=item.get("timestamp"),
                        )
                    )
            logs.sort(key=lambda x: x.timestamp or "", reverse=True)
            return logs[:limit]
        return await asyncio.to_thread(_get)

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

    # --- Environment Methods ---
    async def add_environment_reading(self, reading: EnvironmentReading) -> EnvironmentReading:
        timestamp_str = reading.timestamp or datetime.now().isoformat()
        reading_to_save = reading.model_copy(update={"timestamp": timestamp_str})
        reading_id = str(uuid.uuid4())

        def _save():
            data = {
                "temperature": reading_to_save.temperature,
                "humidity": reading_to_save.humidity,
                "fan_on": reading_to_save.fan_on,
                "timestamp": reading_to_save.timestamp,
            }
            self._ref(f"environment_readings/{reading_id}").set(data)

        await asyncio.to_thread(_save)
        return reading_to_save

    async def get_environment_readings(self, limit: int = 50) -> List[EnvironmentReading]:
        def _get():
            data = self._ref("environment_readings").get()
            readings = []
            for item in self._extract_items(data):
                if "temperature" in item:
                    readings.append(
                        EnvironmentReading(
                            temperature=item["temperature"],
                            humidity=item["humidity"],
                            fan_on=bool(item.get("fan_on", False)),
                            timestamp=item.get("timestamp"),
                        )
                    )
            readings.sort(key=lambda x: x.timestamp or "", reverse=True)
            return readings[:limit]
        return await asyncio.to_thread(_get)

    async def get_latest_reading(self) -> Optional[EnvironmentReading]:
        readings = await self.get_environment_readings(limit=1)
        if readings:
            return readings[0]
        return None

    # --- Environment Threshold Settings ---
    async def get_environment_thresholds(self) -> Optional[dict]:
        """Get saved environment thresholds from Firebase."""
        def _get():
            data = self._ref("settings/environment_thresholds").get()
            return data
        return await asyncio.to_thread(_get)

    async def save_environment_thresholds(self, temp_threshold: float, humidity_threshold: float) -> dict:
        """Save environment thresholds to Firebase."""
        def _save():
            data = {
                "temp_threshold": temp_threshold,
                "humidity_threshold": humidity_threshold,
            }
            self._ref("settings/environment_thresholds").set(data)
            return data
        return await asyncio.to_thread(_save)
