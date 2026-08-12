"""SQLite implementation of BaseRepository using aiosqlite."""

import logging
import uuid
from datetime import datetime, date
from typing import List, Optional
import aiosqlite

from app.models.member import Member
from app.models.locker import Locker
from app.models.environment import EnvironmentReading
from app.models.check_log import CheckLog, AccessAction, AccessStatus
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class SQLiteRepository(BaseRepository):
    """SQLite data access layer."""

    def __init__(self, db_path: str = "gymtag.db", default_locker_count: int = 5):
        self.db_path = db_path
        self.default_locker_count = default_locker_count

    async def initialize(self) -> None:
        """Create tables if they do not exist and initialize lockers."""
        logger.info(f"Initializing SQLite database at {self.db_path}")
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS members (
                    card_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT,
                    phone TEXT,
                    membership_expiry TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS lockers (
                    locker_number INTEGER PRIMARY KEY,
                    is_occupied INTEGER NOT NULL DEFAULT 0,
                    card_id TEXT,
                    assigned_at TEXT
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS check_logs (
                    id TEXT PRIMARY KEY,
                    card_id TEXT NOT NULL,
                    member_name TEXT NOT NULL,
                    action TEXT NOT NULL,
                    status TEXT NOT NULL,
                    reason TEXT,
                    duration_minutes REAL,
                    timestamp TEXT NOT NULL
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS environment_readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    temperature REAL NOT NULL,
                    humidity REAL NOT NULL,
                    fan_on INTEGER NOT NULL DEFAULT 0,
                    timestamp TEXT NOT NULL
                )
            """)

            await db.commit()

        # Seed lockers if empty
        existing_lockers = await self.get_all_lockers()
        if len(existing_lockers) < self.default_locker_count:
            for i in range(1, self.default_locker_count + 1):
                if not any(l.locker_number == i for l in existing_lockers):
                    await self.save_locker(Locker(locker_number=i, is_occupied=False))

    # --- Member Methods ---
    async def get_member(self, card_id: str) -> Optional[Member]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM members WHERE card_id = ?", (card_id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                return Member(
                    card_id=row["card_id"],
                    name=row["name"],
                    email=row["email"],
                    phone=row["phone"],
                    membership_expiry=date.fromisoformat(row["membership_expiry"]),
                    is_active=bool(row["is_active"]),
                    created_at=row["created_at"],
                )

    async def get_all_members(self) -> List[Member]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM members ORDER BY created_at DESC") as cursor:
                rows = await cursor.fetchall()
                return [
                    Member(
                        card_id=row["card_id"],
                        name=row["name"],
                        email=row["email"],
                        phone=row["phone"],
                        membership_expiry=date.fromisoformat(row["membership_expiry"]),
                        is_active=bool(row["is_active"]),
                        created_at=row["created_at"],
                    )
                    for row in rows
                ]

    async def save_member(self, member: Member) -> Member:
        now_str = member.created_at or datetime.now().isoformat()
        member_to_save = member.model_copy(update={"created_at": now_str})
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO members (card_id, name, email, phone, membership_expiry, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(card_id) DO UPDATE SET
                    name=excluded.name,
                    email=excluded.email,
                    phone=excluded.phone,
                    membership_expiry=excluded.membership_expiry,
                    is_active=excluded.is_active
            """, (
                member_to_save.card_id,
                member_to_save.name,
                member_to_save.email,
                member_to_save.phone,
                member_to_save.membership_expiry.isoformat(),
                1 if member_to_save.is_active else 0,
                member_to_save.created_at,
            ))
            await db.commit()
        return member_to_save

    async def delete_member(self, card_id: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("DELETE FROM members WHERE card_id = ?", (card_id,))
            await db.commit()
            return cursor.rowcount > 0

    # --- Locker Methods ---
    async def get_locker(self, locker_number: int) -> Optional[Locker]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM lockers WHERE locker_number = ?", (locker_number,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                return Locker(
                    locker_number=row["locker_number"],
                    is_occupied=bool(row["is_occupied"]),
                    card_id=row["card_id"],
                    assigned_at=row["assigned_at"],
                )

    async def get_all_lockers(self) -> List[Locker]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM lockers ORDER BY locker_number ASC") as cursor:
                rows = await cursor.fetchall()
                return [
                    Locker(
                        locker_number=row["locker_number"],
                        is_occupied=bool(row["is_occupied"]),
                        card_id=row["card_id"],
                        assigned_at=row["assigned_at"],
                    )
                    for row in rows
                ]

    async def save_locker(self, locker: Locker) -> Locker:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO lockers (locker_number, is_occupied, card_id, assigned_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(locker_number) DO UPDATE SET
                    is_occupied=excluded.is_occupied,
                    card_id=excluded.card_id,
                    assigned_at=excluded.assigned_at
            """, (
                locker.locker_number,
                1 if locker.is_occupied else 0,
                locker.card_id,
                locker.assigned_at,
            ))
            await db.commit()
        return locker

    async def get_locker_by_card(self, card_id: str) -> Optional[Locker]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM lockers WHERE card_id = ? AND is_occupied = 1", (card_id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                return Locker(
                    locker_number=row["locker_number"],
                    is_occupied=bool(row["is_occupied"]),
                    card_id=row["card_id"],
                    assigned_at=row["assigned_at"],
                )

    # --- Check Log / Occupancy Methods ---
    async def add_check_log(self, log: CheckLog) -> CheckLog:
        log_id = log.id or str(uuid.uuid4())
        timestamp_str = log.timestamp or datetime.now().isoformat()
        log_to_save = log.model_copy(update={"id": log_id, "timestamp": timestamp_str})

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO check_logs (id, card_id, member_name, action, status, reason, duration_minutes, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log_to_save.id,
                log_to_save.card_id,
                log_to_save.member_name,
                log_to_save.action.value,
                log_to_save.status.value,
                log_to_save.reason,
                log_to_save.duration_minutes,
                log_to_save.timestamp,
            ))
            await db.commit()
        return log_to_save

    async def get_check_logs(self, limit: int = 50, card_id: Optional[str] = None) -> List[CheckLog]:
        query = "SELECT * FROM check_logs"
        params = []
        if card_id:
            query += " WHERE card_id = ?"
            params.append(card_id)
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, tuple(params)) as cursor:
                rows = await cursor.fetchall()
                return [
                    CheckLog(
                        id=row["id"],
                        card_id=row["card_id"],
                        member_name=row["member_name"],
                        action=AccessAction(row["action"]),
                        status=AccessStatus(row["status"]),
                        reason=row["reason"],
                        duration_minutes=row["duration_minutes"],
                        timestamp=row["timestamp"],
                    )
                    for row in rows
                ]

    async def get_active_checkin_for_card(self, card_id: str) -> Optional[CheckLog]:
        """Find the latest check-in for this card that has no subsequent checkout."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM check_logs
                WHERE card_id = ? AND status = 'granted'
                ORDER BY timestamp DESC LIMIT 1
            """, (card_id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                if row["action"] == AccessAction.CHECKOUT.value:
                    return None
                return CheckLog(
                    id=row["id"],
                    card_id=row["card_id"],
                    member_name=row["member_name"],
                    action=AccessAction(row["action"]),
                    status=AccessStatus(row["status"]),
                    reason=row["reason"],
                    duration_minutes=row["duration_minutes"],
                    timestamp=row["timestamp"],
                )

    async def get_current_occupancy_count(self) -> int:
        """Calculate count of members currently inside the gym."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            # Get latest granted scan for each member
            async with db.execute("""
                SELECT card_id, action FROM check_logs
                WHERE status = 'granted' AND id IN (
                    SELECT max_id FROM (
                        SELECT card_id, MAX(timestamp) as max_ts, id as max_id
                        FROM check_logs
                        WHERE status = 'granted'
                        GROUP BY card_id
                    )
                )
            """) as cursor:
                rows = await cursor.fetchall()
                count = sum(1 for r in rows if r["action"] == AccessAction.CHECKIN.value)
                return max(0, count)

    # --- Environment Methods ---
    async def add_environment_reading(self, reading: EnvironmentReading) -> EnvironmentReading:
        timestamp_str = reading.timestamp or datetime.now().isoformat()
        reading_to_save = reading.model_copy(update={"timestamp": timestamp_str})

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO environment_readings (temperature, humidity, fan_on, timestamp)
                VALUES (?, ?, ?, ?)
            """, (
                reading_to_save.temperature,
                reading_to_save.humidity,
                1 if reading_to_save.fan_on else 0,
                reading_to_save.timestamp,
            ))
            await db.commit()
        return reading_to_save

    async def get_environment_readings(self, limit: int = 50) -> List[EnvironmentReading]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM environment_readings ORDER BY timestamp DESC LIMIT ?
            """, (limit,)) as cursor:
                rows = await cursor.fetchall()
                return [
                    EnvironmentReading(
                        temperature=row["temperature"],
                        humidity=row["humidity"],
                        fan_on=bool(row["fan_on"]),
                        timestamp=row["timestamp"],
                    )
                    for row in rows
                ]

    async def get_latest_reading(self) -> Optional[EnvironmentReading]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM environment_readings ORDER BY timestamp DESC LIMIT 1
            """) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                return EnvironmentReading(
                    temperature=row["temperature"],
                    humidity=row["humidity"],
                    fan_on=bool(row["fan_on"]),
                    timestamp=row["timestamp"],
                )
