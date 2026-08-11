from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone as datetime_timezone
from html import escape as html_escape
from pathlib import Path
from time import monotonic
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.services.permit import (
    IRAN_CODE,
    TURKMENISTAN_CODE,
    UZBEKISTAN_CODE,
    Country,
    PermitRuleService,
    country_label,
    is_eu_or_azerbaijan,
    permit_status_text,
    transport_type_label,
    turkmenistan_extra_fee_applies,
)


TAJIKISTAN_CODE = "762"
KAZAKHSTAN_CODE = "398"
KYRGYZSTAN_CODE = "417"
AFGHANISTAN_CODE = "004"


@dataclass(frozen=True)
class FeeItem:
    title: str
    amount_som: int
    amount_usd: float | None
    basis: str
    note: str = ""


def _html(value: object) -> str:
    return html_escape(str(value or ""), quote=False)


def _load_timezone(timezone: str):
    try:
        return ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        return datetime_timezone(timedelta(hours=5))


def _format_som(value: int) -> str:
    return f"{int(round(value)):,}".replace(",", " ") + " so'm"


def _format_usd(value: float) -> str:
    if float(value).is_integer():
        return f"{int(value)} USD"
    return f"{value:.2f} USD"


def _yes(value: object) -> bool:
    return str(value or "").lower() == "yes"


def _float_value(value: object) -> float:
    text = str(value or "").replace(" ", "").replace(",", ".")
    try:
        return max(0.0, float(text))
    except ValueError:
        return 0.0


def _int_value(value: object) -> int:
    try:
        return max(0, int(str(value or "").strip()))
    except ValueError:
        return 0


