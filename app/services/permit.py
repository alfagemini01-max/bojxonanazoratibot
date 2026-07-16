from __future__ import annotations

import json
import re
from html import escape as html_escape
from difflib import SequenceMatcher
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone as datetime_timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


UZBEKISTAN_CODE = "860"
DEFAULT_RULE_CODE = "000"
IRAN_CODE = "364"
TURKMENISTAN_CODE = "795"

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
    "000": {"uz": "Boshqa davlat / ro'yxatda yo'q", "ru": "Другое государство / нет в списке", "en": "Other country / not listed"},
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
    "364": {"uz": "Eron", "ru": "Иран", "en": "Iran"},
}


COUNTRY_LABELS.update({
    "496": {"uz": "Mongoliya", "ru": "Mongolia", "en": "Mongolia"},
    "498": {"uz": "Moldova", "ru": "Moldova", "en": "Moldova"},
    "528": {"uz": "Niderlandiya", "ru": "Netherlands", "en": "Netherlands"},
    "616": {"uz": "Polsha", "ru": "Poland", "en": "Poland"},
    "703": {"uz": "Slovakiya", "ru": "Slovakia", "en": "Slovakia"},
    "705": {"uz": "Sloveniya", "ru": "Slovenia", "en": "Slovenia"},
    "756": {"uz": "Shveytsariya", "ru": "Switzerland", "en": "Switzerland"},
    "804": {"uz": "Ukraina", "ru": "Ukraine", "en": "Ukraine"},
})


COMMON_COUNTRY_ALIASES = {
    "860": ["uzb", "uzbek", "uzbekistan", "ozb", "ozbekiston", "o'zbekiston", "uzbekiston"],
    "156": ["xit", "xito", "xitoy", "china", "chin", "kitay", "kitai"],
    "398": ["qazaq", "qazaqstan", "kazak", "kazakstan", "kazakhstan", "kazahstan", "qozogiston", "qozoqiston"],
    "417": ["qirgiz", "kirgiz", "qirgiziston", "kirgiziston", "kyrgyz", "kyrgyzstan", "kyrgizstan"],
    "762": ["tojik", "tojikiston", "tajik", "tajikistan", "tadjikistan"],
    "795": ["turkman", "turkmaniston", "turkmen", "turkmenistan", "turkmeniya"],
    "004": ["afgon", "afgoniston", "afghan", "afghanistan", "afganistan"],
    "031": ["ozar", "ozarbayjon", "azer", "azerbaijan", "azerbayjan"],
    "364": ["eron", "iran", "irn"],
    "643": ["rossiya", "russia", "rossia", "rus"],
    "792": ["turkiya", "turkey", "turkiye", "turkia"],
    "000": ["boshqa", "boshqa davlat", "nomalum", "noma'lum", "other", "not listed"],
}


COMMON_COUNTRY_ALIASES.update({
    "496": ["mongoliya", "mongolia", "mongol"],
    "498": ["moldova", "moldaviya", "moldavia"],
    "528": ["niderlandiya", "niderland", "netherlands", "holland", "gollandiya"],
    "616": ["polsha", "poland"],
    "703": ["slovakiya", "slovakia", "slovak"],
    "705": ["sloveniya", "slovenia", "sloven"],
    "756": ["shveytsariya", "shveysariya", "switzerland", "swiss"],
    "804": ["ukraina", "ukraine"],
})


@dataclass(frozen=True)
class Country:
    code: str
    name: str


@dataclass(frozen=True)
class CountryMatch:
    country: Country
    score: float


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


def transliterate_cyrillic_to_latin(value: str) -> str:
    mapping = {
        "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo",
        "ж": "j", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
        "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
        "ф": "f", "х": "x", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sh", "ъ": "",
        "ы": "i", "ь": "", "э": "e", "ю": "yu", "я": "ya",
    }
    return "".join(mapping.get(ch, ch) for ch in value.lower())


