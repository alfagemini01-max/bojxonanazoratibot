from __future__ import annotations

import json
import math
from pathlib import Path
from time import monotonic
from typing import Any


class OversizeInputError(ValueError):
    pass


def _number(value: object, name: str, minimum: float, maximum: float) -> float:
    try:
        result = float(str(value).strip().replace(" ", "").replace(",", "."))
    except (TypeError, ValueError) as exc:
        raise OversizeInputError(f"{name}: raqamli qiymat kiriting.") from exc
    if not math.isfinite(result) or not minimum <= result <= maximum:
        raise OversizeInputError(f"{name}: {minimum:g}–{maximum:g} oralig'ida bo'lishi kerak.")
    return result


def _rate(rows: list[dict[str, Any]], value: float, limit_key: str) -> float:
    for row in rows:
        limit = row.get(limit_key)
        if limit is None or value <= float(limit) + 1e-9:
            return float(row["rate"])
    raise RuntimeError("Stavka jadvali to'liq emas.")


class OversizeCalculator:
    def __init__(self, rules_path: Path, bhm_value: int, usd_rate: float) -> None:
        self.rules_path = rules_path
        self.bhm_value = int(bhm_value)
        self.usd_rate = float(usd_rate)
        self._mtime_ns = 0
        self._last_check = 0.0
        self.data: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        stat = self.rules_path.stat()
        self.data = json.loads(self.rules_path.read_text(encoding="utf-8"))
        self._mtime_ns = stat.st_mtime_ns
        self.bhm_value = int(self.data.get("bhm_value") or self.bhm_value)

    def reload_if_changed(self) -> None:
        now = monotonic()
        if now - self._last_check < 1:
            return
        self._last_check = now
        try:
            if self.rules_path.stat().st_mtime_ns != self._mtime_ns:
                self._load()
        except OSError:
            return

    def limits(self, body: dict[str, Any]) -> dict[str, float]:
        configuration = str(body.get("configuration") or "combination")
        if configuration not in {"single", "one_trailer", "multi_trailer"}:
            raise OversizeInputError("Transport tarkibi noto'g'ri tanlangan.")
        axle_count = int(_number(body.get("axle_count"), "O'qlar soni", 2, 20))
        mass_group = "single" if configuration == "single" else "combination"
        mass_table = self.data["limits"]["gross_mass_t"][mass_group]
        mass_key = str(axle_count if axle_count < 6 else 6)
        if mass_key not in mass_table:
            raise OversizeInputError("Tanlangan transport tarkibi va o'qlar soni uchun me'yor mavjud emas.")
        body_type = str(body.get("body_type") or "standard")
        if body_type not in {"standard", "isothermal"}:
            raise OversizeInputError("Kuzov turi noto'g'ri tanlangan.")
        return {
            "gross_mass_t": float(mass_table[mass_key]),
            "axle_t": float(self.data["limits"]["axle_t"]),
            "length_m": float(self.data["limits"]["length_m"][configuration]),
            "width_m": float(self.data["limits"]["width_m"][body_type]),
            "height_m": float(self.data["limits"]["height_m"]),
        }

    def calculate(self, body: dict[str, Any]) -> dict[str, Any]:
        self.reload_if_changed()
        carrier = str(body.get("carrier") or "local")
        if carrier not in {"local", "foreign"}:
            raise OversizeInputError("Tashuvchi turi noto'g'ri tanlangan.")
        distance = _number(body.get("distance_km"), "Masofa", 0.1, 10_000)
        gross_mass = _number(body.get("gross_mass_t"), "Umumiy haqiqiy massa", 0.1, 500)
        length = _number(body.get("length_m"), "Uzunlik", 0.1, 100)
        width = _number(body.get("width_m"), "Kenglik", 0.1, 20)
        height = _number(body.get("height_m"), "Balandlik", 0.1, 20)
        limits = self.limits(body)
        axle_count = int(_number(body.get("axle_count"), "O'qlar soni", 2, 20))
        raw_axles = body.get("axles")
        if not isinstance(raw_axles, list) or len(raw_axles) != axle_count:
            raise OversizeInputError("Har bir o'q uchun tarozida o'lchangan haqiqiy yuklamani kiriting.")

        axles: list[dict[str, float]] = []
        allowed = limits["axle_t"]
        for index, row in enumerate(raw_axles, 1):
            if not isinstance(row, dict):
                raise OversizeInputError(f"{index}-o'q ma'lumoti noto'g'ri.")
            actual = _number(row.get("actual_t"), f"{index}-o'q haqiqiy yuklamasi", 0.01, 50)
            ratio = actual / allowed
            axles.append({"index": index, "actual_t": actual, "allowed_t": allowed, "ratio": ratio})

        axle_total = sum(row["actual_t"] for row in axles)
        tolerance = float(self.data.get("input_consistency_percent", 5)) / 100
        if abs(axle_total - gross_mass) > max(0.1, gross_mass * tolerance):
            raise OversizeInputError(
                f"O'qlar yuklamasi jami ({axle_total:g} t) umumiy massadan ({gross_mass:g} t) "
                f"{tolerance * 100:g}% dan ko'p farq qilmoqda. Ma'lumotlarni tekshiring."
            )

        mass_excess = max(0.0, gross_mass - limits["gross_mass_t"])
        dimension_excess = {
            "length_m": max(0.0, length - limits["length_m"]),
            "width_m": max(0.0, width - limits["width_m"]),
            "height_m": max(0.0, height - limits["height_m"]),
        }
        overloaded = [row for row in axles if row["ratio"] > 1.0 + 1e-9]
        special_permit = mass_excess > 0 or bool(overloaded) or any(dimension_excess.values())
        components: list[dict[str, Any]] = []

        def add(key: str, amount: float, currency: str, formula: str, basis: str) -> None:
            components.append({
                "key": key,
                "amount": round(amount, 2),
                "currency": currency,
                "amount_uzs": round(amount if currency == "UZS" else amount * self.usd_rate),
                "formula": formula,
                "basis": basis,
            })

        if special_permit:
            review_fee = self.data.get("application_review_fee", {})
            add(
                "application_review",
                float(review_fee.get("amount_uzs", 0)),
                "UZS",
                "Yig'im undirilmaydi",
                str(review_fee.get("basis") or "VMQ-86, 25-ilova, 6-band"),
            )

        if special_permit and carrier == "local":
            rules = self.data["local"]
            permit_percent = float(rules["permit"]["up_to_100_km_bhm_percent"])
            permit_percent += max(0.0, distance - 100) * float(rules["permit"]["additional_km_bhm_percent"])
            add("permit", self.bhm_value * permit_percent / 100, "UZS", f"BHM × {permit_percent:g}%", "VMQ-86, 25-ilova, 7-band")
            if mass_excess > 0:
                rate = _rate(rules["gross_mass_bhm_percent_per_km"], mass_excess, "max_excess_t")
                add("gross_mass", distance * self.bhm_value * rate / 100, "UZS", f"{distance:g} km × BHM × {rate:g}%", "VMQ-86, 25-ilova, 7-band")
            for axle in overloaded:
                rate = _rate(rules["axle_bhm_percent_per_axle_km"], axle["ratio"], "max_ratio")
                add("axle", distance * self.bhm_value * rate / 100, "UZS", f"{axle['index']}-o'q: {distance:g} km × BHM × {rate:g}%", "VMQ-86, 25-ilova, 7-band")
            if any(dimension_excess.values()):
                rate = float(rules["dimension_bhm_percent_per_km"])
                add("dimension", distance * self.bhm_value * rate / 100, "UZS", f"{distance:g} km × BHM × {rate:g}%", "VMQ-86, 25-ilova, 7-band")
        elif special_permit:
            rules = self.data["foreign"]
            permit = float(rules["permit"]["up_to_100_km_usd"])
            permit += max(0.0, distance - 100) * float(rules["permit"]["additional_km_usd"])
            add("permit", permit, "USD", f"25 USD + {max(0.0, distance - 100):g} km × 0.11 USD", "VMQ-710, 15-band (VMQ-86 25-ilova 7-bandiga kiritilgan stavka)")
            if mass_excess > 0:
                rate = _rate(rules["gross_mass_usd_per_km"], mass_excess, "max_excess_t")
                add("gross_mass", distance * rate, "USD", f"{distance:g} km × {rate:g} USD", "VMQ-710, 15-band (VMQ-86 25-ilova 7-bandiga kiritilgan stavka)")
            for axle in overloaded:
                rate = _rate(rules["axle_usd_per_axle_km"], axle["ratio"], "max_ratio")
                add("axle", distance * rate, "USD", f"{axle['index']}-o'q: {distance:g} km × {rate:g} USD", "VMQ-710, 15-band (VMQ-86 25-ilova 7-bandiga kiritilgan stavka)")
            if any(dimension_excess.values()):
                rate = float(rules["dimension_usd_per_km"])
                add("dimension", distance * rate, "USD", f"{distance:g} km × {rate:g} USD", "VMQ-710, 15-band (VMQ-86 25-ilova 7-bandiga kiritilgan stavka)")

        inspection = self.data["special_inspection"]
        inspection_conditions = inspection.get("automatic_conditions", {})
        inspection_required = bool(body.get("special_inspection")) or (
            gross_mass > float(inspection_conditions.get("gross_mass_over_t", 70))
            or length > float(inspection_conditions.get("length_over_m", 24))
            or width > float(inspection_conditions.get("width_over_m", 3.5))
            or height > float(inspection_conditions.get("height_over_m", 4.5))
            or any(
                axle["actual_t"] > float(inspection_conditions.get("single_axle_over_t", 13))
                for axle in axles
            )
        )
        if special_permit and inspection_required:
            rate = float(
                inspection["under_100_t_bhm_percent_per_km"]
                if gross_mass < 100
                else inspection["from_100_t_bhm_percent_per_km"]
            )
            add(
                "special_inspection",
                distance * self.bhm_value * rate / 100,
                "UZS",
                f"{distance:g} km × BHM × {rate:g}%",
                str(inspection["basis"]),
            )

        coordination: list[str] = []
        if height > 4.5:
            coordination.append("electric_network")
        if bool(body.get("railway_crossing")) and (
            width > 5 or height > 4.5 or length > limits["length_m"] or gross_mass > 52
        ):
            coordination.append("railway")
        if special_permit:
            coordination.append("road_authority")
            coordination.append("traffic_safety")
        if width > 3.5 or length > 24 or mass_excess > 0 or bool(overloaded):
            coordination.append("escort_vehicle")
        if width > 4 or length > 30:
            coordination.append("traffic_police_escort")
        if gross_mass > 52 or width > 5 or height > 4.35:
            coordination.append("engineering_review")

        unauthorized = bool(body.get("unauthorized_movement"))
        damage = None
        if unauthorized and special_permit:
            damage_rate = next(
                float(row["bhm_per_km"])
                for row in self.data["unauthorized_damage"]
                if row["max_total_mass_t"] is None or gross_mass <= float(row["max_total_mass_t"])
            )
            damage = {
                "amount_uzs": round(distance * self.bhm_value * damage_rate),
                "formula": f"{distance:g} km × {damage_rate:g} BHM",
                "basis": "VMQ-710, 2-ilova 9-band",
            }

        return {
            "ok": True,
            "version": self.data["version"],
            "special_permit_required": special_permit,
            "carrier": carrier,
            "distance_km": round(distance, 2),
            "actual": {"gross_mass_t": gross_mass, "length_m": length, "width_m": width, "height_m": height},
            "limits": limits,
            "excess": {"gross_mass_t": round(mass_excess, 3), **{key: round(value, 3) for key, value in dimension_excess.items()}},
            "axles": [{**row, "ratio": round(row["ratio"], 4), "overloaded": row in overloaded} for row in axles],
            "components": components,
            "totals": {
                "uzs": round(sum(row["amount_uzs"] for row in components)),
                "usd": round(sum(row["amount"] for row in components if row["currency"] == "USD"), 2),
                "bhm": self.bhm_value,
                "usd_rate": self.usd_rate,
            },
            "coordination": list(dict.fromkeys(coordination)),
            "special_inspection_required": special_permit and inspection_required,
            "unauthorized_damage": damage,
            "sources": self.data["sources"],
            "application_review_fee": self.data.get("application_review_fee", {"amount_uzs": 0}),
            "measurement_tolerance": self.data.get("measurement_tolerance", {}),
            "advisory": True,
        }
