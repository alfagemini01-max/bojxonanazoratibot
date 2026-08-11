from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


def _json_value(value: Any) -> Any:
    if isinstance(value, str):
        return json.loads(value)
    return value


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


class RuleVersionStore:
    def __init__(self, database_url: str, data_dir: Path) -> None:
        self.database_url = database_url
        self.local_dir = data_dir / "rule_versions"
        self.pool = None
        self.permission_path: Path | None = None
        self.fees_path: Path | None = None
        self._active_cache: dict[str, Any] | None = None

    async def initialize(self, permission_path: Path, fees_path: Path) -> None:
        self.permission_path = permission_path
        self.fees_path = fees_path
        if self.database_url:
            import asyncpg

            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=0,
                max_size=1,
                command_timeout=20,
                max_inactive_connection_lifetime=180,
            )
            async with self.pool.acquire() as connection:
                await connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS rule_versions (
                        id BIGSERIAL PRIMARY KEY,
                        version_no BIGINT UNIQUE NOT NULL,
                        status TEXT NOT NULL,
                        source TEXT NOT NULL,
                        created_by TEXT NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        permission_data JSONB NOT NULL,
                        fees_data JSONB NOT NULL,
                        summary JSONB NOT NULL DEFAULT '{}'::jsonb
                    );
                    CREATE INDEX IF NOT EXISTS rule_versions_status_idx
                        ON rule_versions(status, version_no DESC);
                    CREATE TABLE IF NOT EXISTS admin_audit_log (
                        id BIGSERIAL PRIMARY KEY,
                        action TEXT NOT NULL,
                        actor TEXT NOT NULL,
                        details JSONB NOT NULL DEFAULT '{}'::jsonb,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    );
                    CREATE INDEX IF NOT EXISTS admin_audit_created_idx
                        ON admin_audit_log(created_at DESC);
                    """
                )
            await self._ensure_initial_version()
            await self.sync_active()
            return

        self.local_dir.mkdir(parents=True, exist_ok=True)
        active_path = self.local_dir / "active.json"
        if not active_path.exists():
            await self.publish(
                json.loads(permission_path.read_text(encoding="utf-8")),
                json.loads(fees_path.read_text(encoding="utf-8")),
                actor="system",
                source="initial",
                summary={"initial": True},
            )
        await self.sync_active()

    async def close(self) -> None:
        if self.pool is not None:
            await self.pool.close()
        self.pool = None

    async def _ensure_initial_version(self) -> None:
        async with self.pool.acquire() as connection:
            exists = await connection.fetchval("SELECT EXISTS(SELECT 1 FROM rule_versions)")
            if exists:
                return
            permission = json.loads(self.permission_path.read_text(encoding="utf-8"))
            fees = json.loads(self.fees_path.read_text(encoding="utf-8"))
            await connection.execute(
                """
                INSERT INTO rule_versions
                    (version_no, status, source, created_by, permission_data, fees_data, summary)
                VALUES (1, 'active', 'initial', 'system', $1::jsonb, $2::jsonb, $3::jsonb)
                """,
                json.dumps(permission, ensure_ascii=False),
                json.dumps(fees, ensure_ascii=False),
                json.dumps({"initial": True}),
            )

    async def sync_active(self) -> dict[str, Any] | None:
        snapshot = await self.get_active()
        if not snapshot or not self.permission_path or not self.fees_path:
            return snapshot
        _write_json(self.permission_path, snapshot["permission"])
        _write_json(self.fees_path, snapshot["fees"])
        return snapshot

    async def get_active(self) -> dict[str, Any] | None:
        if self._active_cache is not None:
            return self._active_cache
        if self.pool is not None:
            async with self.pool.acquire() as connection:
                row = await connection.fetchrow(
                    """
                    SELECT version_no, source, created_by, created_at, permission_data, fees_data, summary
                    FROM rule_versions WHERE status = 'active'
                    ORDER BY version_no DESC LIMIT 1
                    """
                )
            if not row:
                return None
            self._active_cache = {
                "version_no": row["version_no"],
                "source": row["source"],
                "created_by": row["created_by"],
                "created_at": row["created_at"].isoformat(),
                "permission": _json_value(row["permission_data"]),
                "fees": _json_value(row["fees_data"]),
                "summary": _json_value(row["summary"]),
            }
            return self._active_cache
        active_path = self.local_dir / "active.json"
        self._active_cache = json.loads(active_path.read_text(encoding="utf-8")) if active_path.exists() else None
        return self._active_cache

    async def publish(
        self,
        permission: dict[str, Any],
        fees: dict[str, Any],
        actor: str,
        source: str,
        summary: dict[str, Any],
    ) -> dict[str, Any]:
        if self.pool is not None:
            async with self.pool.acquire() as connection:
                async with connection.transaction():
                    version_no = int(await connection.fetchval("SELECT COALESCE(MAX(version_no), 0) + 1 FROM rule_versions"))
                    await connection.execute("UPDATE rule_versions SET status = 'archived' WHERE status = 'active'")
                    await connection.execute(
                        """
                        INSERT INTO rule_versions
                            (version_no, status, source, created_by, permission_data, fees_data, summary)
                        VALUES ($1, 'active', $2, $3, $4::jsonb, $5::jsonb, $6::jsonb)
                        """,
                        version_no,
                        source,
                        actor,
                        json.dumps(permission, ensure_ascii=False),
                        json.dumps(fees, ensure_ascii=False),
                        json.dumps(summary, ensure_ascii=False),
                    )
                    await connection.execute(
                        "INSERT INTO admin_audit_log(action, actor, details) VALUES('publish', $1, $2::jsonb)",
                        actor,
                        json.dumps({"version_no": version_no, "source": source}, ensure_ascii=False),
                    )
            self._active_cache = None
            snapshot = await self.get_active()
        else:
            versions = await self.list_versions(limit=10_000)
            version_no = max((int(item["version_no"]) for item in versions), default=0) + 1
            snapshot = {
                "version_no": version_no,
                "source": source,
                "created_by": actor,
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "permission": permission,
                "fees": fees,
                "summary": summary,
            }
            _write_json(self.local_dir / f"version_{version_no:06d}.json", snapshot)
            _write_json(self.local_dir / "active.json", snapshot)
            self._active_cache = snapshot
            await self.audit("publish", actor, {"version_no": version_no, "source": source})
        if self.permission_path and self.fees_path:
            _write_json(self.permission_path, permission)
            _write_json(self.fees_path, fees)
        return snapshot

    async def list_versions(self, limit: int = 30) -> list[dict[str, Any]]:
        limit = max(1, min(100, int(limit)))
        if self.pool is not None:
            async with self.pool.acquire() as connection:
                rows = await connection.fetch(
                    """
                    SELECT version_no, status, source, created_by, created_at, summary
                    FROM rule_versions ORDER BY version_no DESC LIMIT $1
                    """,
                    limit,
                )
            return [
                {
                    "version_no": row["version_no"],
                    "status": row["status"],
                    "source": row["source"],
                    "created_by": row["created_by"],
                    "created_at": row["created_at"].isoformat(),
                    "summary": _json_value(row["summary"]),
                }
                for row in rows
            ]
        files = sorted(self.local_dir.glob("version_*.json"), reverse=True)[:limit]
        active = await self.get_active()
        active_no = int(active.get("version_no", 0)) if active else 0
        result = []
        for path in files:
            item = json.loads(path.read_text(encoding="utf-8"))
            result.append({
                "version_no": item["version_no"],
                "status": "active" if int(item["version_no"]) == active_no else "archived",
                "source": item.get("source", ""),
                "created_by": item.get("created_by", ""),
                "created_at": item.get("created_at", ""),
                "summary": item.get("summary", {}),
            })
        return result

    async def rollback(self, version_no: int, actor: str) -> dict[str, Any]:
        if self.pool is not None:
            async with self.pool.acquire() as connection:
                row = await connection.fetchrow(
                    "SELECT permission_data, fees_data FROM rule_versions WHERE version_no = $1",
                    int(version_no),
                )
            if not row:
                raise ValueError("Tanlangan qoida versiyasi topilmadi.")
            permission = _json_value(row["permission_data"])
            fees = _json_value(row["fees_data"])
        else:
            path = self.local_dir / f"version_{int(version_no):06d}.json"
            if not path.exists():
                raise ValueError("Tanlangan qoida versiyasi topilmadi.")
            item = json.loads(path.read_text(encoding="utf-8"))
            permission, fees = item["permission"], item["fees"]
        return await self.publish(
            permission,
            fees,
            actor=actor,
            source=f"rollback:{version_no}",
            summary={"rollback_from": int(version_no)},
        )

    async def audit(self, action: str, actor: str, details: dict[str, Any]) -> None:
        if self.pool is not None:
            async with self.pool.acquire() as connection:
                await connection.execute(
                    "INSERT INTO admin_audit_log(action, actor, details) VALUES($1, $2, $3::jsonb)",
                    action,
                    actor,
                    json.dumps(details, ensure_ascii=False),
                )
            return
        self.local_dir.mkdir(parents=True, exist_ok=True)
        audit_path = self.local_dir / "audit.jsonl"
        record = {
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "action": action,
            "actor": actor,
            "details": details,
        }
        with audit_path.open("a", encoding="utf-8") as output:
            output.write(json.dumps(record, ensure_ascii=False) + "\n")

    async def list_audit(self, limit: int = 50) -> list[dict[str, Any]]:
        limit = max(1, min(200, int(limit)))
        if self.pool is not None:
            async with self.pool.acquire() as connection:
                rows = await connection.fetch(
                    "SELECT action, actor, details, created_at FROM admin_audit_log ORDER BY id DESC LIMIT $1",
                    limit,
                )
            return [
                {
                    "action": row["action"],
                    "actor": row["actor"],
                    "details": _json_value(row["details"]),
                    "created_at": row["created_at"].isoformat(),
                }
                for row in rows
            ]
        path = self.local_dir / "audit.jsonl"
        if not path.exists():
            return []
        lines = path.read_text(encoding="utf-8").splitlines()
        return [json.loads(line) for line in reversed(lines[-limit:])]