class PermitRuleService:
    def __init__(self, data_path: Path) -> None:
        self.data_path = data_path
        self.data = json.loads(data_path.read_text(encoding="utf-8"))
        self.countries: dict[str, str] = dict(self.data["countries"])
        self.rules: dict[str, dict[str, dict[str, str]]] = self.data["rules"]
        self.exceptions: dict[str, list[dict[str, str]]] = self.data.get("exceptions", {})
        self.vid_types: dict[str, str] = self.data["vid_types"]
        self.aliases = self._build_aliases()
        self.country_candidates = self._build_country_candidates()

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
        for code, values in COMMON_COUNTRY_ALIASES.items():
            for value in values:
                aliases[normalize_country_text(value)] = code
        return aliases

    def _build_country_candidates(self) -> dict[str, set[str]]:
        candidates: dict[str, set[str]] = {}
        for code, name in self.countries.items():
            candidates.setdefault(code, set()).update({name, transliterate_cyrillic_to_latin(name), code})
            for label in COUNTRY_LABELS.get(code, {}).values():
                candidates[code].add(label)
        for code, values in self.data.get("manual_aliases", {}).items():
            candidates.setdefault(code, set()).update(values)
        for code, values in COMMON_COUNTRY_ALIASES.items():
            candidates.setdefault(code, set()).update(values)
        return candidates

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

    def country_by_code(self, code: str) -> Country | None:
        return self.find_country(str(code).zfill(3))

    @staticmethod
    def _similarity(query: str, candidate: str) -> float:
        if not query or not candidate:
            return 0.0
        if query == candidate:
            return 1.0
        if len(query) >= 3 and (candidate.startswith(query) or query.startswith(candidate)):
            shorter = min(len(query), len(candidate))
            longer = max(len(query), len(candidate))
            return max(0.9, shorter / longer)
        if len(query) >= 4 and (query in candidate or candidate in query):
            shorter = min(len(query), len(candidate))
            longer = max(len(query), len(candidate))
            return max(0.76, shorter / longer)
        return SequenceMatcher(None, query, candidate).ratio()

    def search_countries(self, text: str, threshold: float = 0.75, limit: int = 8) -> list[CountryMatch]:
        needle = normalize_country_text(text)
        if not needle:
            return []

        matches: list[CountryMatch] = []
        for code, candidates in self.country_candidates.items():
            best_score = 0.0
            for candidate in candidates:
                best_score = max(best_score, self._similarity(needle, normalize_country_text(candidate)))
            if best_score < threshold:
                continue
            country = self.country_by_code(code)
            if country:
                matches.append(CountryMatch(country=country, score=best_score))

        matches.sort(key=lambda item: (-item.score, country_label(item.country, "uz")))
        return matches[:limit]

    def suggest_countries(self, text: str, limit: int = 6) -> list[str]:
        needle = normalize_country_text(text)
        if not needle:
            return []
        return [f"{country_label(match.country, 'uz')} ({match.country.code})" for match in self.search_countries(text, 0.6, limit)]

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
        country_rules = self.rules.get(vehicle_country.code, {})
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
            exceptions=self.matching_exceptions(vehicle_country.code, vid_cd),
        )

    def matching_exceptions(self, country_code: str, vid_cd: str) -> list[dict[str, str]]:
        try:
            index = int(vid_cd) - 1
        except ValueError:
            return []
        rows = []
        for row in self.exceptions.get(country_code, []):
            mask = str(row.get("exception_for", "")).zfill(8)
            if index < len(mask) and mask[index] == "1":
                rows.append(row)
        return rows

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

        if vehicle_country_code == IRAN_CODE:
            return "0 USD"
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


def _html(value: object) -> str:
    return html_escape(str(value or ""), quote=False)


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


def turkmenistan_extra_fee_applies(result: PermitResult) -> bool:
    if result.vehicle_country.code != TURKMENISTAN_CODE:
        return False
    if result.origin.code == UZBEKISTAN_CODE and result.destination.code != UZBEKISTAN_CODE:
        return True
    return (
        result.destination.code == UZBEKISTAN_CODE
        and result.origin.code not in {UZBEKISTAN_CODE, TURKMENISTAN_CODE}
    )