class FeeCalculator:
    def __init__(self, data_path: Path, bhm_value: int, usd_rate: float) -> None:
        self.data_path = data_path
        self._mtime_ns = 0
        self._last_reload_check = 0.0
        self._reload_check_interval = 1.0
        self.data = {}
        self.bhm_value = int(bhm_value or self.data.get("bhm", {}).get("value", 412000))
        self.usd_rate = float(usd_rate or 0) or 12600.0
        self._load_data()

    def _load_data(self) -> None:
        stat = self.data_path.stat()
        self._mtime_ns = stat.st_mtime_ns
        self.data = json.loads(self.data_path.read_text(encoding="utf-8"))
        self.bhm_value = int(self.data.get("bhm", {}).get("value") or self.bhm_value or 412000)
        self.legal_basis = self.data.get("legal_basis", {})

    def reload_if_changed(self) -> None:
        now = monotonic()
        if now - self._last_reload_check < self._reload_check_interval:
            return
        self._last_reload_check = now
        try:
            mtime_ns = self.data_path.stat().st_mtime_ns
        except OSError:
            return
        if mtime_ns != self._mtime_ns:
            self._load_data()

    def customs_clearance_amount(self, customs_value_usd: float) -> tuple[float, int]:
        self.reload_if_changed()
        for row in self.data["customs_clearance_bhm_scale"]:
            max_usd = row.get("max_usd")
            if max_usd is None or customs_value_usd <= float(max_usd):
                bhm = float(row["bhm"])
                return bhm, int(round(bhm * self.bhm_value))
        return 25.0, int(round(25 * self.bhm_value))

    def base_entry_fee_usd(self, vehicle_country_code: str, weight_category: str | None, stay_duration: str | None) -> float:
        self.reload_if_changed()
        fees = self.data["entry_fee"]
        if vehicle_country_code == IRAN_CODE:
            return float(fees["iran_usd"])
        if vehicle_country_code == AFGHANISTAN_CODE:
            return float(fees["afghanistan_usd"])
        if vehicle_country_code == KAZAKHSTAN_CODE:
            return float(fees["kazakhstan_usd"])
        if vehicle_country_code == KYRGYZSTAN_CODE:
            return float(fees["kyrgyzstan_usd"])
        if vehicle_country_code == TAJIKISTAN_CODE:
            return float(fees["tajikistan_by_weight_usd"].get(weight_category or "up_to_10", 100))
        if vehicle_country_code == TURKMENISTAN_CODE:
            return float(fees["turkmenistan_by_weight_usd"].get(weight_category or "up_to_10", 130))
        if is_eu_or_azerbaijan(vehicle_country_code):
            return float(fees["eu_azerbaijan_by_stay_usd"].get(stay_duration or "up_to_14", 80))
        return float(fees["default_foreign_usd"])

    def entry_fee_usd_for_rule(
        self,
        rule: dict[str, str],
        vehicle_country_code: str,
        weight_category: str | None,
        stay_duration: str | None,
    ) -> float:
        custom_amount = str(rule.get("dues_amount_usd") or "").strip()
        if custom_amount and custom_amount not in {"100/150/200", "130/180/250", "80/280"}:
            try:
                return float(custom_amount.replace(" ", "").replace(",", "."))
            except ValueError:
                pass
        return self.base_entry_fee_usd(vehicle_country_code, weight_category, stay_duration)

    def build_message(
        self,
        payload: dict[str, object],
        permit_service: PermitRuleService,
        timezone: str = "Asia/Tashkent",
        lang: str | None = "uz",
    ) -> str:
        self.reload_if_changed()
        code = lang if lang in {"uz", "ru", "en"} else "uz"
        now = datetime.now(_load_timezone(timezone)).strftime("%d.%m.%Y, %H:%M")

        vehicle_country = permit_service.country_by_code(str(payload.get("vehicle_country_code", "")))
        origin = permit_service.country_by_code(str(payload.get("origin_country_code", ""))) if payload.get("origin_country_code") else None
        destination = permit_service.country_by_code(str(payload.get("destination_country_code", ""))) if payload.get("destination_country_code") else None

        vehicle_type = str(payload.get("vehicle_type", "truck"))
        direction = str(payload.get("direction", "entry"))
        permit_result = None
        if origin and destination and vehicle_country:
            permit_result = permit_service.evaluate(origin, destination, vehicle_country)

        items: list[FeeItem] = []
        warnings: list[str] = []
        summaries: list[str] = []

        if str(payload.get("calculation_mode")) == "quick":
            quick_notes = {
                "uz": "⚡ Tezkor hisob: faqat asosiy majburiy to'lovlar hisoblandi. Maxsus holatlar uchun batafsil hisoblashni tanlang.",
                "ru": "⚡ Быстрый расчет: учтены только основные обязательные платежи. Для особых условий выберите подробный расчет.",
                "en": "⚡ Quick calculation: only core mandatory payments are included. Select detailed calculation for special conditions.",
            }
            warnings.append(quick_notes[code])

        foreign_vehicle = bool(vehicle_country and vehicle_country.code != UZBEKISTAN_CODE)
        cargo_vehicle = vehicle_type in {"truck", "truck_trailer"}
        entry_or_transit = direction in {"entry", "transit"}
        humanitarian_reduction_applied = False

        if foreign_vehicle and cargo_vehicle and entry_or_transit and permit_result:
            rule = permit_result.rule or {}
            dues_cd = str(rule.get("dues_cd", "0"))
            entry_fee_usd = 0.0
            if dues_cd == "1":
                entry_fee_usd = self.entry_fee_usd_for_rule(
                    rule,
                    vehicle_country.code,
                    str(payload.get("weight_category") or ""),
                    str(payload.get("stay_duration") or ""),
                )
                if _yes(payload.get("humanitarian")):
                    entry_fee_usd = entry_fee_usd * 0.5
                    humanitarian_reduction_applied = entry_fee_usd > 0
            if turkmenistan_extra_fee_applies(permit_result):
                entry_fee_usd += float(self.data["entry_fee"]["turkmenistan_extra_usd"])

            if entry_fee_usd > 0 or vehicle_country.code == IRAN_CODE:
                items.append(
                    FeeItem(
                        "Kirish/tranzit yig'imi",
                        int(round(entry_fee_usd * self.usd_rate)),
                        entry_fee_usd,
                        self.legal_basis["entry_transit_fee"],
                        "MB kursi bo'yicha so'mda undiriladi.",
                    )
                )
            else:
                summaries.append("✅ Kirish/tranzit yig'imi undirilmaydi.")

            summaries.append(permit_status_text(permit_result.rule, code))

        if _yes(payload.get("declared")):
            customs_value = _float_value(payload.get("customs_value_usd"))
            bhm, amount = self.customs_clearance_amount(customs_value)
            items.append(
                FeeItem(
                    "Bojxona rasmiylashtiruvi yig'imi",
                    amount,
                    None,
                    self.legal_basis["customs_clearance"],
                    f"Bojxona qiymati: {_format_usd(customs_value)}; stavka: {bhm:g} BHM.",
                )
            )

        transit_declaration_required = cargo_vehicle and direction in {"entry", "transit"}
        if transit_declaration_required or _yes(payload.get("transit_declaration")):
            amount = int(round(float(self.data["fixed"]["transit_declaration_bhm"]) * self.bhm_value))
            items.append(
                FeeItem(
                    "Tranzit deklaratsiyasi rasmiylashtiruvi",
                    amount,
                    None,
                    self.legal_basis["transit_declaration"],
                    "Yuk bojxona nazoratida harakatlanganda 1 ta tranzit deklaratsiyasi uchun 0,25 BHM.",
                )
            )

        if _yes(payload.get("tinted")):
            if foreign_vehicle and direction in {"entry", "transit"}:
                usd = float(self.data["fixed"]["tinted_foreign_usd"])
                items.append(
                    FeeItem(
                        "Qoraytirilgan oyna uchun yig'im",
                        int(round(usd * self.usd_rate)),
                        usd,
                        self.legal_basis["tinted_foreign"],
                        "Xorijiy avtotransport vaqtincha kirishi yoki tranziti uchun.",
                    )
                )
            else:
                warnings.append("🚘 Qoraytirilgan oyna bo'yicha ruxsatnoma toifaga qarab 5 BHM dan 50 BHM gacha rasmiylashtiriladi.")

        if foreign_vehicle and entry_or_transit and _yes(payload.get("osago_missing")):
            warnings.append("🛡️ Xorijiy avto egasining majburiy sug'urtasi OSAGO chegara postida VM 790-son qarori jadvali bo'yicha rasmiylashtiriladi.")

        if _yes(payload.get("heavy")):
            warnings.append("🚛 Og'ir vaznli yoki yirik gabaritli transport uchun qonunchilikda belgilangan alohida to'lov undirilishi mumkin.")

        if _yes(payload.get("humanitarian")) and humanitarian_reduction_applied:
            warnings.append("🆘 Gumanitar yuk deb belgilangan holatda kirish/tranzit yig'imlariga 0,5 kamaytiruvchi koeffitsiyent qo'llanishi mumkin.")

        if _yes(payload.get("animal")):
            warnings.append("🐾 Hayvon yoki hayvonot mahsuloti bo'lsa, veterinariya nazorati xizmatlari preyskurant bo'yicha rasmiylashtiriladi.")

        temp_days = _int_value(payload.get("temp_overstay_days"))
        if temp_days:
            items.append(
                FeeItem(
                    "Vaqtincha olib kirish muddatini o'tkazish",
                    temp_days * self.bhm_value,
                    None,
                    self.legal_basis["temporary_import_overstay"],
                    f"Kechikkan muddat: {temp_days} kun; har kun uchun 1 BHM.",
                )
            )

        delivery_days = _int_value(payload.get("delivery_overdue_days"))
        if delivery_days:
            items.append(
                FeeItem(
                    "Yukni muddatida yetkazmaganlik yig'imi",
                    delivery_days * self.bhm_value,
                    None,
                    self.legal_basis["overdue_delivery"],
                    f"Kechikkan muddat: {delivery_days} kun; har kun uchun 1 BHM.",
                )
            )

        warnings.append("🚫 Terminal yig'imi va \"Bojxona servis\" xizmat yig'imi talab qilinsa, ularning huquqiy asosi alohida tekshirilishi lozim.")

        total_som = sum(item.amount_som for item in items)
        total_usd = sum(item.amount_usd or 0 for item in items)

        labels = {
            "uz": {
                "title": "💰🚘 <b>Chegara to'lovlari kalkulyatori</b>",
                "vehicle": "🚘 Transport",
                "country": "🌍 Ro'yxat davlati",
                "direction": "🧭 Yo'nalish",
                "route": "📍 Tashuv yo'nalishi",
                "type": "🚛 Tashuv turi",
                "payments": "💳 Hisoblangan to'lovlar",
                "no_payment": "✅ Hozirgi javoblar bo'yicha aniq hisoblanadigan to'lov aniqlanmadi.",
                "total": "➕ Jami taxminiy summa",
                "warnings": "⚠️ Eslatmalar",
                "advisory": "ℹ️ Ma'lumotlar axborot-tavsiyaviy xususiyatga ega. Yakuniy summa chegara bojxona postida amaldagi kurs va vakolatli tizimlar bo'yicha aniqlanadi.",
                "time": "🕘 Vaqt",
            },
            "ru": {
                "title": "💰🚘 <b>Калькулятор пограничных платежей</b>",
                "vehicle": "🚘 Транспорт",
                "country": "🌍 Государство регистрации",
                "direction": "🧭 Направление",
                "route": "📍 Маршрут перевозки",
                "type": "🚛 Вид перевозки",
                "payments": "💳 Расчетные платежи",
                "no_payment": "✅ По указанным ответам платежи для точного расчета не выявлены.",
                "total": "➕ Итого ориентировочно",
                "warnings": "⚠️ Примечания",
                "advisory": "ℹ️ Информация носит информационно-рекомендательный характер. Окончательная сумма определяется на пограничном таможенном посту по действующему курсу и уполномоченным системам.",
                "time": "🕘 Время",
            },
            "en": {
                "title": "💰🚘 <b>Border Fee Calculator</b>",
                "vehicle": "🚘 Vehicle",
                "country": "🌍 Registration country",
                "direction": "🧭 Direction",
                "route": "📍 Carriage route",
                "type": "🚛 Carriage type",
                "payments": "💳 Estimated payments",
                "no_payment": "✅ No exactly calculable payment was identified from the provided answers.",
                "total": "➕ Estimated total",
                "warnings": "⚠️ Notes",
                "advisory": "ℹ️ This information is for reference and advisory purposes. The final amount is determined at the border customs post based on the current rate and authorized systems.",
                "time": "🕘 Time",
            },
        }[code]

        vehicle_type_labels = {
            "uz": {"light": "Yengil avto", "bus": "Avtobus", "truck": "Yuk avtomobili", "truck_trailer": "Yuk avto + tirkama"},
            "ru": {"light": "Легковой автомобиль", "bus": "Автобус", "truck": "Грузовой автомобиль", "truck_trailer": "Грузовой автомобиль + прицеп"},
            "en": {"light": "Passenger car", "bus": "Bus", "truck": "Truck", "truck_trailer": "Truck + trailer"},
        }[code]
        direction_labels = {
            "uz": {"entry": "O'zbekistonga kirish", "transit": "Tranzit o'tish", "exit": "O'zbekistondan chiqish"},
            "ru": {"entry": "Въезд в Узбекистан", "transit": "Транзит через Узбекистан", "exit": "Выезд из Узбекистана"},
            "en": {"entry": "Entry into Uzbekistan", "transit": "Transit through Uzbekistan", "exit": "Exit from Uzbekistan"},
        }[code]

        lines = [
            labels["title"],
            "━━━━━━━━━━━━━━━━━━━━",
            f"{labels['vehicle']}: <b>{_html(vehicle_type_labels.get(vehicle_type, vehicle_type))}</b>",
            f"{labels['country']}: <b>{_html(country_label(vehicle_country, code) if vehicle_country else '')}</b>",
            f"{labels['direction']}: <b>{_html(direction_labels.get(direction, direction))}</b>",
        ]
        if origin and destination:
            lines.append(f"{labels['route']}: <b>{_html(country_label(origin, code))} → {_html(country_label(destination, code))}</b>")
        if permit_result:
            lines.append(f"{labels['type']}: <b>{_html(transport_type_label(permit_result.vid_cd, permit_result.vid_name, code))}</b>")
        lines.append("")

        if summaries:
            lines.extend(_html(item) for item in summaries)
            lines.append("")

        lines.append(labels["payments"] + ":")
        if items:
            for index, item in enumerate(items, start=1):
                amount = _format_som(item.amount_som)
                if item.amount_usd is not None:
                    amount = f"{_format_usd(item.amount_usd)} ≈ {amount}"
                lines.append(f"{index}. <b>{_html(item.title)}</b> — <b>{_html(amount)}</b>")
                lines.append(f"   📖 {_html(item.basis)}")
                if item.note:
                    lines.append(f"   📝 {_html(item.note)}")
        else:
            lines.append(labels["no_payment"])

        lines.append("")
        lines.append(f"{labels['total']}: <b>{_html(_format_som(total_som))}</b>")
        if total_usd:
            lines.append(f"💵 USD qismi: <b>{_html(_format_usd(total_usd))}</b> | kurs: <code>{self.usd_rate:g}</code>")

        if warnings:
            lines.append("")
            lines.append(labels["warnings"] + ":")
            for index, warning in enumerate(warnings, start=1):
                lines.append(f"{index}. {_html(warning)}")

        lines.extend([
            "━━━━━━━━━━━━━━━━━━━━",
            labels["advisory"],
            f"{labels['time']}: {now}",
        ])
        return "\n".join(lines)
