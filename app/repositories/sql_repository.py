from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from .base import VehicleRecord


DEFAULT_SQL_QUERY = """
/*
  Ushbu so'rov bitta transport raqami bo'yicha botga kerakli maydonlarni qaytarishi kerak.
  pyodbc orqali bitta parametr uzatiladi: ? = normalizatsiya qilingan davlat raqami.

  Qaytadigan ustunlar:
    plate, origin, vehicle_type, status, conclusion,
    doc_type, doc_number, doc_from_post, doc_start_date, doc_to_post,
    doc_deadline, doc_state, doc_level,
    debt_level, debt_text,
    fine_level, fine_text, fine_count, fine_amount, fine_decisions,
    ban_level, ban_text,
    cargo_control_missing_warning, system_error

  Bir nechta nazorat hujjati bo'lsa, har bir hujjat alohida qatorda qaytishi mumkin.
*/
SELECT
    ? AS plate,
    'Noma''lum' AS origin,
    'Noma''lum' AS vehicle_type,
    'neutral' AS status,
    'SQL so''rovi moslashtirilmagan. So''rov faylini real bazaga moslang.' AS conclusion,
    NULL AS doc_type,
    NULL AS doc_number,
    NULL AS doc_from_post,
    NULL AS doc_start_date,
    NULL AS doc_to_post,
    NULL AS doc_deadline,
    NULL AS doc_state,
    NULL AS doc_level,
    'neutral' AS debt_level,
    'tekshirilmadi' AS debt_text,
    'neutral' AS fine_level,
    'tekshirilmadi' AS fine_text,
    NULL AS fine_count,
    NULL AS fine_amount,
    NULL AS fine_decisions,
    'neutral' AS ban_level,
    'tekshirilmadi' AS ban_text,
    0 AS cargo_control_missing_warning,
    0 AS system_error
"""


class SqlServerVehicleRepository:
    def __init__(self, connection_string: str, query_path: Path | None = None) -> None:
        if not connection_string:
            raise ValueError("SQL_CONNECTION_STRING bo'sh. .env fayliga SQL Server ulanish satrini yozing.")
        self.connection_string = connection_string
        self.query = self._load_query(query_path)

    def _load_query(self, query_path: Path | None) -> str:
        if query_path and query_path.exists():
            return query_path.read_text(encoding="utf-8")
        return DEFAULT_SQL_QUERY

    async def find_by_plate(self, plate: str) -> VehicleRecord | None:
        rows = await asyncio.to_thread(self._fetch_rows, plate)
        if not rows:
            return None
        return self._map_rows(rows)

    def _fetch_rows(self, plate: str) -> list[dict[str, Any]]:
        try:
            import pyodbc
        except ImportError as exc:
            raise RuntimeError(
                "SQL Server rejimi uchun pyodbc kerak. requirements-sql.txt orqali o'rnating."
            ) from exc

        with pyodbc.connect(self.connection_string, timeout=15) as connection:
            cursor = connection.cursor()
            cursor.execute(self.query, plate)
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def _map_rows(self, rows: list[dict[str, Any]]) -> VehicleRecord:
        first = rows[0]
        docs: list[dict[str, Any]] = []

        for row in rows:
            if not row.get("doc_type"):
                continue
            docs.append(
                {
                    "type": row.get("doc_type"),
                    "number": row.get("doc_number"),
                    "from_post": row.get("doc_from_post"),
                    "start_date": row.get("doc_start_date"),
                    "to_post": row.get("doc_to_post"),
                    "deadline": row.get("doc_deadline"),
                    "state": row.get("doc_state"),
                    "level": row.get("doc_level") or "ok",
                }
            )

        return {
            "plate": first.get("plate"),
            "origin": first.get("origin") or "Noma'lum",
            "vehicle_type": first.get("vehicle_type") or "Noma'lum",
            "status": first.get("status") or "neutral",
            "conclusion": first.get("conclusion") or "Ma'lumot tekshirildi.",
            "docs": docs,
            "debt": {"level": first.get("debt_level") or "ok", "text": first.get("debt_text") or "yo'q"},
            "fine": {
                "level": first.get("fine_level") or "ok",
                "text": first.get("fine_text") or "yo'q",
                "count": first.get("fine_count"),
                "amount": first.get("fine_amount") or first.get("fine_amount_text"),
                "decisions": self._split_decisions(
                    first.get("fine_decisions")
                    or first.get("fine_decision_numbers")
                    or first.get("fine_decision_no")
                ),
            },
            "ban": {"level": first.get("ban_level") or "ok", "text": first.get("ban_text") or "yo'q"},
            "cargo_control_missing_warning": self._as_bool(first.get("cargo_control_missing_warning")),
            "system_error": self._as_bool(first.get("system_error")),
        }

    @staticmethod
    def _as_bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        return str(value).strip().lower() in {"1", "true", "yes", "ha"}

    @staticmethod
    def _split_decisions(value: Any) -> list[str]:
        if not value:
            return []
        if isinstance(value, (list, tuple, set)):
            return [str(item).strip() for item in value if str(item).strip()]
        text = str(value).replace(";", ",").replace("\n", ",")
        return [item.strip() for item in text.split(",") if item.strip()]