def turkmenistan_extra_fee_text(lang: str | None = "uz") -> str:
    code = _lang(lang)
    return {
        "uz": "Turkmaniston transporti uchun qo'shimcha yig'im — 375 USD",
        "ru": "дополнительный сбор для транспорта Туркменистана — 375 USD",
        "en": "additional fee for Turkmenistan vehicles — 375 USD",
    }[code]


def is_eu_or_azerbaijan(country_code: str) -> bool:
    return country_code in {
        "031", "040", "056", "100", "191", "196", "203", "208", "233", "246",
        "250", "276", "300", "348", "372", "380", "428", "440", "442", "470",
        "528", "616", "620", "642", "703", "705", "724", "752",
    }


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
        if turkmenistan_extra_fee_applies(result):
            return {
                "uz": (f"💵 Yig'im undiriladi: <b>{turkmenistan_extra_fee_text(code)}</b>", "Turkmaniston bo'yicha qo'shimcha yig'im qo'llanadi."),
                "ru": (f"💵 Сбор взимается: <b>{turkmenistan_extra_fee_text(code)}</b>", "Применяется дополнительный сбор по Туркменистану."),
                "en": (f"💵 Fee is charged: <b>{turkmenistan_extra_fee_text(code)}</b>", "The additional Turkmenistan fee applies."),
            }[code]
        return {
            "uz": ("✅ Yig'im undirilmaydi", "Excel spravochnikda ushbu tashuv turi bo'yicha yig'im majburiy emas deb belgilangan."),
            "ru": ("✅ Сбор не взимается", "В Excel-справочнике по данному виду перевозки сбор указан как необязательный."),
            "en": ("✅ Fee is not charged", "The Excel reference data marks the fee as not mandatory for this carriage type."),
        }[code]
    if dues_cd == "3":
        if turkmenistan_extra_fee_applies(result):
            return {
                "uz": (f"⚠️ Yig'im ruxsatnoma turiga qarab aniqlanadi; <b>{turkmenistan_extra_fee_text(code)}</b>", "Spravochnikda yig'im ruxsatnoma turiga qarab belgilangan, Turkmaniston bo'yicha qo'shimcha yig'im ham qo'llanadi."),
                "ru": (f"⚠️ Сбор определяется по виду разрешения; <b>{turkmenistan_extra_fee_text(code)}</b>", "Сбор определяется по виду разрешения, также применяется дополнительный сбор по Туркменистану."),
                "en": (f"⚠️ Fee depends on the permit type; <b>{turkmenistan_extra_fee_text(code)}</b>", "The fee depends on the permit type and the additional Turkmenistan fee also applies."),
            }[code]
        return {
            "uz": ("⚠️ Yig'im ruxsatnoma turiga qarab aniqlanadi", "Spravochnikda yig'im ruxsatnoma turiga qarab belgilanishi ko'rsatilgan."),
            "ru": ("⚠️ Сбор определяется по виду разрешения", "В справочнике указано, что сбор определяется в зависимости от вида разрешения."),
            "en": ("⚠️ Fee depends on the permit type", "The reference data states that the fee is determined by the permit type."),
        }[code]
    if dues_cd != "1":
        if turkmenistan_extra_fee_applies(result):
            return {
                "uz": (f"💵 Yig'im undiriladi: <b>{turkmenistan_extra_fee_text(code)}</b>", "Turkmaniston bo'yicha qo'shimcha yig'im qo'llanadi."),
                "ru": (f"💵 Сбор взимается: <b>{turkmenistan_extra_fee_text(code)}</b>", "Применяется дополнительный сбор по Туркменистану."),
                "en": (f"💵 Fee is charged: <b>{turkmenistan_extra_fee_text(code)}</b>", "The additional Turkmenistan fee applies."),
            }[code]
        return {
            "uz": ("⚪ Yig'im qo'llanmaydi", "Yig'im bo'yicha majburiy belgi mavjud emas."),
            "ru": ("⚪ Сбор не применяется", "Обязательная отметка по сбору отсутствует."),
            "en": ("⚪ Fee is not applied", "There is no mandatory fee mark in the reference data."),
        }[code]

    rate = PermitRuleService._fee_rate(result.vehicle_country.code, code)
    if turkmenistan_extra_fee_applies(result):
        rate = f"{rate}; {turkmenistan_extra_fee_text(code)}"
    return {
        "uz": (f"💵 Yig'im undiriladi: <b>{rate}</b>", "Excel spravochnikda yig'im majburiy deb belgilanganligi sababli stavka qo'llanadi."),
        "ru": (f"💵 Сбор взимается: <b>{rate}</b>", "Так как в Excel-справочнике сбор указан как обязательный, применяется ставка сбора."),
        "en": (f"💵 Fee is charged: <b>{rate}</b>", "Because the Excel reference data marks the fee as mandatory, the fee rate is applied."),
    }[code]


