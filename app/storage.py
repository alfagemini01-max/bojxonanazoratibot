from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import aiosqlite


@dataclass
class UserProfile:
    user_id: int
    full_name: str | None
    phone: str | None
    terms_accepted_at: str | None

    @property
    def is_registered(self) -> bool:
        return bool(self.full_name and self.phone and self.terms_accepted_at)


class UserStorage:
    def __init__(self, database_path: Path, timezone: str = "Asia/Tashkent") -> None:
        self.database_path = database_path
        self.timezone = ZoneInfo(timezone)

    async def init(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self.database_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    telegram_full_name TEXT,
                    full_name TEXT,
                    phone TEXT,
                    terms_accepted_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            await db.commit()

    def now_text(self) -> str:
        return datetime.now(self.timezone).isoformat(timespec="seconds")

    async def upsert_telegram_user(self, user_id: int, username: str | None, telegram_full_name: str | None) -> None:
        now = self.now_text()
        async with aiosqlite.connect(self.database_path) as db:
            await db.execute(
                """
                INSERT INTO users (user_id, username, telegram_full_name, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    username = excluded.username,
                    telegram_full_name = excluded.telegram_full_name,
                    updated_at = excluded.updated_at
                """,
                (user_id, username, telegram_full_name, now, now),
            )
            await db.commit()

    async def set_full_name(self, user_id: int, full_name: str) -> None:
        async with aiosqlite.connect(self.database_path) as db:
            await db.execute(
                "UPDATE users SET full_name = ?, updated_at = ? WHERE user_id = ?",
                (full_name.strip(), self.now_text(), user_id),
            )
            await db.commit()

    async def set_phone(self, user_id: int, phone: str) -> None:
        async with aiosqlite.connect(self.database_path) as db:
            await db.execute(
                "UPDATE users SET phone = ?, updated_at = ? WHERE user_id = ?",
                (phone.strip(), self.now_text(), user_id),
            )
            await db.commit()

    async def accept_terms(self, user_id: int) -> str:
        accepted_at = self.now_text()
        async with aiosqlite.connect(self.database_path) as db:
            await db.execute(
                "UPDATE users SET terms_accepted_at = ?, updated_at = ? WHERE user_id = ?",
                (accepted_at, accepted_at, user_id),
            )
            await db.commit()
        return accepted_at

    async def get_profile(self, user_id: int) -> UserProfile | None:
        async with aiosqlite.connect(self.database_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT user_id, full_name, phone, terms_accepted_at FROM users WHERE user_id = ?",
                (user_id,),
            )
            row = await cursor.fetchone()
        if not row:
            return None
        return UserProfile(
            user_id=row["user_id"],
            full_name=row["full_name"],
            phone=row["phone"],
            terms_accepted_at=row["terms_accepted_at"],
        )
