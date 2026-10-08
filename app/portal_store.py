from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import aiosqlite


logger = logging.getLogger(__name__)


POST_SEED = [
    ("35004", "Dovut-ota", "CHBP", "Qoraqalpog'iston", "KZ", 43.1355, 58.5986),
    ("35003", "Xo'jayli", "CHBP", "Qoraqalpog'iston", "TM", 42.4045, 59.4512),
    ("06010", "Olot", "CHBP", "Buxoro", "TM", 39.1537, 63.5141),
    ("10008", "Qarshi-Kerki", "CHBP", "Qashqadaryo", "TM", 38.8841, 65.7172),
    ("22017", "Ayritom", "CHBP", "Surxondaryo", "AF", 37.2251, 67.4274),
    ("22003", "Sariosiyo", "CHBP", "Surxondaryo", "TJ", 38.5065, 68.0205),
    ("18002", "Jartepa", "CHBP", "Samarqand", "TJ", 39.5309, 67.4089),
    ("27011", "Oybek", "CHBP", "Toshkent viloyati", "TJ", 40.1678, 69.6056),
    ("27013", "Bekobod avto", "CHBP", "Toshkent viloyati", "TJ", 40.2307, 69.1725),
    ("27021", "G'ishtko'prik", "CHBP", "Toshkent viloyati", "KZ", 41.4688, 69.0717),
    ("27001", "Yallama", "CHBP", "Toshkent viloyati", "KZ", 41.5852, 69.6584),
    ("24004", "Sirdaryo", "CHBP", "Sirdaryo", "KZ", 40.9284, 68.8225),
    ("03002", "Do'stlik", "CHBP", "Andijon", "KG", 40.4443, 72.3436),
    ("03006", "Qorasuv", "CHBP", "Andijon", "KG", 40.7047, 72.8823),
    ("14003", "Uchqo'rg'on", "CHBP", "Namangan", "KG", 41.1357, 72.0795),
    ("30004", "Farg'ona", "CHBP", "Farg'ona", "KG", 40.3734, 71.7603),
    ("30010", "O'zbekiston", "CHBP", "Farg'ona", "KG", 40.4168, 70.6102),
    ("30006", "Rishton", "CHBP", "Farg'ona", "KG", 40.0317, 71.0772),
    ("33001", "Shovot", "CHBP", "Xorazm", "TM", 41.6538, 60.3001),
    ("33004", "Do'stlik", "CHBP", "Xorazm", "TM", 41.3337, 60.6175),
    ("00101", "Toshkent xalqaro aeroporti", "AERO", "Toshkent shahri", "", 41.2579, 69.2812),
    ("06006", "Buxoro TIF", "TIF", "Buxoro", "", 39.7681, 64.4556),
    ("18005", "Samarqand TIF", "TIF", "Samarqand", "", 39.6542, 66.9597),
    ("22005", "Termiz TIF", "TIF", "Surxondaryo", "", 37.2611, 67.3086),
    ("22011", "Daryo porti", "PORT", "Surxondaryo", "", 37.201032, 67.299349),
    ("26002", "Toshkent-tovar TIF", "TIF", "Toshkent shahri", "", 41.296705, 69.298132),
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _json(value: Any) -> str:
    return json.dumps(value or {}, ensure_ascii=False, separators=(",", ":"))


def _public_record(row: Any) -> dict[str, Any]:
    """Convert database records to values accepted by aiohttp's JSON encoder."""
    result = dict(row)
    for key, value in result.items():
        if isinstance(value, (datetime, date)):
            result[key] = value.isoformat()
    return result


class PortalStore:
    """Small shared store for portal features, independent of rule evaluation."""

    def __init__(self, database_url: str, sqlite_path: Path, database_quota_mb: int = 0) -> None:
        self.database_url = database_url
        self.user_sqlite_path = sqlite_path
        self.sqlite_path = sqlite_path.with_name("portal_data.sqlite3")
        self.pool = None
        self.backend = "sqlite"
        self.database_limit_bytes = max(0, int(database_quota_mb)) * 1024 * 1024 or None
        self._write_lock = asyncio.Lock()

    async def initialize(self) -> None:
        if self.database_url:
            try:
                import asyncpg

                self.pool = await asyncpg.create_pool(
                    self.database_url,
                    min_size=0,
                    max_size=2,
                    command_timeout=15,
                    max_inactive_connection_lifetime=180,
                )
                await self._initialize_postgres()
                self.backend = "postgresql"
                return
            except Exception:
                logger.exception("Portal PostgreSQL unavailable")
                if self.pool:
                    await self.pool.close()
                self.pool = None
                raise
        await self._initialize_sqlite()

    async def close(self) -> None:
        if self.pool:
            await self.pool.close()
            self.pool = None

    async def _initialize_postgres(self) -> None:
        async with self.pool.acquire() as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS portal_analytics (
                    id BIGSERIAL PRIMARY KEY, event_type TEXT NOT NULL,
                    origin_code TEXT, destination_code TEXT, vehicle_code TEXT,
                    transport_type TEXT, rule_version BIGINT, error_code TEXT,
                    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS portal_analytics_created_idx ON portal_analytics(created_at DESC);
                CREATE INDEX IF NOT EXISTS portal_analytics_route_idx ON portal_analytics(event_type, vehicle_code, origin_code, destination_code);
                CREATE TABLE IF NOT EXISTS portal_feedback (
                    id BIGSERIAL PRIMARY KEY, status TEXT NOT NULL DEFAULT 'new',
                    message TEXT NOT NULL, language TEXT NOT NULL DEFAULT 'uz',
                    telegram_user_id BIGINT, origin_code TEXT, destination_code TEXT,
                    vehicle_code TEXT, transport_type TEXT, rule_version BIGINT,
                    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE TABLE IF NOT EXISTS saved_routes (
                    id BIGSERIAL PRIMARY KEY, telegram_user_id BIGINT NOT NULL,
                    origin_code TEXT NOT NULL, destination_code TEXT NOT NULL,
                    vehicle_code TEXT NOT NULL, language TEXT NOT NULL DEFAULT 'uz',
                    transport_type TEXT, active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE(telegram_user_id, origin_code, destination_code, vehicle_code)
                );
                CREATE TABLE IF NOT EXISTS notification_outbox (
                    id BIGSERIAL PRIMARY KEY, telegram_user_id BIGINT NOT NULL,
                    route_id BIGINT, rule_version BIGINT NOT NULL, language TEXT NOT NULL DEFAULT 'uz',
                    payload JSONB NOT NULL, status TEXT NOT NULL DEFAULT 'pending', attempts INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), sent_at TIMESTAMPTZ,
                    UNIQUE(telegram_user_id, route_id, rule_version)
                );
                CREATE TABLE IF NOT EXISTS customs_posts (
                    code TEXT PRIMARY KEY, name_uz TEXT NOT NULL, name_ru TEXT NOT NULL DEFAULT '', name_en TEXT NOT NULL DEFAULT '',
                    post_type TEXT NOT NULL DEFAULT 'CHBP', region TEXT NOT NULL DEFAULT '', neighbor_code TEXT NOT NULL DEFAULT '',
                    latitude DOUBLE PRECISION NOT NULL, longitude DOUBLE PRECISION NOT NULL,
                    working_hours TEXT NOT NULL DEFAULT 'Ma\u2019lumot kiritilmagan', contact TEXT NOT NULL DEFAULT '', address TEXT NOT NULL DEFAULT '',
                    allowed_transport TEXT NOT NULL DEFAULT 'Yuk va yengil transport', allowed_cargo TEXT NOT NULL DEFAULT 'Umumiy tartibda',
                    is_active BOOLEAN NOT NULL DEFAULT TRUE, updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )
        await self._seed_posts()

    async def _initialize_sqlite(self) -> None:
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self.sqlite_path) as db:
            await db.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS portal_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, event_type TEXT NOT NULL,
                    origin_code TEXT, destination_code TEXT, vehicle_code TEXT,
                    transport_type TEXT, rule_version INTEGER, error_code TEXT,
                    metadata TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS portal_analytics_created_idx ON portal_analytics(created_at);
                CREATE TABLE IF NOT EXISTS portal_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, status TEXT NOT NULL DEFAULT 'new', message TEXT NOT NULL,
                    language TEXT NOT NULL DEFAULT 'uz', telegram_user_id INTEGER, origin_code TEXT, destination_code TEXT,
                    vehicle_code TEXT, transport_type TEXT, rule_version INTEGER, metadata TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS saved_routes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, telegram_user_id INTEGER NOT NULL,
                    origin_code TEXT NOT NULL, destination_code TEXT NOT NULL, vehicle_code TEXT NOT NULL,
                    language TEXT NOT NULL DEFAULT 'uz', transport_type TEXT, active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                    UNIQUE(telegram_user_id, origin_code, destination_code, vehicle_code)
                );
                CREATE TABLE IF NOT EXISTS notification_outbox (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, telegram_user_id INTEGER NOT NULL, route_id INTEGER,
                    rule_version INTEGER NOT NULL, language TEXT NOT NULL DEFAULT 'uz', payload TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending', attempts INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL, sent_at TEXT,
                    UNIQUE(telegram_user_id, route_id, rule_version)
                );
                CREATE TABLE IF NOT EXISTS customs_posts (
                    code TEXT PRIMARY KEY, name_uz TEXT NOT NULL, name_ru TEXT NOT NULL DEFAULT '', name_en TEXT NOT NULL DEFAULT '',
                    post_type TEXT NOT NULL DEFAULT 'CHBP', region TEXT NOT NULL DEFAULT '', neighbor_code TEXT NOT NULL DEFAULT '',
                    latitude REAL NOT NULL, longitude REAL NOT NULL, working_hours TEXT NOT NULL DEFAULT 'Ma\u2019lumot kiritilmagan',
                    contact TEXT NOT NULL DEFAULT '', address TEXT NOT NULL DEFAULT '', allowed_transport TEXT NOT NULL DEFAULT 'Yuk va yengil transport',
                    allowed_cargo TEXT NOT NULL DEFAULT 'Umumiy tartibda', is_active INTEGER NOT NULL DEFAULT 1, updated_at TEXT NOT NULL
                );
                """
            )
            await db.commit()
        await self._seed_posts()

    async def _seed_posts(self) -> None:
        if self.pool:
            async with self.pool.acquire() as db:
                for code, name, kind, region, neighbor, lat, lon in POST_SEED:
                    await db.execute(
                        """INSERT INTO customs_posts(code,name_uz,post_type,region,neighbor_code,latitude,longitude)
                           VALUES($1,$2,$3,$4,$5,$6,$7) ON CONFLICT(code) DO NOTHING""",
                        code, name, kind, region, neighbor, lat, lon,
                    )
            return
        async with aiosqlite.connect(self.sqlite_path) as db:
            await db.executemany(
                """INSERT OR IGNORE INTO customs_posts
                   (code,name_uz,post_type,region,neighbor_code,latitude,longitude,updated_at)
                   VALUES(?,?,?,?,?,?,?,?)""",
                [(code, name, kind, region, neighbor, lat, lon, _now()) for code, name, kind, region, neighbor, lat, lon in POST_SEED],
            )
            await db.commit()

    async def record_event(self, event_type: str, **values: Any) -> None:
        params = (
            event_type, values.get("origin_code"), values.get("destination_code"), values.get("vehicle_code"),
            values.get("transport_type"), values.get("rule_version"), values.get("error_code"), _json(values.get("metadata")),
        )
        try:
            if self.pool:
                async with self.pool.acquire() as db:
                    await db.execute(
                        """INSERT INTO portal_analytics(event_type,origin_code,destination_code,vehicle_code,transport_type,rule_version,error_code,metadata)
                           VALUES($1,$2,$3,$4,$5,$6,$7,$8::jsonb)""", *params,
                    )
            else:
                async with aiosqlite.connect(self.sqlite_path) as db:
                    await db.execute(
                        """INSERT INTO portal_analytics(event_type,origin_code,destination_code,vehicle_code,transport_type,rule_version,error_code,metadata,created_at)
                           VALUES(?,?,?,?,?,?,?,?,?)""", (*params, _now()),
                    )
                    await db.commit()
        except Exception:
            logger.exception("Analytics event could not be persisted")

    async def analytics_summary(self, days: int = 30) -> dict[str, Any]:
        days = max(1, min(365, int(days)))
        if self.pool:
            async with self.pool.acquire() as db:
                total = await db.fetchval("SELECT COUNT(*) FROM portal_analytics WHERE created_at >= NOW()-($1::int*INTERVAL '1 day')", days)
                countries = await db.fetch("""SELECT vehicle_code code,COUNT(*) count FROM portal_analytics WHERE created_at >= NOW()-($1::int*INTERVAL '1 day') AND vehicle_code IS NOT NULL GROUP BY vehicle_code ORDER BY count DESC LIMIT 10""", days)
                routes = await db.fetch("""SELECT origin_code,destination_code,vehicle_code,COUNT(*) count FROM portal_analytics WHERE created_at >= NOW()-($1::int*INTERVAL '1 day') AND event_type IN ('permit_check','fee_check') GROUP BY origin_code,destination_code,vehicle_code ORDER BY count DESC LIMIT 10""", days)
                errors = await db.fetch("""SELECT COALESCE(error_code,'unknown') code,COUNT(*) count FROM portal_analytics WHERE created_at >= NOW()-($1::int*INTERVAL '1 day') AND event_type='error' GROUP BY error_code ORDER BY count DESC LIMIT 10""", days)
                missing = await db.fetchval("SELECT COUNT(*) FROM portal_analytics WHERE created_at >= NOW()-($1::int*INTERVAL '1 day') AND error_code='rule_missing'", days)
        else:
            cutoff = datetime.now(timezone.utc).timestamp() - days * 86400
            cutoff_text = datetime.fromtimestamp(cutoff, timezone.utc).isoformat(timespec="seconds")
            async with aiosqlite.connect(self.sqlite_path) as db:
                db.row_factory = aiosqlite.Row
                total = (await (await db.execute("SELECT COUNT(*) FROM portal_analytics WHERE created_at>=?", (cutoff_text,))).fetchone())[0]
                countries = await (await db.execute("SELECT vehicle_code code,COUNT(*) count FROM portal_analytics WHERE created_at>=? AND vehicle_code IS NOT NULL GROUP BY vehicle_code ORDER BY count DESC LIMIT 10", (cutoff_text,))).fetchall()
                routes = await (await db.execute("SELECT origin_code,destination_code,vehicle_code,COUNT(*) count FROM portal_analytics WHERE created_at>=? AND event_type IN ('permit_check','fee_check') GROUP BY origin_code,destination_code,vehicle_code ORDER BY count DESC LIMIT 10", (cutoff_text,))).fetchall()
                errors = await (await db.execute("SELECT COALESCE(error_code,'unknown') code,COUNT(*) count FROM portal_analytics WHERE created_at>=? AND event_type='error' GROUP BY error_code ORDER BY count DESC LIMIT 10", (cutoff_text,))).fetchall()
                missing = (await (await db.execute("SELECT COUNT(*) FROM portal_analytics WHERE created_at>=? AND error_code='rule_missing'", (cutoff_text,))).fetchone())[0]
        return {"total": int(total or 0), "missing_rules": int(missing or 0), "countries": [dict(row) for row in countries], "routes": [dict(row) for row in routes], "errors": [dict(row) for row in errors], "days": days, "backend": self.backend}

    async def system_status(self) -> dict[str, Any]:
        bot_users = web_visitors = saved_routes = feedback = posts = checks = 0
        database_bytes = 0
        database_limit_bytes = self.database_limit_bytes
        database_connections = 0
        database_max_connections = 0
        database_latency_ms = 0.0
        database_ok = True
        try:
            if self.pool:
                async with self.pool.acquire() as db:
                    started = asyncio.get_running_loop().time()
                    database_bytes = int(await db.fetchval("SELECT pg_database_size(current_database())") or 0)
                    database_latency_ms = round(
                        (asyncio.get_running_loop().time() - started) * 1000,
                        1,
                    )
                    database_connections = int(
                        await db.fetchval(
                            "SELECT COUNT(*) FROM pg_stat_activity WHERE datname=current_database()"
                        )
                        or 0
                    )
                    try:
                        database_max_connections = int(
                            await db.fetchval("SELECT current_setting('max_connections')::int")
                            or 0
                        )
                    except Exception:
                        database_max_connections = 0
                    users_table = await db.fetchval("SELECT to_regclass('public.users')")
                    if users_table:
                        bot_users = int(await db.fetchval("SELECT COUNT(*) FROM users") or 0)
                    web_visitors = int(await db.fetchval("SELECT COUNT(DISTINCT metadata->>'visitor_id') FROM portal_analytics WHERE COALESCE(metadata->>'visitor_id','')<>''") or 0)
                    saved_routes = int(await db.fetchval("SELECT COUNT(*) FROM saved_routes WHERE active=TRUE") or 0)
                    feedback = int(await db.fetchval("SELECT COUNT(*) FROM portal_feedback WHERE status IN ('new','reviewing')") or 0)
                    posts = int(await db.fetchval("SELECT COUNT(*) FROM customs_posts WHERE is_active=TRUE") or 0)
                    checks = int(await db.fetchval("SELECT COUNT(*) FROM portal_analytics WHERE event_type IN ('permit_check','fee_check')") or 0)
            else:
                database_bytes = sum(path.stat().st_size for path in (self.sqlite_path, self.user_sqlite_path) if path.exists())
                async with aiosqlite.connect(self.sqlite_path) as db:
                    web_visitors = int((await (await db.execute("SELECT COUNT(DISTINCT json_extract(metadata,'$.visitor_id')) FROM portal_analytics WHERE COALESCE(json_extract(metadata,'$.visitor_id'),'')<>''")).fetchone())[0] or 0)
                    saved_routes = int((await (await db.execute("SELECT COUNT(*) FROM saved_routes WHERE active=1")).fetchone())[0] or 0)
                    feedback = int((await (await db.execute("SELECT COUNT(*) FROM portal_feedback WHERE status IN ('new','reviewing')")).fetchone())[0] or 0)
                    posts = int((await (await db.execute("SELECT COUNT(*) FROM customs_posts WHERE is_active=1")).fetchone())[0] or 0)
                    checks = int((await (await db.execute("SELECT COUNT(*) FROM portal_analytics WHERE event_type IN ('permit_check','fee_check')")).fetchone())[0] or 0)
                if self.user_sqlite_path.exists():
                    async with aiosqlite.connect(self.user_sqlite_path) as db:
                        users_table = await (
                            await db.execute(
                                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='users'"
                            )
                        ).fetchone()
                        if users_table:
                            bot_users = int(
                                (await (await db.execute("SELECT COUNT(*) FROM users")).fetchone())[0]
                                or 0
                            )
        except Exception:
            database_ok = False
            logger.exception("System statistics could not be read")

        memory_bytes = 0
        try:
            if os.path.exists("/proc/self/status"):
                for line in Path("/proc/self/status").read_text(encoding="utf-8").splitlines():
                    if line.startswith("VmRSS:"):
                        memory_bytes = int(line.split()[1]) * 1024
                        break
        except (OSError, ValueError):
            pass
        return {
            "database": {
                "ok": database_ok,
                "backend": self.backend,
                "used_bytes": database_bytes,
                "limit_bytes": database_limit_bytes,
                "free_bytes": (
                    max(0, database_limit_bytes - database_bytes)
                    if database_limit_bytes is not None
                    else None
                ),
                "quota_configured": database_limit_bytes is not None,
                "connections": database_connections,
                "max_connections": database_max_connections,
                "latency_ms": database_latency_ms,
            },
            "process": {"memory_bytes": memory_bytes},
            "usage": {
                "bot_users": bot_users,
                "web_visitors": web_visitors,
                "saved_routes": saved_routes,
                "open_feedback": feedback,
                "active_posts": posts,
                "checks": checks,
            },
        }

    async def create_feedback(self, body: dict[str, Any]) -> int:
        message = str(body.get("message") or "").strip()
        if not 5 <= len(message) <= 2000:
            raise ValueError("Xabar 5-2000 belgi oralig'ida bo'lishi kerak.")
        fields = (message, str(body.get("lang") or "uz"), body.get("telegram_user_id"), body.get("origin"), body.get("destination"), body.get("vehicle"), body.get("transport_type"), body.get("rule_version"), _json(body.get("metadata")))
        if self.pool:
            async with self.pool.acquire() as db:
                return int(await db.fetchval("""INSERT INTO portal_feedback(message,language,telegram_user_id,origin_code,destination_code,vehicle_code,transport_type,rule_version,metadata) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9::jsonb) RETURNING id""", *fields))
        now = _now()
        async with aiosqlite.connect(self.sqlite_path) as db:
            cursor = await db.execute("""INSERT INTO portal_feedback(message,language,telegram_user_id,origin_code,destination_code,vehicle_code,transport_type,rule_version,metadata,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)""", (*fields, now, now))
            await db.commit()
            return int(cursor.lastrowid)

    async def list_feedback(self, limit: int = 100) -> list[dict[str, Any]]:
        limit = max(1, min(200, int(limit)))
        if self.pool:
            async with self.pool.acquire() as db:
                rows = await db.fetch("SELECT * FROM portal_feedback ORDER BY id DESC LIMIT $1", limit)
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                db.row_factory = aiosqlite.Row
                rows = await (await db.execute("SELECT * FROM portal_feedback ORDER BY id DESC LIMIT ?", (limit,))).fetchall()
        return [_public_record(row) for row in rows]

    async def set_feedback_status(self, feedback_id: int, status: str) -> None:
        if status not in {"new", "reviewing", "resolved", "rejected"}:
            raise ValueError("Murojaat holati noto'g'ri.")
        if self.pool:
            async with self.pool.acquire() as db:
                await db.execute("UPDATE portal_feedback SET status=$1,updated_at=NOW() WHERE id=$2", status, feedback_id)
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                await db.execute("UPDATE portal_feedback SET status=?,updated_at=? WHERE id=?", (status, _now(), feedback_id))
                await db.commit()

    async def list_posts(self, include_inactive: bool = False) -> list[dict[str, Any]]:
        where = "" if include_inactive else " WHERE is_active=" + ("TRUE" if self.pool else "1")
        query = "SELECT * FROM customs_posts" + where + " ORDER BY region,name_uz"
        if self.pool:
            async with self.pool.acquire() as db:
                rows = await db.fetch(query)
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                db.row_factory = aiosqlite.Row
                rows = await (await db.execute(query)).fetchall()
        return [_public_record(row) for row in rows]

    async def save_post(self, body: dict[str, Any]) -> dict[str, Any]:
        code = str(body.get("code") or "").strip()
        name = str(body.get("name_uz") or "").strip()
        if not code or not name:
            raise ValueError("Post kodi va nomi majburiy.")
        lat, lon = float(body.get("latitude")), float(body.get("longitude"))
        if not 35 <= lat <= 46 or not 55 <= lon <= 75:
            raise ValueError("Koordinata O'zbekiston hududiga mos emas.")
        values = (code, name, str(body.get("name_ru") or ""), str(body.get("name_en") or ""), str(body.get("post_type") or "CHBP"), str(body.get("region") or ""), str(body.get("neighbor_code") or ""), lat, lon, str(body.get("working_hours") or "Ma'lumot kiritilmagan"), str(body.get("contact") or ""), str(body.get("address") or ""), str(body.get("allowed_transport") or "Yuk va yengil transport"), str(body.get("allowed_cargo") or "Umumiy tartibda"), bool(body.get("is_active", True)))
        async with self._write_lock:
            if self.pool:
                async with self.pool.acquire() as db:
                    await db.execute("""INSERT INTO customs_posts(code,name_uz,name_ru,name_en,post_type,region,neighbor_code,latitude,longitude,working_hours,contact,address,allowed_transport,allowed_cargo,is_active) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15) ON CONFLICT(code) DO UPDATE SET name_uz=EXCLUDED.name_uz,name_ru=EXCLUDED.name_ru,name_en=EXCLUDED.name_en,post_type=EXCLUDED.post_type,region=EXCLUDED.region,neighbor_code=EXCLUDED.neighbor_code,latitude=EXCLUDED.latitude,longitude=EXCLUDED.longitude,working_hours=EXCLUDED.working_hours,contact=EXCLUDED.contact,address=EXCLUDED.address,allowed_transport=EXCLUDED.allowed_transport,allowed_cargo=EXCLUDED.allowed_cargo,is_active=EXCLUDED.is_active,updated_at=NOW()""", *values)
            else:
                async with aiosqlite.connect(self.sqlite_path) as db:
                    await db.execute("""INSERT INTO customs_posts(code,name_uz,name_ru,name_en,post_type,region,neighbor_code,latitude,longitude,working_hours,contact,address,allowed_transport,allowed_cargo,is_active,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(code) DO UPDATE SET name_uz=excluded.name_uz,name_ru=excluded.name_ru,name_en=excluded.name_en,post_type=excluded.post_type,region=excluded.region,neighbor_code=excluded.neighbor_code,latitude=excluded.latitude,longitude=excluded.longitude,working_hours=excluded.working_hours,contact=excluded.contact,address=excluded.address,allowed_transport=excluded.allowed_transport,allowed_cargo=excluded.allowed_cargo,is_active=excluded.is_active,updated_at=excluded.updated_at""", (*values[:-1], int(values[-1]), _now()))
                    await db.commit()
        return {"code": code, "name_uz": name}

    async def delete_post(self, code: str) -> None:
        if self.pool:
            async with self.pool.acquire() as db:
                await db.execute("UPDATE customs_posts SET is_active=FALSE,updated_at=NOW() WHERE code=$1", code)
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                await db.execute("UPDATE customs_posts SET is_active=0,updated_at=? WHERE code=?", (_now(), code))
                await db.commit()

    async def save_route(self, telegram_user_id: int, body: dict[str, Any]) -> None:
        fields = (int(telegram_user_id), str(body["origin"]), str(body["destination"]), str(body["vehicle"]), str(body.get("lang") or "uz"), str(body.get("transport_type") or ""))
        if self.pool:
            async with self.pool.acquire() as db:
                await db.execute("""INSERT INTO saved_routes(telegram_user_id,origin_code,destination_code,vehicle_code,language,transport_type) VALUES($1,$2,$3,$4,$5,$6) ON CONFLICT(telegram_user_id,origin_code,destination_code,vehicle_code) DO UPDATE SET active=TRUE,language=EXCLUDED.language,transport_type=EXCLUDED.transport_type,updated_at=NOW()""", *fields)
        else:
            now = _now()
            async with aiosqlite.connect(self.sqlite_path) as db:
                await db.execute("""INSERT INTO saved_routes(telegram_user_id,origin_code,destination_code,vehicle_code,language,transport_type,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(telegram_user_id,origin_code,destination_code,vehicle_code) DO UPDATE SET active=1,language=excluded.language,transport_type=excluded.transport_type,updated_at=excluded.updated_at""", (*fields, now, now))
                await db.commit()

    async def enqueue_rule_notifications(self, version: int, changed_codes: list[str], source: str) -> int:
        codes = sorted({str(code).zfill(3) for code in changed_codes if str(code).strip()})
        payload = _json({"version": version, "changed_codes": codes, "source": source})
        if self.pool:
            async with self.pool.acquire() as db:
                if codes:
                    await db.execute("""INSERT INTO notification_outbox(telegram_user_id,route_id,rule_version,language,payload) SELECT telegram_user_id,id,$1,language,$2::jsonb FROM saved_routes WHERE active=TRUE AND (origin_code=ANY($3::text[]) OR destination_code=ANY($3::text[]) OR vehicle_code=ANY($3::text[])) ON CONFLICT DO NOTHING""", version, payload, codes)
                else:
                    await db.execute("""INSERT INTO notification_outbox(telegram_user_id,route_id,rule_version,language,payload) SELECT telegram_user_id,id,$1,language,$2::jsonb FROM saved_routes WHERE active=TRUE ON CONFLICT DO NOTHING""", version, payload)
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                if codes:
                    placeholders = ",".join("?" for _ in codes)
                    await db.execute(f"""INSERT OR IGNORE INTO notification_outbox(telegram_user_id,route_id,rule_version,language,payload,created_at) SELECT telegram_user_id,id,?,language,?,? FROM saved_routes WHERE active=1 AND (origin_code IN ({placeholders}) OR destination_code IN ({placeholders}) OR vehicle_code IN ({placeholders}))""", (version, payload, _now(), *codes, *codes, *codes))
                else:
                    await db.execute("""INSERT OR IGNORE INTO notification_outbox(telegram_user_id,route_id,rule_version,language,payload,created_at) SELECT telegram_user_id,id,?,language,?,? FROM saved_routes WHERE active=1""", (version, payload, _now()))
                await db.commit()
        return 1

    async def pending_notifications(self, limit: int = 25) -> list[dict[str, Any]]:
        if self.pool:
            async with self.pool.acquire() as db:
                rows = await db.fetch("SELECT * FROM notification_outbox WHERE status='pending' AND attempts<5 ORDER BY id LIMIT $1", limit)
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                db.row_factory = aiosqlite.Row
                rows = await (await db.execute("SELECT * FROM notification_outbox WHERE status='pending' AND attempts<5 ORDER BY id LIMIT ?", (limit,))).fetchall()
        return [dict(row) for row in rows]

    async def finish_notification(self, item_id: int, sent: bool) -> None:
        if self.pool:
            async with self.pool.acquire() as db:
                await db.execute("UPDATE notification_outbox SET status=$1,attempts=attempts+1,sent_at=CASE WHEN $2 THEN NOW() ELSE sent_at END WHERE id=$3", "sent" if sent else "pending", sent, item_id)
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                await db.execute("UPDATE notification_outbox SET status=?,attempts=attempts+1,sent_at=CASE WHEN ? THEN ? ELSE sent_at END WHERE id=?", ("sent" if sent else "pending", int(sent), _now(), item_id))
                await db.commit()