def additional_note_lines(result: PermitResult, lang: str | None = "uz") -> list[str]:
    code = _lang(lang)
    rule = result.rule or {}
    notes: list[str] = []

    if turkmenistan_extra_fee_applies(result):
        notes.append({
            "uz": "Turkmaniston Respublikasi yuk avtotransport vositasi bilan uchinchi mamlakatlardan O'zbekistonga yuk olib kirish yoki O'zbekiston hududidan yuk olib chiqishda 375 USD qo'shimcha yig'im undiriladi.",
            "ru": "Для грузовых автотранспортных средств Туркменистана при ввозе грузов из третьих стран в Узбекистан либо вывозе грузов с территории Узбекистана взимается дополнительный сбор 375 USD.",
            "en": "For Turkmenistan freight vehicles, an additional fee of 375 USD is charged when importing goods into Uzbekistan from third countries or exporting goods from Uzbekistan.",
        }[code])

    if result.vehicle_country.code == IRAN_CODE:
        notes.append({
            "uz": "Eron Islom Respublikasi avtotransport vositalari uchun kirish va tranzit yig'im stavkasi tenglik asosida 0 USD etib belgilangan.",
            "ru": "Для автотранспортных средств Исламской Республики Иран ставка сбора за въезд и транзит на основе взаимности установлена в размере 0 USD.",
            "en": "For vehicles of the Islamic Republic of Iran, the entry and transit fee rate is set at 0 USD on a reciprocity basis.",
        }[code])

    if is_eu_or_azerbaijan(result.vehicle_country.code) and str(rule.get("dues_cd")) == "1":
        notes.append({
            "uz": "Yevropa Ittifoqi davlatlari va Ozarbayjon bo'yicha yig'im muddati chiqishda transport vositasining haqiqiy bo'lgan muddatiga qarab qayta hisob-kitob qilinadi.",
            "ru": "По государствам Европейского союза и Азербайджану сумма сбора при выезде пересчитывается исходя из фактического срока нахождения транспортного средства.",
            "en": "For EU countries and Azerbaijan, the fee is recalculated on exit based on the vehicle's actual stay period.",
        }[code])

    if str(rule.get("permission_cd")) == "1":
        notes.append({
            "uz": "Ruxsatnoma blanki milliy tashuvchilar ehtiyojidan ortiq qismdan realizatsiya qilinganda 400 USD undiriladi; tranzit ruxsatnomasi uchun 0,5 koeffitsiyent, uchinchi mamlakatlardan yuk tashish ruxsatnomasi uchun 2,0 koeffitsiyent qo'llaniladi.",
            "ru": "При реализации разрешения сверх потребности национальных перевозчиков взимается 400 USD; для транзитного разрешения применяется коэффициент 0,5, для разрешения на перевозку из третьих стран — коэффициент 2,0.",
            "en": "When permit forms are issued from the surplus over national carriers' needs, 400 USD is charged; a 0.5 coefficient applies to transit permits and a 2.0 coefficient to third-country carriage permits.",
        }[code])

    notes.extend([
        {
            "uz": "Agar transport vositasi og'ir vaznli yoki yirik gabaritli bo'lsa, mazkur yig'imlardan tashqari qonunchilikda belgilangan alohida to'lovlar ham undiriladi.",
            "ru": "Если транспортное средство является тяжеловесным или крупногабаритным, помимо указанных сборов взимаются отдельные платежи, установленные законодательством.",
            "en": "If the vehicle is heavy or oversized, separate statutory charges are collected in addition to these fees.",
        }[code],
        {
            "uz": "Gumanitar yuklar olib o'tilganda kirish va tranzit yig'imlariga nisbatan 0,5 kamaytiruvchi koeffitsiyent qo'llanishi mumkin.",
            "ru": "При перевозке гуманитарных грузов к ставкам сборов за въезд и транзит может применяться понижающий коэффициент 0,5.",
            "en": "For humanitarian cargo, a reduction coefficient of 0.5 may apply to entry and transit fee rates.",
        }[code],
        {
            "uz": "Agar xalqaro shartnomada boshqacha tartib belgilangan bo'lsa, xalqaro shartnoma qoidalari qo'llaniladi.",
            "ru": "Если международным договором установлен иной порядок, применяются правила международного договора.",
            "en": "If an international treaty establishes different rules, the treaty provisions apply.",
        }[code],
    ])
    return notes


