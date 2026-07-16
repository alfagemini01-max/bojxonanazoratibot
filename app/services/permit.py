from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone as datetime_timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


UZBEKISTAN_CODE = "860"
DEFAULT_RULE_CODE = "000"

VID_LABELS = {
    "uz": {
        "1": "Ikki tomonlama tashuv: tashuv O'zbekistonda boshlanadi",
        "2": "Ikki tomonlama tashuv: tashuv O'zbekistonda tugaydi",
        "3": "Tranzit tashuv",
        "4": "Uchinchi davlatga tashuv",
        "5": "Uchinchi davlatdan tashuv",
        "6": "Ichki tashuv",
        "7": "Majburiyatnoma asosida yuksiz kirish",
        "8": "Majburiyatnoma asosida yuksiz tranzit",
    },
    "ru": {
        "1": "Двусторонняя перевозка: начало перевозки в Узбекистане",
        "2": "Двусторонняя перевозка: окончание перевозки в Узбекистане",
        "3": "Транзитная перевозка",
        "4": "Перевозка в третью страну",
        "5": "Перевозка из третьей страны",
        "6": "Внутренняя перевозка",
        "7": "Порожний въезд по обязательству",
        "8": "Порожний транзит по обязательству",
    },
    "en": {
        "1": "Bilateral carriage: carriage starts in Uzbekistan",
        "2": "Bilateral carriage: carriage ends in Uzbekistan",
        "3": "Transit carriage",
        "4": "Carriage to a third country",
        "5": "Carriage from a third country",
        "6": "Domestic carriage",
        "7": "Empty entry under undertaking",
        "8": "Empty transit under undertaking",
    },
}

COUNTRY_LABELS = {
    "860": {"uz": "O'zbekiston", "ru": "Узбекистан", "en": "Uzbekistan"},
    "156": {"uz": "Xitoy", "ru": "Китай", "en": "China"},
    "398": {"uz": "Qozog'iston", "ru": "Казахстан", "en": "Kazakhstan"},
    "417": {"uz": "Qirg'iziston", "ru": "Кыргызстан", "en": "Kyrgyzstan"},
    "762": {"uz": "Tojikiston", "ru": "Таджикистан", "en": "Tajikistan"},
    "795": {"uz": "Turkmaniston", "ru": "Туркменистан", "en": "Turkmenistan"},
    "004": {"uz": "Afg'oniston", "ru": "Афганистан", "en": "Afghanistan"},
    "031": {"uz": "Ozarbayjon", "ru": "Азербайджан", "en": "Azerbaijan"},
    "276": {"uz": "Germaniya", "ru": "Германия", "en": "Germany"},
    "268": {"uz": "Gruziya", "ru": "Грузия", "en": "Georgia"},
    "112": {"uz": "Belarus", "ru": "Беларусь", "en": "Belarus"},
    "792": {"uz": "Turkiya", "ru": "Турция", "en": "Turkey"},
    "643": {"uz": "Rossiya", "ru": "Россия", "en": "Russia"},
}


@dataclass(frozen=True)
class Country:
    code: str
    name: str


@dataclass(frozen=True)
class PermitResult:
    origin: Country
    destination: Country
    vehicle_country: Country
    vid_cd: str
    vid_name: str
    rule: dict[str, str] | None
    fee_text: str
    fee_note: str
    exceptions: list[dict[str, str]]


def _load_timezone(timezone: str):
    try:
        return ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        return datetime_timezone(timedelta(hours=5))


