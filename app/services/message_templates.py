from __future__ import annotations

from datetime import datetime
from html import escape
from zoneinfo import ZoneInfo

from app.repositories.base import VehicleRecord


STATUS_TITLE = {
    "ok": "✅ NAZORATDAGI HUJJATLAR TOPILMADI",
    "info": "🟢 NAZORAT HUJJATI MAVJUD",
    "warn": "🟡 E'TIBOR TALAB ETILADI",
    "danger": "🔴 DIQQAT",
    "neutral": "⚪ TEKSHIRUV TO'LIQ YAKUNLANMADI",
}

LEVEL_ICON = {
    "ok": "✅",
    "info": "🟢",
    "warn": "⚠️",
    "danger": "🔴",
    "neutral": "ℹ️",
}

DOC_ICON = {
    "Tranzit deklaratsiya": "📦",
    "Eksport 3 qadam": "📤",
    "YUBNK": "🚚",
    "Majburiyatnoma": "📄",
}


def _safe(value: object) -> str:
    if value is None:
        return ""
    return escape(str(value), quote=False)


def _transport_label(record: VehicleRecord) -> str:
    origin = str(record.get("origin") or "Noma'lum")
    vehicle_type = str(record.get("vehicle_type") or "Noma'lum")

    if origin == "Xorijiy":
        origin_text = "Xorijiy davlat transport vositasi"
    elif origin == "Milliy":
        origin_text = "Milliy avtotransport vositasi"
    else:
        origin_text = "Transport vositasi"

    return f"{origin_text}, {vehicle_type.lower()}"


def _vehicle_icon(vehicle_type: object) -> str:
    text = str(vehicle_type or "").lower()
    if "yuk" in text:
        return "🚚"
    if "avtobus" in text:
        return "🚌"
    if "tirkama" in text:
        return "🔗"
    return "🚘"


def _check_line(title: str, check: dict[str, str] | None) -> str:
    check = check or {"level": "ok", "text": "yo'q"}
    level = check.get("level", "ok")
    text = check.get("text", "yo'q")
    if level == "ok":
        prefix = "❌"
    elif level == "danger":
        prefix = "🔴"
    elif level == "warn":
        prefix = "⚠️"
    else:
        prefix = "ℹ️"
    return f"{title}: <b>{prefix} {_safe(text)}</b>"


def _doc_lines(index: int, doc: dict[str, object]) -> list[str]:
    doc_type = str(doc.get("type") or "Hujjat")
    icon = DOC_ICON.get(doc_type, "📄")
    level = str(doc.get("level") or "ok")
    level_icon = LEVEL_ICON.get(level, "ℹ️")
    lines = [
        f"{index}. {icon} <b>{_safe(doc_type)}</b>",
        f"   📄 Raqami: <code>{_safe(doc.get('number'))}</code>",
    ]

    if doc.get("from_post"):
        lines.append(f"   📍 Nazoratga qo'ygan post: {_safe(doc.get('from_post'))}")
    if doc_type != "Majburiyatnoma" and doc.get("to_post"):
        lines.append(f"   🏁 Nazoratga qo'yilgan post: {_safe(doc.get('to_post'))}")
    if doc.get("start_date"):
        lines.append(f"   🗓 Sana: {_safe(doc.get('start_date'))}")
    if doc.get("deadline"):
        lines.append(f"   ⏰ Muddat: {_safe(doc.get('deadline'))}")
    if doc.get("state"):
        lines.append(f"   {level_icon} Holati: <b>{_safe(doc.get('state'))}</b>")
    return lines


def build_vehicle_message(record: VehicleRecord, timezone: str = "Asia/Tashkent") -> str:
    plate = record.get("plate") or ""
    status = str(record.get("status") or "neutral")
    docs = list(record.get("docs") or [])
    now = datetime.now(ZoneInfo(timezone)).strftime("%d.%m.%Y, %H:%M")
    icon = _vehicle_icon(record.get("vehicle_type"))
    conclusion = record.get("conclusion") or "Ma'lumot tekshirildi."
    debt_line = _check_line("Bojxona yig'imlaridan qarzdorlik", record.get("debt"))
    fine_line = _check_line("YHXB jarimasi", record.get("fine"))
    ban_line = _check_line("Boshqa taqiqlar", record.get("ban"))

    lines: list[str] = [
        f"{icon} <b>{_safe(plate)}</b>",
        f"<i>{_safe(_transport_label(record))}</i>",
        "━━━━━━━━━━━━━━━━━━━━",
        f"<b>{STATUS_TITLE.get(status, STATUS_TITLE['neutral'])}</b>",
    ]

    if record.get("system_error"):
        lines.extend(
            [
                "",
                "⏳ Muhim tizimlardan biri javob bermadi.",
                "Bojxona postida qayta tekshirish talab etiladi.",
            ]
        )
    elif docs:
        lines.append(f"📋 Nazoratda: <b>{len(docs)} ta hujjat</b>")
        lines.append("")
        for index, doc in enumerate(docs, start=1):
            lines.extend(_doc_lines(index, doc))
            lines.append("")
    else:
        lines.append("📋 Nazoratdagi hujjat: <b>topilmadi</b>")

    if record.get("expected_missing"):
        lines.append(f"⚠️ {_safe(record.get('expected_missing'))} hujjati rasmiylashtirilishi kerak.")

    if record.get("cargo_control_missing_warning"):
        lines.append(
            "⚠️ Sizda ayni vaqtda yuk bo'yicha nazoratga qo'yilgan hujjat mavjud emas. "
            "Agar transport yuk bilan harakatlanayotgan bo'lsa, tegishli nazorat hujjatlarini rasmiylashtirish talab etiladi."
        )

    lines.extend(
        [
            "━━━━━━━━━━━━━━━━━━━━",
            f"💰 {debt_line}",
            f"🚓 {fine_line}",
            f"🚫 {ban_line}",
            "━━━━━━━━━━━━━━━━━━━━",
            f"ℹ️ {_safe(conclusion)}",
            f"🕘 {_safe(now)}",
        ]
    )
    return "\n".join(line for line in lines if line is not None).strip()


def build_not_found_message(plate: str, timezone: str = "Asia/Tashkent") -> str:
    now = datetime.now(ZoneInfo(timezone)).strftime("%d.%m.%Y, %H:%M")
    return "\n".join(
        [
            f"🚘 <b>{_safe(plate)}</b>",
            "━━━━━━━━━━━━━━━━━━━━",
            "ℹ️ Bunday avtomobil bo'yicha ma'lumot topilmadi.",
            "Davlat raqamini to'g'ri formatda qayta yuboring.",
            f"🕘 {_safe(now)}",
        ]
    )