def build_permit_message(result: PermitResult, timezone: str = "Asia/Tashkent", lang: str | None = "uz") -> str:
    code = _lang(lang)
    now = datetime.now(_load_timezone(timezone)).strftime("%d.%m.%Y, %H:%M")
    rule = result.rule
    fee_text, _ = fee_status_lines(result, code)
    labels = {
        "uz": {
            "title": "🚛 <b>Ruxsatnoma va yig'im tekshiruvi</b>",
            "origin": "📍 Tashuv boshlangan davlat",
            "destination": "🏁 Tashuv tugaydigan davlat",
            "vehicle": "🚚 Avtotransport ro'yxatdan o'tgan davlat",
            "type": "🧭 Aniqlangan tashuv turi",
            "exceptions_title": "🧾 Ushbu tashuv turi bo'yicha ruxsatnoma talab etilmaydigan istisno holatlar",
            "notes_title": "📌 Qo'shimcha izohlar",
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
            "exceptions_title": "🧾 Исключения, при которых разрешение по данному виду перевозки не требуется",
            "notes_title": "📌 Дополнительные примечания",
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
            "exceptions_title": "🧾 Exceptions where a permit is not required for this carriage type",
            "notes_title": "📌 Additional notes",
            "unknown": "⚠️ This response is not a final legal conclusion. Re-checking in the authorized system is required.",
            "advisory": "⚠️ The information is provided for reference and advisory purposes.",
            "time": "🕘 Check time",
        },
    }[code]

    lines = [
        labels["title"],
        "━━━━━━━━━━━━━━━━━━━━",
        f"{labels['origin']}: <b>{_html(country_label(result.origin, code))}</b>",
        f"{labels['destination']}: <b>{_html(country_label(result.destination, code))}</b>",
        f"{labels['vehicle']}: <b>{_html(country_label(result.vehicle_country, code))}</b>",
        "",
        f"{labels['type']}: <b>{_html(transport_type_label(result.vid_cd, result.vid_name, code))}</b>",
        permit_status_text(rule, code),
        fee_text,
        "",
    ]
    if result.exceptions:
        lines.append(labels["exceptions_title"] + ":")
        for index, item in enumerate(result.exceptions, start=1):
            lines.append(f"{index}. {_html(item.get('exception_desc'))}")
        lines.append("")
    if not rule:
        lines.append(labels["unknown"])
    note_lines = additional_note_lines(result, code)
    if note_lines:
        lines.append(labels["notes_title"] + ":")
        for index, note in enumerate(note_lines, start=1):
            lines.append(f"{index}. {_html(note)}")
    lines.extend([
        "━━━━━━━━━━━━━━━━━━━━",
        labels["advisory"],
        f"{labels['time']}: {now}",
    ])
    return "\n".join(lines)