def normalize_country_text(value: str) -> str:
    text = (value or "").strip().lower()
    replacements = {
        "'": "",
        "ʻ": "",
        "‘": "",
        "’": "",
        "`": "",
        "ʼ": "",
        "-": " ",
        ".": " ",
        ",": " ",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


class PermitRuleService:
    def __init__(self, data_path: Path) -> None:
        self.data_path = data_path
        self.data = json.loads(data_path.read_text(encoding="utf-8"))
        self.countries: dict[str, str] = dict(self.data["countries"])
        self.rules: dict[str, dict[str, dict[str, str]]] = self.data["rules"]
        self.exceptions: dict[str, list[dict[str, str]]] = self.data.get("exceptions", {})
        self.vid_types: dict[str, str] = self.data["vid_types"]
        self.aliases = self._build_aliases()

    def _build_aliases(self) -> dict[str, str]:
        aliases: dict[str, str] = {}
        aliases[normalize_country_text("O'zbekiston")] = UZBEKISTAN_CODE
        aliases[normalize_country_text("Узбекистан")] = UZBEKISTAN_CODE
        aliases[normalize_country_text("Uzbekistan")] = UZBEKISTAN_CODE
        for code, name in self.countries.items():
            aliases[normalize_country_text(name)] = code
            aliases[normalize_country_text(code)] = code
        for code, values in self.data.get("manual_aliases", {}).items():
            for value in values:
                aliases[normalize_country_text(value)] = code
        return aliases

    def find_country(self, text: str) -> Country | None:
        normalized = normalize_country_text(text)
        if not normalized:
            return None
        if normalized.isdigit():
            code = normalized.zfill(3)
        else:
            code = self.aliases.get(normalized)
        if not code:
            return None
        if code == UZBEKISTAN_CODE:
            return Country(code, "O'zbekiston")
        name = self.countries.get(code)
        if not name:
            fallback_names = {
                "762": "Tojikiston",
                "795": "Turkmaniston",
                "643": "Rossiya",
                "792": "Turkiya",
            }
            name = fallback_names.get(code)
        return Country(code, name) if name else None

    def suggest_countries(self, text: str, limit: int = 6) -> list[str]:
        needle = normalize_country_text(text)
        if not needle:
            return []
        matches: list[str] = []
        seen: set[str] = set()
        all_items = [(UZBEKISTAN_CODE, "O'zbekiston"), *self.countries.items()]
        candidates: list[tuple[str, str]] = []
        for code, name in all_items:
            candidates.append((code, name))
            for label in COUNTRY_LABELS.get(code, {}).values():
                candidates.append((code, label))
        for code, values in self.data.get("manual_aliases", {}).items():
            for value in values:
                candidates.append((code, value))

        for code, candidate in candidates:
            n = normalize_country_text(candidate)
            if code in seen or not (needle in n or n in needle):
                continue
            seen.add(code)
            display_name = COUNTRY_LABELS.get(code, {}).get("uz") or self.countries.get(code, candidate).title()
            matches.append(f"{display_name} ({code})")
            if len(matches) >= limit:
                break
        return matches[:limit]

    def detect_transport_type(self, origin: Country, destination: Country, vehicle_country: Country) -> str:
        if origin.code == UZBEKISTAN_CODE and destination.code == UZBEKISTAN_CODE:
            return "6"
        if origin.code == UZBEKISTAN_CODE:
            return "1" if vehicle_country.code == destination.code else "4"
        if destination.code == UZBEKISTAN_CODE:
            return "2" if vehicle_country.code == origin.code else "5"
        return "3"

    def evaluate(self, origin: Country, destination: Country, vehicle_country: Country) -> PermitResult:
        vid_cd = self.detect_transport_type(origin, destination, vehicle_country)
        country_rules = self.rules.get(vehicle_country.code) or self.rules.get(DEFAULT_RULE_CODE, {})
        rule = country_rules.get(vid_cd)
        fee_text, fee_note = self._fee_for_rule(vehicle_country.code, rule)
        return PermitResult(
            origin=origin,
            destination=destination,
            vehicle_country=vehicle_country,
            vid_cd=vid_cd,
            vid_name=self.vid_types.get(vid_cd, "Aniqlanmagan tashuv turi"),
            rule=rule,
            fee_text=fee_text,
            fee_note=fee_note,
            exceptions=self.exceptions.get(vehicle_country.code, []),
        )

    def _fee_for_rule(self, vehicle_country_code: str, rule: dict[str, str] | None) -> tuple[str, str]:
        if not rule:
            return "⚪ Qoida topilmadi", "Spravochnikda ushbu davlat va tashuv turi bo'yicha qoida topilmadi."

        dues_cd = str(rule.get("dues_cd", "0"))
        if dues_cd == "2":
            return "✅ Yig'im undirilmaydi", "Excel spravochnikda ushbu tashuv turi bo'yicha yig'im majburiy emas deb belgilangan."
        if dues_cd == "3":
            return "⚠️ Yig'im ruxsatnoma turiga qarab aniqlanadi", "Spravochnikda yig'im ruxsatnoma turiga qarab belgilanishi ko'rsatilgan."
        if dues_cd != "1":
            return "⚪ Yig'im qo'llanmaydi", "Yig'im bo'yicha majburiy belgi yo'q."

        fee = self._fee_rate(vehicle_country_code)
        return f"💵 Yig'im undiriladi: {fee}", "Excel spravochnikda yig'im majburiy deb belgilanganligi sababli stavka qo'llanadi."

    @staticmethod
    def _fee_rate(vehicle_country_code: str, lang: str | None = "uz") -> str:
        code = _lang(lang)
        tajikistan = {"762"}
        turkmenistan = {"795"}
        afghanistan = {"004"}
        kazakhstan = {"398"}
        kyrgyzstan = {"417"}
        eu_and_azerbaijan = {
            "031", "040", "056", "100", "191", "196", "203", "208", "233", "246",
            "250", "276", "300", "348", "372", "380", "428", "440", "442", "470",
            "528", "616", "620", "642", "703", "705", "724", "752",
        }

        if vehicle_country_code in afghanistan:
            return "50 USD"
        if vehicle_country_code in kazakhstan or vehicle_country_code in kyrgyzstan:
            return "300 USD"
        if vehicle_country_code in tajikistan:
            return {
                "uz": "10 tonnagacha — 100 USD, 10-20 tonnagacha — 150 USD, 20 tonnadan yuqori — 200 USD",
                "ru": "до 10 тонн — 100 USD, от 10 до 20 тонн — 150 USD, свыше 20 тонн — 200 USD",
                "en": "up to 10 tons — 100 USD, 10 to 20 tons — 150 USD, over 20 tons — 200 USD",
            }[code]
        if vehicle_country_code in turkmenistan:
            return {
                "uz": "10 tonnagacha — 130 USD, 10-20 tonnagacha — 180 USD, 20 tonnadan yuqori — 250 USD",
                "ru": "до 10 тонн — 130 USD, от 10 до 20 тонн — 180 USD, свыше 20 тонн — 250 USD",
                "en": "up to 10 tons — 130 USD, 10 to 20 tons — 180 USD, over 20 tons — 250 USD",
            }[code]
        if vehicle_country_code in eu_and_azerbaijan:
            return {
                "uz": "14 kungacha — 80 USD, 14 kundan ortiq — 280 USD",
                "ru": "до 14 дней — 80 USD, свыше 14 дней — 280 USD",
                "en": "up to 14 days — 80 USD, over 14 days — 280 USD",
            }[code]
        return "400 USD"


def _lang(lang: str | None) -> str:
    return lang if lang in {"uz", "ru", "en"} else "uz"


def country_label(country: Country, lang: str | None = "uz") -> str:
    code = _lang(lang)
    labels = COUNTRY_LABELS.get(country.code)
    if labels:
        return labels.get(code) or labels["uz"]
    return country.name.title() if country.name.isupper() else country.name


def transport_type_label(vid_cd: str, fallback: str, lang: str | None = "uz") -> str:
    code = _lang(lang)
    return VID_LABELS.get(code, VID_LABELS["uz"]).get(vid_cd, fallback)


def permit_status_text(rule: dict[str, str] | None, lang: str | None = "uz") -> str:
    code = _lang(lang)
    if not rule:
        return {
            "uz": "⚪ Ruxsatnoma: qoida topilmadi",
            "ru": "⚪ Разрешение: правило не найдено",
            "en": "⚪ Permit: rule not found",
        }[code]
    permission_cd = str(rule.get("permission_cd", "0"))
    if permission_cd == "1":
        return {
            "uz": "📄 Ruxsatnoma: ⚠️ majburiy",
            "ru": "📄 Разрешение: ⚠️ обязательно",
            "en": "📄 Permit: ⚠️ required",
        }[code]
    if permission_cd == "2":
        return {
            "uz": "📄 Ruxsatnoma: ✅ talab etilmaydi",
            "ru": "📄 Разрешение: ✅ не требуется",
            "en": "📄 Permit: ✅ not required",
        }[code]
    if permission_cd == "3":
        return {
            "uz": "📄 Ruxsatnoma: ⛔ ushbu tashuv turi taqiqlangan",
            "ru": "📄 Разрешение: ⛔ данный вид перевозки запрещен",
            "en": "📄 Permit: ⛔ this carriage type is prohibited",
        }[code]
    return {
        "uz": "📄 Ruxsatnoma: ⚪ aniqlanmadi",
        "ru": "📄 Разрешение: ⚪ не определено",
        "en": "📄 Permit: ⚪ not determined",
    }[code]


def fee_status_lines(result: PermitResult, lang: str | None = "uz") -> tuple[str, str]:
    code = _lang(lang)
    rule = result.rule
    if not rule:
        return {
            "uz": ("💵 Yig'im: ⚪ qoida topilmadi", "Spravochnikda ushbu davlat va tashuv turi bo'yicha qoida topilmadi."),
            "ru": ("💵 Сбор: ⚪ правило не найдено", "В справочнике не найдено правило по данной стране и виду перевозки."),
            "en": ("💵 Fee: ⚪ rule not found", "No rule was found in the reference data for this country and carriage type."),
        }[code]

    dues_cd = str(rule.get("dues_cd", "0"))
    if dues_cd == "2":
        return {
            "uz": ("✅ Yig'im undirilmaydi", "Excel spravochnikda ushbu tashuv turi bo'yicha yig'im majburiy emas deb belgilangan."),
            "ru": ("✅ Сбор не взимается", "В Excel-справочнике по данному виду перевозки сбор указан как необязательный."),
            "en": ("✅ Fee is not charged", "The Excel reference data marks the fee as not mandatory for this carriage type."),
        }[code]
    if dues_cd == "3":
        return {
            "uz": ("⚠️ Yig'im ruxsatnoma turiga qarab aniqlanadi", "Spravochnikda yig'im ruxsatnoma turiga qarab belgilanishi ko'rsatilgan."),
            "ru": ("⚠️ Сбор определяется по виду разрешения", "В справочнике указано, что сбор определяется в зависимости от вида разрешения."),
            "en": ("⚠️ Fee depends on the permit type", "The reference data states that the fee is determined by the permit type."),
        }[code]
    if dues_cd != "1":
        return {
            "uz": ("⚪ Yig'im qo'llanmaydi", "Yig'im bo'yicha majburiy belgi mavjud emas."),
            "ru": ("⚪ Сбор не применяется", "Обязательная отметка по сбору отсутствует."),
            "en": ("⚪ Fee is not applied", "There is no mandatory fee mark in the reference data."),
        }[code]

    rate = PermitRuleService._fee_rate(result.vehicle_country.code, code)
    return {
        "uz": (f"💵 Yig'im undiriladi: <b>{rate}</b>", "Excel spravochnikda yig'im majburiy deb belgilanganligi sababli stavka qo'llanadi."),
        "ru": (f"💵 Сбор взимается: <b>{rate}</b>", "Так как в Excel-справочнике сбор указан как обязательный, применяется ставка сбора."),
        "en": (f"💵 Fee is charged: <b>{rate}</b>", "Because the Excel reference data marks the fee as mandatory, the fee rate is applied."),
    }[code]


def build_permit_message(result: PermitResult, timezone: str = "Asia/Tashkent", lang: str | None = "uz") -> str:
    code = _lang(lang)
    now = datetime.now(_load_timezone(timezone)).strftime("%d.%m.%Y, %H:%M")
    rule = result.rule
    fee_text, fee_note = fee_status_lines(result, code)
    labels = {
        "uz": {
            "title": "🚛 <b>Ruxsatnoma va yig'im tekshiruvi</b>",
            "origin": "📍 Tashuv boshlangan davlat",
            "destination": "🏁 Tashuv tugaydigan davlat",
            "vehicle": "🚚 Avtotransport ro'yxatdan o'tgan davlat",
            "type": "🧭 Aniqlangan tashuv turi",
            "source": "ℹ️ Spravochnik belgisi",
            "exception": "📝 Ushbu davlat bo'yicha ruxsatnoma istisnolari mavjud. Zarur bo'lsa, istisno turini alohida tekshirish kerak.",
            "unknown": "⚠️ Ushbu javob yakuniy huquqiy xulosa emas. Vakolatli tizimda qayta tekshirish talab etiladi.",
            "advisory": "⚠️ Ma'lumotlar axborot-tavsiyaviy xususiyatga ega.",
            "time": "🕘 Tekshiruv vaqti",
        },
        "ru": {
            "title": "🚛 <b>Проверка разрешения и сбора</b>",
            "origin": "📍 Государство начала перевозки",
            "destination": "🏁 Государство окончания перевозки",
            "vehicle": "🚚 Государство регистрации автотранспорта",
            "type": "🧭 Определенный вид перевозки",
            "source": "ℹ️ Отметка справочника",
            "exception": "📝 По данной стране имеются исключения по разрешениям. При необходимости вид исключения следует проверить отдельно.",
            "unknown": "⚠️ Данный ответ не является окончательным правовым заключением. Требуется повторная проверка в уполномоченной системе.",
            "advisory": "⚠️ Информация носит информационно-рекомендательный характер.",
            "time": "🕘 Время проверки",
        },
        "en": {
            "title": "🚛 <b>Permit and Fee Check</b>",
            "origin": "📍 Country where carriage starts",
            "destination": "🏁 Country where carriage ends",
            "vehicle": "🚚 Vehicle registration country",
            "type": "🧭 Detected carriage type",
            "source": "ℹ️ Reference mark",
            "exception": "📝 Permit exceptions exist for this country. If necessary, the exception type should be checked separately.",
            "unknown": "⚠️ This response is not a final legal conclusion. Re-checking in the authorized system is required.",
            "advisory": "⚠️ The information is provided for reference and advisory purposes.",
            "time": "🕘 Check time",
        },
    }[code]

    lines = [
        labels["title"],
        "━━━━━━━━━━━━━━━━━━━━",
        f"{labels['origin']}: <b>{country_label(result.origin, code)}</b>",
        f"{labels['destination']}: <b>{country_label(result.destination, code)}</b>",
        f"{labels['vehicle']}: <b>{country_label(result.vehicle_country, code)}</b>",
        "",
        f"{labels['type']}: <b>{transport_type_label(result.vid_cd, result.vid_name, code)}</b>",
        permit_status_text(rule, code),
        fee_text,
        "",
    ]
    if rule:
        lines.append(f"{labels['source']}: {rule.get('permission_name_ru')} / {rule.get('dues_name_ru')}")
    if fee_note:
        lines.append(f"📌 {fee_note}")
    if rule and str(rule.get("exception_cd")) == "2":
        lines.append(labels["exception"])
    if not rule:
        lines.append(labels["unknown"])
    lines.extend([
        "━━━━━━━━━━━━━━━━━━━━",
        labels["advisory"],
        f"{labels['time']}: {now}",
    ])
    return "\n".join(lines)
