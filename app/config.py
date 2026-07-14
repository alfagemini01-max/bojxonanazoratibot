from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    bot_token: str
    bot_mode: str
    webhook_url: str
    webhook_path: str
    web_host: str
    web_port: int
    data_source: str
    database_path: Path
    terms_pdf_path: Path
    sql_connection_string: str
    sql_query_path: Path
    timezone: str = "Asia/Tashkent"


def get_settings() -> Settings:
    return Settings(
        bot_token=os.getenv("BOT_TOKEN", "").strip(),
        bot_mode=os.getenv("BOT_MODE", "polling").strip().lower(),
        webhook_url=os.getenv("WEBHOOK_URL", "").strip(),
        webhook_path=os.getenv("WEBHOOK_PATH", "/webhook").strip(),
        web_host=os.getenv("WEB_SERVER_HOST", "0.0.0.0").strip(),
        web_port=int(os.getenv("PORT", "8080")),
        data_source=os.getenv("DATA_SOURCE", "demo").strip().lower(),
        database_path=BASE_DIR / os.getenv("DATABASE_PATH", "data/bot_data.sqlite3"),
        terms_pdf_path=BASE_DIR / os.getenv("TERMS_PDF_PATH", "assets/foydalanish_shartlari.pdf"),
        sql_connection_string=os.getenv("SQL_CONNECTION_STRING", "").strip(),
        sql_query_path=BASE_DIR / os.getenv(
            "SQL_QUERY_PATH",
            "sql/vehicle_check.sql",
        ),
        timezone=os.getenv("TZ", "Asia/Tashkent").strip(),
    )
