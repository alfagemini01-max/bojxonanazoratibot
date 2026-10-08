from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)
CBU_RATES_URL = "https://cbu.uz/uz/arkhiv-kursov-valyut/json/"
IMPORTANT_CURRENCIES = ("USD", "EUR", "RUB", "CNY", "KZT")
REFRESH_INTERVAL = timedelta(hours=6)
FAILURE_RETRY_INTERVAL = timedelta(minutes=5)


class CurrencyRateService:
    def __init__(self, cache_path: Path, usd_fallback_rate: float) -> None:
        self.cache_path = cache_path
        self.usd_fallback_rate = float(usd_fallback_rate)
        self._lock = asyncio.Lock()
        self._rates: dict[str, dict[str, Any]] = {}
        self._fetched_at: datetime | None = None
        self._last_attempt_at: datetime | None = None
        self._load_cache()

    @property
    def usd_rate(self) -> float:
        return float(self._rates.get("USD", {}).get("rate") or self.usd_fallback_rate)

    def snapshot(self) -> dict[str, Any]:
        rows = [self._rates[code] for code in IMPORTANT_CURRENCIES if code in self._rates]
        if not rows:
            rows = [{
                "code": "USD",
                "rate": self.usd_fallback_rate,
                "diff": 0,
                "date": "",
                "name_uz": "AQSH dollari (zaxira kursi)",
                "name_ru": "Доллар США (резервный курс)",
                "name_en": "US dollar (fallback rate)",
            }]
        return {
            "rates": rows,
            "fetched_at": self._fetched_at.isoformat() if self._fetched_at else None,
            "source": CBU_RATES_URL,
            "using_fallback": "USD" not in self._rates,
        }

    def _load_cache(self) -> None:
        try:
            payload = json.loads(self.cache_path.read_text(encoding="utf-8"))
            rows = payload.get("rates") or []
            self._rates = {str(row["code"]): row for row in rows if row.get("code") in IMPORTANT_CURRENCIES}
            fetched_at = payload.get("fetched_at")
            self._fetched_at = datetime.fromisoformat(fetched_at) if fetched_at else None
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
            self._rates = {}
            self._fetched_at = None

    def _fresh(self) -> bool:
        if not self._fetched_at or "USD" not in self._rates:
            return False
        fetched = self._fetched_at
        if fetched.tzinfo is None:
            fetched = fetched.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) - fetched.astimezone(timezone.utc) < REFRESH_INTERVAL

    @staticmethod
    def parse_cbu_payload(payload: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        rates: dict[str, dict[str, Any]] = {}
        for row in payload:
            code = str(row.get("Ccy") or "").upper()
            if code not in IMPORTANT_CURRENCIES:
                continue
            nominal = max(1, int(float(row.get("Nominal") or 1)))
            rate = float(str(row.get("Rate") or "0").replace(" ", "").replace(",", ".")) / nominal
            diff = float(str(row.get("Diff") or "0").replace(" ", "").replace(",", ".")) / nominal
            if rate <= 0:
                continue
            rates[code] = {
                "code": code,
                "rate": round(rate, 6),
                "diff": round(diff, 6),
                "date": str(row.get("Date") or ""),
                "name_uz": str(row.get("CcyNm_UZ") or code),
                "name_ru": str(row.get("CcyNm_RU") or code),
                "name_en": str(row.get("CcyNm_EN") or code),
            }
        return rates

    async def refresh(self, force: bool = False) -> dict[str, Any]:
        if not force and self._fresh():
            return self.snapshot()
        if (
            not force
            and self._last_attempt_at
            and datetime.now(timezone.utc) - self._last_attempt_at < FAILURE_RETRY_INTERVAL
        ):
            return self.snapshot()
        async with self._lock:
            if not force and self._fresh():
                return self.snapshot()
            self._last_attempt_at = datetime.now(timezone.utc)
            try:
                from aiohttp import ClientSession, ClientTimeout

                timeout = ClientTimeout(total=10, connect=4)
                async with ClientSession(timeout=timeout, headers={"User-Agent": "NazoratBot/1.0"}) as session:
                    async with session.get(CBU_RATES_URL) as response:
                        response.raise_for_status()
                        payload = await response.json(content_type=None)
                rates = self.parse_cbu_payload(payload)
                if "USD" not in rates:
                    raise ValueError("CBU response does not contain USD")
                self._rates = rates
                self._fetched_at = datetime.now(timezone.utc)
                self._save_cache()
            except Exception as exc:
                logger.warning("CBU currency rates could not be refreshed: %s", exc)
            return self.snapshot()

    def _save_cache(self) -> None:
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.cache_path.with_suffix(self.cache_path.suffix + ".tmp")
            temporary.write_text(
                json.dumps(self.snapshot(), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            temporary.replace(self.cache_path)
        except OSError as exc:
            logger.warning("Currency-rate cache could not be written: %s", exc)


_service: CurrencyRateService | None = None


def get_currency_rate_service(cache_path: Path, usd_fallback_rate: float) -> CurrencyRateService:
    global _service
    if _service is None:
        _service = CurrencyRateService(cache_path, usd_fallback_rate)
    return _service


def current_usd_rate(fallback_rate: float) -> float:
    return _service.usd_rate if _service is not None else float(fallback_rate)


def setup_currency_rate_lifecycle(app: Any, service: CurrencyRateService) -> None:
    async def worker() -> None:
        while True:
            await service.refresh()
            await asyncio.sleep(60 * 60)

    async def start(_: Any) -> None:
        app["currency_rate_task"] = asyncio.create_task(worker())

    async def stop(_: Any) -> None:
        task = app.get("currency_rate_task")
        if task:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)

    app.on_startup.append(start)
    app.on_cleanup.append(stop)
