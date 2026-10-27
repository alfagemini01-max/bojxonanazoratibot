from __future__ import annotations

import asyncio
import json
import logging
import os
import secrets
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import aiosqlite


logger = logging.getLogger(__name__)


POST_SEED = [
    # Qoraqalpogʻiston Respublikasi boʻyicha
    ("35001", "Nukus aeroporti", "AERO", "Qoraqalpog'iston", "", 42.4869, 59.6223),
    ("35002", "Nukus TIF", "TIF", "Qoraqalpog'iston", "", 42.4602, 59.6166),
    ("35003", "Xo'jayli", "CHBP", "Qoraqalpog'iston", "TM", 42.4045, 59.4512),
    ("35004", "Dovut-ota", "CHBP", "Qoraqalpog'iston", "KZ", 43.1355, 58.5986),
    ("35010", "Qoraqalpog'iston temir yo'l", "RW", "Qoraqalpog'iston", "KZ", 44.8876, 56.0354),

    # Andijon viloyati boʻyicha
    ("03002", "Do'stlik", "CHBP", "Andijon", "KG", 40.4443, 72.3436),
    ("03003", "Andijon aeroporti", "AERO", "Andijon", "", 40.7289, 72.2936),
    ("03005", "Mingtepa", "CHBP", "Andijon", "KG", 40.4285, 72.2854),
    ("03006", "Qorasuv", "CHBP", "Andijon", "KG", 40.7047, 72.8823),
    ("03007", "Xonobod", "CHBP", "Andijon", "KG", 40.8012, 72.9984),
    ("03008", "Pushmon", "CHBP", "Andijon", "KG", 40.6124, 72.4112),
    ("03009", "Madaniyat", "CHBP", "Andijon", "KG", 40.8521, 72.8856),
    ("03011", "Andijon TIF", "TIF", "Andijon", "", 40.7821, 72.3442),
    ("03013", "Keskanyor", "CHBP", "Andijon", "KG", 40.5214, 72.1895),
    ("03014", "Savay temir yo'l", "RW", "Andijon", "KG", 40.7891, 72.8541),
    ("03015", "Asaka TIF", "TIF", "Andijon", "", 40.6415, 72.2389),

    # Buxoro viloyati boʻyicha
    ("06001", "Buxoro aeroporti", "AERO", "Buxoro", "", 39.7753, 64.4831),
    ("06006", "Buxoro TIF", "TIF", "Buxoro", "", 39.7681, 64.4556),
    ("06009", "Qorako'l TIF", "TIF", "Buxoro", "", 39.5012, 63.8561),
    ("06010", "Olot", "CHBP", "Buxoro", "TM", 39.1537, 63.5141),
    ("06011", "Xo'jadavlat temir yo'l", "RW", "Buxoro", "TM", 39.2312, 63.6541),

    # Jizzax viloyati boʻyicha
    ("08003", "Uchto'rg'on", "CHBP", "Jizzax", "TJ", 40.1254, 67.8451),
    ("08004", "Jizzax TIF", "TIF", "Jizzax", "", 40.1158, 67.8422),
    ("08007", "Qo'shkent", "CHBP", "Jizzax", "TJ", 40.0521, 68.2145),

    # Qashqadaryo viloyati boʻyicha
    ("10002", "Nasaf TIF", "TIF", "Qashqadaryo", "", 38.8612, 65.7891),
    ("10007", "Qamashi-G'uzor TIF", "TIF", "Qashqadaryo", "", 38.6214, 66.2541),
    ("10008", "Qarshi-Kerki", "CHBP", "Qashqadaryo", "TM", 38.8841, 65.7172),
    ("10012", "Qarshi aeroporti", "AERO", "Qashqadaryo", "", 38.8341, 65.7725),

    # Navoiy viloyati boʻyicha
    ("12002", "Navoiy aeroporti", "AERO", "Navoiy", "", 40.1189, 65.1764),
    ("12003", "Navoiy TIF", "TIF", "Navoiy", "", 40.0841, 65.3789),
    ("12008", "Zarafshon TIF", "TIF", "Navoiy", "", 41.5721, 64.2145),

    # Namangan viloyati boʻyicha
    ("14002", "Namangan aeroporti", "AERO", "Namangan", "", 40.9842, 71.5583),
    ("14003", "Uchqo'rg'on", "CHBP", "Namangan", "KG", 41.1357, 72.0795),
    ("14004", "Kosonsoy", "CHBP", "Namangan", "KG", 41.2541, 71.5489),
    ("14005", "Pop", "CHBP", "Namangan", "TJ", 40.8741, 71.1025),
    ("14010", "Namangan TIF", "TIF", "Namangan", "", 40.9981, 71.6725),

    # Samarqand viloyati boʻyicha
    ("18001", "Samarqand aeroporti", "AERO", "Samarqand", "", 39.7005, 66.9839),
    ("18002", "Jartepa", "CHBP", "Samarqand", "TJ", 39.5309, 67.4089),
    ("18005", "Samarqand TIF", "TIF", "Samarqand", "", 39.6542, 66.9597),
    ("18007", "Ulug'bek TIF", "TIF", "Samarqand", "", 39.6741, 66.9215),

    # Surxondaryo viloyati boʻyicha
    ("22002", "Termiz aeroporti", "AERO", "Surxondaryo", "", 37.2867, 67.3094),
    ("22003", "Sariosiyo", "CHBP", "Surxondaryo", "TJ", 38.5065, 68.0205),
    ("22004", "Sariosiyo temir yo'l", "RW", "Surxondaryo", "TJ", 38.4891, 67.9854),
    ("22005", "Termiz TIF", "TIF", "Surxondaryo", "", 37.2611, 67.3086),
    ("22006", "Denov TIF", "TIF", "Surxondaryo", "", 38.2741, 67.8954),
    ("22007", "Gulbahor", "CHBP", "Surxondaryo", "TJ", 37.3854, 67.6214),
    ("22011", "Daryo porti", "PORT", "Surxondaryo", "AF", 37.2010, 67.2993),
    ("22015", "Boldir temir yo'l", "RW", "Surxondaryo", "TM", 37.3541, 67.4521),
    ("22017", "Ayritom", "CHBP", "Surxondaryo", "AF", 37.2251, 67.4274),
    ("22022", "Termiz xalqaro savdo markazi TIF", "TIF", "Surxondaryo", "", 37.2145, 67.4012),

    # Sirdaryo viloyati boʻyicha
    ("24002", "Xovosobod", "CHBP", "Sirdaryo", "TJ", 40.2145, 69.0521),
    ("24004", "Sirdaryo", "CHBP", "Sirdaryo", "KZ", 40.9284, 68.8225),
    ("24006", "Oq oltin", "CHBP", "Sirdaryo", "KZ", 40.3541, 68.9125),
    ("24009", "Guliston TIF", "TIF", "Sirdaryo", "", 40.4891, 68.7845),
    ("24014", "Malik", "CHBP", "Sirdaryo", "KZ", 40.8541, 68.6541),

    # Toshkent viloyati boʻyicha
    ("27001", "Yallama", "CHBP", "Toshkent viloyati", "KZ", 41.5852, 69.6584),
    ("27008", "Navoiy", "CHBP", "Toshkent viloyati", "KZ", 41.4214, 69.2145),
    ("27009", "S. Najimov", "CHBP", "Toshkent viloyati", "KZ", 41.5142, 69.3521),
    ("27011", "Oybek", "CHBP", "Toshkent viloyati", "TJ", 40.1678, 69.6056),
    ("27013", "Bekobod avto", "CHBP", "Toshkent viloyati", "TJ", 40.2307, 69.1725),
    ("27014", "Chirchiq TIF", "TIF", "Toshkent viloyati", "", 41.4689, 69.5841),
    ("27015", "Olmaliq TIF", "TIF", "Toshkent viloyati", "", 40.8541, 69.5984),
    ("27016", "Yangiyo'l TIF", "TIF", "Toshkent viloyati", "", 41.1145, 69.0521),
    ("27019", "Nazarbek TIF", "TIF", "Toshkent viloyati", "", 41.3125, 69.1452),
    ("27020", "Keles TIF", "TIF", "Toshkent viloyati", "", 41.4012, 69.2014),
    ("27021", "G'ishtko'prik", "CHBP", "Toshkent viloyati", "KZ", 41.4688, 69.0717),
    ("27023", "Farhod", "CHBP", "Toshkent viloyati", "TJ", 40.2145, 69.2541),
    ("27024", "Bekobod temir yo'l", "RW", "Toshkent viloyati", "TJ", 40.2189, 69.2214),
    ("27028", "Angren TIF", "TIF", "Toshkent viloyati", "", 41.0145, 70.1425),

    # Fargʻona viloyati boʻyicha
    ("30001", "Farg'ona aeroporti", "AERO", "Farg'ona", "", 40.3586, 71.7456),
    ("30002", "Qo'qon TIF", "TIF", "Farg'ona", "", 40.5289, 70.9421),
    ("30004", "Farg'ona", "CHBP", "Farg'ona", "KG", 40.3734, 71.7603),
    ("30005", "Andarxon", "CHBP", "Farg'ona", "TJ", 40.2854, 70.7854),
    ("30006", "Rishton", "CHBP", "Farg'ona", "KG", 40.0317, 71.0772),
    ("30008", "Rovot", "CHBP", "Farg'ona", "TJ", 40.1854, 70.9541),
    ("30009", "Vodiy TIF", "TIF", "Farg'ona", "", 40.4214, 71.6845),
    ("30010", "O'zbekiston", "CHBP", "Farg'ona", "KG", 40.4168, 70.6102),
    ("30012", "So'x", "CHBP", "Farg'ona", "KG", 39.9541, 71.1245),

    # Xorazm viloyati boʻyicha
    ("33001", "Shovot", "CHBP", "Xorazm", "TM", 41.6538, 60.3001),
    ("33004", "Do'stlik", "CHBP", "Xorazm", "TM", 41.3337, 60.6175),
    ("33007", "Urganch TIF", "TIF", "Xorazm", "", 41.5541, 60.6241),
    ("33011", "Urganch aeroporti", "AERO", "Xorazm", "", 41.5839, 60.6425),
    ("33033", "Shovot chegaraoldi savdo zonasi", "CHBP", "Xorazm", "TM", 41.6741, 60.2845),

    # Toshkent shahri boʻyicha
    ("26002", "Toshkent-tovar TIF", "TIF", "Toshkent shahri", "", 41.2967, 69.2981),
    ("26003", "Ark buloq TIF", "TIF", "Toshkent shahri", "", 41.2641, 69.1845),
    ("26004", "Chuqursoy TIF", "TIF", "Toshkent shahri", "", 41.3854, 69.2541),
    ("26009", "Keles temir yo'l", "RW", "Toshkent shahri", "KZ", 41.4012, 69.2014),
    ("26010", "Sirg'ali TIF", "TIF", "Toshkent shahri", "", 41.2214, 69.2451),
    ("26013", "Chuqursoy texnik idora temir yo'l", "RW", "Toshkent shahri", "KZ", 41.3891, 69.2512),

    # “Toshkent-AERO” ixtisoslashtirilgan bojxona kompleksi
    ("00101", "Toshkent xalqaro aeroporti", "AERO", "Toshkent shahri", "", 41.2579, 69.2812),
    ("00102", "Avia yuklar TIF", "TIF", "Toshkent shahri", "", 41.2612, 69.2845),
    ("00107", "Elektron tijorat TIF", "TIF", "Toshkent shahri", "", 41.2689, 69.2912),
    ("00110", "Toshkent-Humo aeroporti", "AERO", "Toshkent shahri", "", 41.2941, 69.3145),
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


def _inspector_record(row: Any, *, include_token: bool = False) -> dict[str, Any]:
    result = _public_record(row)
    payload = result.get("payload")
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except (TypeError, ValueError, json.JSONDecodeError):
            payload = {}
    result["payload"] = payload if isinstance(payload, dict) else {}
    if not include_token:
        result.pop("public_token", None)
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
                CREATE TABLE IF NOT EXISTS inspector_documents (
                    id BIGSERIAL PRIMARY KEY,
                    document_no TEXT NOT NULL UNIQUE,
                    public_token TEXT NOT NULL UNIQUE,
                    status TEXT NOT NULL DEFAULT 'active',
                    inspector_name TEXT NOT NULL,
                    driver_name TEXT NOT NULL,
                    vehicle_plate TEXT NOT NULL,
                    post_code TEXT NOT NULL DEFAULT '',
                    post_name TEXT NOT NULL,
                    crossing_at TEXT NOT NULL,
                    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS notification_outbox_pending_idx
                    ON notification_outbox(status, attempts, id);
                CREATE INDEX IF NOT EXISTS saved_routes_origin_idx
                    ON saved_routes(origin_code) WHERE active = true;
                CREATE INDEX IF NOT EXISTS saved_routes_dest_idx
                    ON saved_routes(destination_code) WHERE active = true;
                CREATE INDEX IF NOT EXISTS saved_routes_vehicle_idx
                    ON saved_routes(vehicle_code) WHERE active = true;
                CREATE INDEX IF NOT EXISTS portal_analytics_event_idx
                    ON portal_analytics(event_type, created_at DESC);
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
                CREATE TABLE IF NOT EXISTS inspector_documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_no TEXT NOT NULL UNIQUE,
                    public_token TEXT NOT NULL UNIQUE,
                    status TEXT NOT NULL DEFAULT 'active',
                    inspector_name TEXT NOT NULL,
                    driver_name TEXT NOT NULL,
                    vehicle_plate TEXT NOT NULL,
                    post_code TEXT NOT NULL DEFAULT '',
                    post_name TEXT NOT NULL,
                    crossing_at TEXT NOT NULL,
                    payload TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS notification_outbox_pending_idx
                    ON notification_outbox(status, attempts, id);
                CREATE INDEX IF NOT EXISTS saved_routes_origin_idx
                    ON saved_routes(origin_code);
                CREATE INDEX IF NOT EXISTS saved_routes_dest_idx
                    ON saved_routes(destination_code);
                CREATE INDEX IF NOT EXISTS saved_routes_vehicle_idx
                    ON saved_routes(vehicle_code);
                CREATE INDEX IF NOT EXISTS portal_analytics_event_idx
                    ON portal_analytics(event_type, created_at);
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
                           VALUES($1,$2,$3,$4,$5,$6,$7)
                           ON CONFLICT(code) DO UPDATE SET
                           name_uz=EXCLUDED.name_uz,
                           post_type=EXCLUDED.post_type,
                           region=EXCLUDED.region,
                           neighbor_code=EXCLUDED.neighbor_code,
                           latitude=COALESCE(customs_posts.latitude, EXCLUDED.latitude),
                           longitude=COALESCE(customs_posts.longitude, EXCLUDED.longitude)""",
                        code, name, kind, region, neighbor, lat, lon,
                    )
            return
        async with aiosqlite.connect(self.sqlite_path) as db:
            await db.executemany(
                """INSERT INTO customs_posts
                   (code,name_uz,post_type,region,neighbor_code,latitude,longitude,updated_at)
                   VALUES(?,?,?,?,?,?,?,?)
                   ON CONFLICT(code) DO UPDATE SET
                   name_uz=excluded.name_uz,
                   post_type=excluded.post_type,
                   region=excluded.region,
                   neighbor_code=excluded.neighbor_code,
                   latitude=COALESCE(customs_posts.latitude, excluded.latitude),
                   longitude=COALESCE(customs_posts.longitude, excluded.longitude),
                   updated_at=excluded.updated_at""",
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

    async def create_inspector_document(self, body: dict[str, Any], actor: str) -> dict[str, Any]:
        def text(name: str, minimum: int, maximum: int, default: str = "") -> str:
            value = str(body.get(name) or default).strip()
            if not minimum <= len(value) <= maximum:
                raise ValueError(f"{name}: {minimum}-{maximum} belgi oralig'ida bo'lishi kerak.")
            return value

        driver_name = text("driver_name", 2, 160)
        vehicle_plate = text("vehicle_plate", 2, 40).upper()

        post_code = str(body.get("post_code") or "").strip()[:40]
        post_name_default = ""
        if post_code:
            for seed in POST_SEED:
                if seed[0] == post_code:
                    post_name_default = f"{seed[1]} posti"
                    break
        post_name = str(body.get("post_name") or post_name_default or f"Bojxona posti {post_code}".strip() or "Bojxona posti")[:180]

        crossing_at = str(body.get("crossing_at") or body.get("crossing_time") or _now()[:16].replace("T", " "))[:64]
        inspector_name = text("inspector_name", 2, 160, actor or "Navbatchi inspektor")

        raw_documents = body.get("documents") or []
        if not isinstance(raw_documents, list) or len(raw_documents) == 0:
            raw_documents = [{"code": "INV", "title": "Invoys / Yuk xati", "status": "Rasmiylashtirilgan", "description": "Asosiy hujjat"}]

        normalized_documents: list[dict[str, str]] = []
        for index, item in enumerate(raw_documents[:12], 1):
            if not isinstance(item, dict):
                continue
            code = str(item.get("code") or item.get("type") or item.get("number") or f"DOC-{index}").strip().upper()[:80]
            title = str(item.get("title") or item.get("type") or item.get("number") or "Rasmiy hujjat").strip()[:180]
            status = str(item.get("status") or "Rasmiylashtirilgan").strip()[:80]
            description = str(item.get("description") or item.get("note") or item.get("number") or "").strip()[:500]
            if len(code) < 1:
                code = f"DOC-{index}"
            if len(title) < 1:
                title = "Hujjat"
            normalized_documents.append(
                {"code": code, "title": title, "status": status, "description": description}
            )

        if not normalized_documents:
            normalized_documents.append(
                {"code": "INV", "title": "Invoys / Yuk xati", "status": "Rasmiylashtirilgan", "description": "Asosiy hujjat"}
            )

        allowed_vehicle_images = {
            "auto", "sedan", "hatchback", "suv", "minivan", "pickup", "microbus", "city-bus",
            "coach-bus", "cargo-van", "box-truck", "dump-truck", "tanker-truck", "refrigerated-truck",
            "flatbed-truck", "tractor-unit", "box-semitrailer", "curtain-semitrailer", "container-truck",
            "car-carrier", "heavy-haul-lowboy",
        }
        vehicle_image_type = str(body.get("vehicle_image_type") or "auto").strip().lower()
        if vehicle_image_type not in allowed_vehicle_images:
            vehicle_image_type = "auto"
        try:
            payment_total_uzs = max(0, min(10_000_000_000_000, int(float(body.get("payment_total_uzs") or 0))))
        except (TypeError, ValueError):
            payment_total_uzs = 0

        payload = {
            "nationality": str(body.get("nationality") or body.get("driver_country") or "UZ").strip()[:120],
            "passport": str(body.get("passport") or body.get("driver_passport") or "").strip().upper()[:80],
            "phone": str(body.get("phone") or body.get("driver_phone") or "").strip()[:80],
            "vehicle_country": str(body.get("vehicle_country") or "UZ").strip()[:120],
            "vehicle_model": str(body.get("vehicle_model") or "").strip()[:160],
            "vehicle_image_type": vehicle_image_type,
            "trailer_plate": str(body.get("trailer_plate") or "").strip().upper()[:80],
            "payment_total_uzs": payment_total_uzs,
            "location": str(body.get("location") or body.get("destination") or "").strip()[:240],
            "cargo": str(body.get("cargo") or body.get("cargo_description") or "").strip()[:500],
            "additional_info": str(body.get("additional_info") or body.get("service_note") or "").strip()[:2000],
            "documents": normalized_documents,
        }
        now = _now()
        for _ in range(5):
            document_no = f"BXT-{datetime.now(timezone.utc).year}-{secrets.token_hex(4).upper()}"
            public_token = secrets.token_urlsafe(24)
            try:
                if self.pool:
                    async with self.pool.acquire() as db:
                        row = await db.fetchrow(
                            """INSERT INTO inspector_documents
                               (document_no,public_token,inspector_name,driver_name,vehicle_plate,post_code,post_name,crossing_at,payload)
                               VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9::jsonb) RETURNING *""",
                            document_no, public_token, inspector_name, driver_name, vehicle_plate,
                            post_code, post_name, crossing_at, _json(payload),
                        )
                    return _inspector_record(row, include_token=True)
                async with aiosqlite.connect(self.sqlite_path) as db:
                    db.row_factory = aiosqlite.Row
                    cursor = await db.execute(
                        """INSERT INTO inspector_documents
                           (document_no,public_token,inspector_name,driver_name,vehicle_plate,post_code,post_name,crossing_at,payload,created_at,updated_at)
                           VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                        (document_no, public_token, inspector_name, driver_name, vehicle_plate,
                         post_code, post_name, crossing_at, _json(payload), now, now),
                    )
                    await db.commit()
                    row = await (await db.execute(
                        "SELECT * FROM inspector_documents WHERE id=?", (cursor.lastrowid,)
                    )).fetchone()
                return _inspector_record(row, include_token=True)
            except Exception as exc:
                if "unique" not in str(exc).lower() and "duplicate" not in str(exc).lower():
                    raise
        raise RuntimeError("Hujjat uchun yagona raqam yaratib bo'lmadi.")

    async def get_inspector_document(self, public_token: str, *, include_token: bool = False) -> dict[str, Any] | None:
        token = str(public_token or "").strip()
        if not 20 <= len(token) <= 80:
            return None
        if self.pool:
            async with self.pool.acquire() as db:
                row = await db.fetchrow(
                    "SELECT * FROM inspector_documents WHERE public_token=$1", token
                )
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                db.row_factory = aiosqlite.Row
                row = await (await db.execute(
                    "SELECT * FROM inspector_documents WHERE public_token=?", (token,)
                )).fetchone()
        return _inspector_record(row, include_token=include_token) if row else None

    async def list_inspector_documents(self, limit: int = 100) -> list[dict[str, Any]]:
        limit = max(1, min(200, int(limit)))
        if self.pool:
            async with self.pool.acquire() as db:
                rows = await db.fetch(
                    "SELECT * FROM inspector_documents ORDER BY id DESC LIMIT $1", limit
                )
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                db.row_factory = aiosqlite.Row
                rows = await (await db.execute(
                    "SELECT * FROM inspector_documents ORDER BY id DESC LIMIT ?", (limit,)
                )).fetchall()
        return [_inspector_record(row, include_token=True) for row in rows]

    async def set_inspector_document_status(self, public_token: str, status: str) -> None:
        if status not in {"active", "revoked"}:
            raise ValueError("Hujjat holati noto'g'ri.")
        if self.pool:
            async with self.pool.acquire() as db:
                result = await db.execute(
                    "UPDATE inspector_documents SET status=$1,updated_at=NOW() WHERE public_token=$2",
                    status, public_token,
                )
                if result.endswith(" 0"):
                    raise ValueError("Hujjat topilmadi.")
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                cursor = await db.execute(
                    "UPDATE inspector_documents SET status=?,updated_at=? WHERE public_token=?",
                    (status, _now(), public_token),
                )
                await db.commit()
                if cursor.rowcount == 0:
                    raise ValueError("Hujjat topilmadi.")

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
