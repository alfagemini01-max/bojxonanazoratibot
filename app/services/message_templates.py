from __future__ import annotations

from datetime import datetime, timedelta, timezone as datetime_timezone
from html import escape
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.i18n import normalize_lang
from app.repositories.base import VehicleRecord


PRIMARY_DOCS = {"Tranzit deklaratsiya", "Eksport 3 qadam", "YUBNK"}

TR = {
    "uz": {
        "status_ok": "✅ NAZORATDAGI YUK HUJJATI TOPILMADI",
        "status_info": "🟢 NAZORAT HUJJATI MAVJUD",
        "status_warn": "🟡 E'TIBOR TALAB ETILADI",
        "status_danger": "🔴 DIQQAT",
        "status_neutral": "⚪ TEKSHIRUV TO'LIQ YAKUNLANMADI",
        "foreign": "Xorijiy davlat transport vositasi",
        "national": "Milliy avtotransport vositasi",
        "vehicle": "Transport vositasi",
        "cargo_doc": "Nazoratdagi yuk hujjati",
        "not_found": "topilmadi",
        "docs_count": "Nazoratda: <b>{count} ta hujjat</b>",
        "doc_number": "Raqami",
        "from_post": "Nazoratga qo'ygan post",
        "to_post": "Nazoratga qo'yilgan post",
        "date": "Sana",
        "deadline": "Muddat",
        "state": "Holati",
        "debt": "Bojxona yig'imlaridan qarzdorlik",
        "fine": "IIB jarimasi",
        "ban": "Boshqa taqiqlar",
        "none": "yo'q",
        "exists": "bor",
        "not_checked": "tekshirilmadi",
        "may_be_calculated": "hisoblanishi mumkin",
        "decision_numbers": "Jarima to'g'risidagi qaror raqamlari",
        "fine_pay_notice": "Chegara bojxona postiga kelgunga qadar IIB jarimalarini to'lash choralarini ko'ring.",
        "iib_search": "Ushbu avtotransport vositasiga IIB tomonidan qidiruv e'lon qilingan. IIB organlari bilan bog'lanishingizni so'raymiz.",
        "cargo_warning": "⚠️ <b>YUK NAZORATI BO'YICHA OGOHLANTIRISH</b>\nAgar ushbu transport vositasida yuk bilan xalqaro tashuv amalga oshirilayotgan bo'lsa, chegara bojxona postiga yetib kelgunga qadar bojxona organlarida tegishli nazorat hujjatini rasmiylashtiring.",
        "doc_overdue_warning": "⚠️ Nazoratdagi yuk hujjati bo'yicha belgilangan muddat o'tgan. Belgilangan bojxona postida hujjatni nazoratdan yechish talab etiladi.",
        "doc_release_warning": "ℹ️ Yuk belgilangan postga yetkazilgach, nazoratdagi yuk hujjatini bojxona organlarida nazoratdan yechish talab etiladi.",
        "system_error_1": "⏳ Muhim tizimlardan biri javob bermadi.",
        "system_error_2": "Bojxona postida qayta tekshirish talab etiladi.",
        "conclusion_ban": "IIB tomonidan qidiruv holati aniqlangan. IIB organlari bilan bog'lanish talab etiladi.",
        "conclusion_doc_danger": "Nazoratdagi yuk hujjati muddati o'tgan. Belgilangan bojxona postida nazoratdan yechish talab etiladi.",
        "conclusion_doc": "Nazoratdagi yuk hujjati mavjud. Belgilangan tartibda nazoratdan yechish talab etiladi.",
        "conclusion_fine": "IIB jarimasi mavjud. Chegara postiga kelgunga qadar jarimani to'lash tavsiya etiladi.",
        "conclusion_clear": "Transport vositasi bo'yicha faol yuk nazorati hujjati aniqlanmadi.",
        "not_found_message": "Bunday avtomobil bo'yicha ma'lumot topilmadi.",
        "retry_plate": "Davlat raqamini to'g'ri formatda qayta yuboring.",
    },
    "ru": {
        "status_ok": "✅ ДОКУМЕНТ ГРУЗОВОГО КОНТРОЛЯ НЕ НАЙДЕН",
        "status_info": "🟢 ИМЕЕТСЯ КОНТРОЛЬНЫЙ ДОКУМЕНТ",
        "status_warn": "🟡 ТРЕБУЕТСЯ ВНИМАНИЕ",
        "status_danger": "🔴 ВНИМАНИЕ",
        "status_neutral": "⚪ ПРОВЕРКА НЕ ЗАВЕРШЕНА",
        "foreign": "Иностранное транспортное средство",
        "national": "Национальное транспортное средство",
        "vehicle": "Транспортное средство",
        "cargo_doc": "Документ грузового контроля",
        "not_found": "не найден",
        "docs_count": "На контроле: <b>{count} документ(ов)</b>",
        "doc_number": "Номер",
        "from_post": "Пост постановки на контроль",
        "to_post": "Пост назначения контроля",
        "date": "Дата",
        "deadline": "Срок",
        "state": "Статус",
        "debt": "Задолженность по таможенным сборам",
        "fine": "Штраф ОВД",
        "ban": "Прочие ограничения",
        "none": "нет",
        "exists": "имеется",
        "not_checked": "не проверено",
        "may_be_calculated": "может быть начислено",
        "decision_numbers": "Номера постановлений о наложении штрафа",
        "fine_pay_notice": "До прибытия на пограничный таможенный пост примите меры по оплате штрафов ОВД.",
        "iib_search": "По данному транспортному средству органами внутренних дел объявлен розыск. Просим обратиться в органы внутренних дел.",
        "cargo_warning": "⚠️ <b>ПРЕДУПРЕЖДЕНИЕ ПО ГРУЗОВОМУ КОНТРОЛЮ</b>\nЕсли на данном транспортном средстве осуществляется международная перевозка груза, до прибытия на пограничный таможенный пост оформите соответствующий контрольный документ в таможенных органах.",
        "doc_overdue_warning": "⚠️ По документу грузового контроля истек установленный срок. На указанном таможенном посту требуется снятие документа с контроля.",
        "doc_release_warning": "ℹ️ После доставки груза в указанный пост документ грузового контроля должен быть снят с контроля в таможенных органах.",
        "system_error_1": "⏳ Одна из важных систем не ответила.",
        "system_error_2": "Требуется повторная проверка на таможенном посту.",
        "conclusion_ban": "Выявлено объявление в розыск органами внутренних дел. Требуется обратиться в органы внутренних дел.",
        "conclusion_doc_danger": "Срок документа грузового контроля истек. Требуется снятие с контроля на указанном таможенном посту.",
        "conclusion_doc": "Имеется документ грузового контроля. Требуется снятие с контроля в установленном порядке.",
        "conclusion_fine": "Имеется штраф ОВД. Рекомендуется оплатить штраф до прибытия на пограничный пост.",
        "conclusion_clear": "Активный документ грузового контроля по транспортному средству не выявлен.",
        "not_found_message": "По данному автомобилю сведения не найдены.",
        "retry_plate": "Отправьте государственный номер в правильном формате.",
    },
    "en": {
        "status_ok": "✅ NO CARGO CONTROL DOCUMENT FOUND",
        "status_info": "🟢 CONTROL DOCUMENT EXISTS",
        "status_warn": "🟡 ATTENTION REQUIRED",
        "status_danger": "🔴 ATTENTION",
        "status_neutral": "⚪ CHECK NOT COMPLETED",
        "foreign": "Foreign state vehicle",
        "national": "National vehicle",
        "vehicle": "Vehicle",
        "cargo_doc": "Cargo control document",
        "not_found": "not found",
        "docs_count": "Under control: <b>{count} document(s)</b>",
        "doc_number": "Number",
        "from_post": "Control registration post",
        "to_post": "Control destination post",
        "date": "Date",
        "deadline": "Deadline",
        "state": "Status",
        "debt": "Customs fee debt",
        "fine": "Internal Affairs fine",
        "ban": "Other restrictions",
        "none": "none",
        "exists": "exists",
        "not_checked": "not checked",
        "may_be_calculated": "may be charged",
        "decision_numbers": "Fine decision numbers",
        "fine_pay_notice": "Please take measures to pay Internal Affairs fines before arriving at the border customs post.",
        "iib_search": "This vehicle has been declared wanted by the internal affairs authorities. Please contact the internal affairs authorities.",
        "cargo_warning": "⚠️ <b>CARGO CONTROL NOTICE</b>\nIf this vehicle is carrying out international cargo transportation, arrange the relevant customs control document with the customs authorities before arriving at the border customs post.",
        "doc_overdue_warning": "⚠️ The established deadline for the cargo control document has expired. The document must be released from control at the designated customs post.",
        "doc_release_warning": "ℹ️ After the cargo is delivered to the designated post, the cargo control document must be released from control by the customs authorities.",
        "system_error_1": "⏳ One of the important systems did not respond.",
        "system_error_2": "A repeated check at the customs post is required.",
        "conclusion_ban": "A wanted status by the internal affairs authorities has been identified. Contacting the internal affairs authorities is required.",
        "conclusion_doc_danger": "The cargo control document deadline has expired. Release from control at the designated customs post is required.",
        "conclusion_doc": "A cargo control document exists. Release from control is required in the established procedure.",
        "conclusion_fine": "An Internal Affairs fine exists. It is recommended to pay the fine before arriving at the border post.",
        "conclusion_clear": "No active cargo control document was identified for the vehicle.",
        "not_found_message": "No information was found for this vehicle.",
        "retry_plate": "Please send the state plate number in the correct format.",
    },
}

DOC_TYPES = {
    "Tranzit deklaratsiya": {"uz": "Tranzit deklaratsiya", "ru": "Транзитная декларация", "en": "Transit declaration"},
    "Eksport 3 qadam": {"uz": "Eksport 3 qadam", "ru": "Экспорт 3 шага", "en": "Export step 3"},
    "YUBNK": {"uz": "YUBNK", "ru": "ККДГ", "en": "Cargo delivery control book"},
    "Majburiyatnoma": {"uz": "Majburiyatnoma", "ru": "Обязательство", "en": "Commitment form"},
}

DOC_ICON = {
    "Tranzit deklaratsiya": "📦",
    "Eksport 3 qadam": "📤",
    "YUBNK": "🚚",
    "Majburiyatnoma": "📄",
}

STATE_TRANSLATIONS = {
    "Muddati o'tmagan": {"uz": "Muddati o'tmagan", "ru": "Срок не истек", "en": "Not expired"},
    "Muddati o'tgan": {"uz": "Muddati o'tgan", "ru": "Срок истек", "en": "Expired"},
    "Tugashiga 3 kun qoldi": {"uz": "Tugashiga 3 kun qoldi", "ru": "До окончания 3 дня", "en": "3 days remaining"},
    "Yuk yetkazib berilmagan": {"uz": "Yuk yetkazib berilmagan", "ru": "Груз не доставлен", "en": "Cargo not delivered"},
}

VEHICLE_TYPES = {
    "Yengil avtomobil": {"uz": "yengil avtomobil", "ru": "легковой автомобиль", "en": "passenger car"},
    "Yuk mashinasi": {"uz": "yuk mashinasi", "ru": "грузовой автомобиль", "en": "truck"},
    "Avtobus": {"uz": "avtobus", "ru": "автобус", "en": "bus"},
    "Tirkama": {"uz": "tirkama", "ru": "прицеп", "en": "trailer"},
    "Noma'lum": {"uz": "noma'lum", "ru": "неизвестно", "en": "unknown"},
}


def _tr(lang: str, key: str, **kwargs: object) -> str:
    return TR[normalize_lang(lang)][key].format(**kwargs)


def _safe(value: object) -> str:
    if value is None:
        return ""
    return escape(str(value), quote=False)


def _load_timezone(timezone: str):
    try:
        return ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        return datetime_timezone(timedelta(hours=5))


def _localized(mapping: dict[str, str], lang: str) -> str:
    return mapping.get(normalize_lang(lang)) or mapping["uz"]


def _vehicle_icon(vehicle_type: object) -> str:
    text = str(vehicle_type or "").lower()
    if "yuk" in text:
        return "🚚"
    if "avtobus" in text:
        return "🚌"
    if "tirkama" in text:
        return "🔗"
    return "🚘"


def _transport_label(record: VehicleRecord, lang: str) -> str:
    origin = str(record.get("origin") or "Noma'lum")
    vehicle_type = str(record.get("vehicle_type") or "Noma'lum")
    origin_key = "foreign" if origin == "Xorijiy" else "national" if origin == "Milliy" else "vehicle"
    type_text = _localized(VEHICLE_TYPES.get(vehicle_type, VEHICLE_TYPES["Noma'lum"]), lang)
    return f"{_tr(lang, origin_key)}, {type_text}"


def _status_title(record: VehicleRecord, lang: str) -> str:
    status = str(record.get("status") or "neutral")
    return _tr(lang, f"status_{status}" if f"status_{status}" in TR[normalize_lang(lang)] else "status_neutral")


def _check_value(check: dict[str, object] | None, lang: str) -> str:
    check = check or {"level": "ok", "text": "yo'q"}
    level = str(check.get("level", "ok"))
    text = str(check.get("text", ""))
    if level == "ok":
        return f"❌ {_tr(lang, 'none')}"
    if level == "neutral":
        return f"ℹ️ {_tr(lang, 'not_checked')}"
    lowered = text.lower().replace("—", "-")
    if "hisoblanishi mumkin" in lowered or "yig'im hisoblanishi mumkin" in lowered:
        return f"⚠️ {_tr(lang, 'may_be_calculated')}"
    if "bor -" in lowered:
        amount = text.split("-", 1)[1].strip()
        return f"⚠️ {_tr(lang, 'exists')} - {_safe(amount)}"
    return f"⚠️ {_tr(lang, 'exists')}"


def _fine_lines(check: dict[str, object] | None, lang: str) -> list[str]:
    check = check or {"level": "ok", "text": "yo'q"}
    level = str(check.get("level", "ok"))
    if level == "ok":
        return [f"🚓 {_tr(lang, 'fine')}: <b>❌ {_tr(lang, 'none')}</b>"]
    if level == "neutral":
        return [f"🚓 {_tr(lang, 'fine')}: <b>ℹ️ {_tr(lang, 'not_checked')}</b>"]

    lines = [f"🚓 {_tr(lang, 'fine')}: <b>⚠️ {_tr(lang, 'exists')}</b>"]
    if check.get("count") and check.get("amount"):
        if lang == "ru":
            lines.append(f"   {_safe(check.get('count'))} шт., всего {_safe(check.get('amount'))}")
        elif lang == "en":
            lines.append(f"   {_safe(check.get('count'))} item(s), total {_safe(check.get('amount'))}")
        else:
            lines.append(f"   {_safe(check.get('count'))} ta, jami {_safe(check.get('amount'))}")
    elif check.get("text"):
        lines.append(f"   {_safe(check.get('text'))}")
    decisions = list(check.get("decisions") or [])
    if decisions:
        lines.append(f"   {_tr(lang, 'decision_numbers')}:")
        for number in decisions:
            lines.append(f"   • <code>{_safe(number)}</code>")
    lines.append(f"   ⚠️ {_tr(lang, 'fine_pay_notice')}")
    return lines


def _ban_line(check: dict[str, object] | None, lang: str) -> str:
    check = check or {"level": "ok", "text": "yo'q"}
    level = str(check.get("level", "ok"))
    if level in {"danger", "warn"}:
        return f"🚫 {_tr(lang, 'ban')}: <b>🔴 {_tr(lang, 'exists')}</b>\n   ⚠️ {_tr(lang, 'iib_search')}"
    if level == "neutral":
        return f"🚫 {_tr(lang, 'ban')}: <b>ℹ️ {_tr(lang, 'not_checked')}</b>"
    return f"🚫 {_tr(lang, 'ban')}: <b>❌ {_tr(lang, 'none')}</b>"


def _doc_type(doc_type: str, lang: str) -> str:
    return _localized(DOC_TYPES.get(doc_type, {"uz": doc_type, "ru": doc_type, "en": doc_type}), lang)


def _doc_state(state: object, lang: str) -> str:
    text = str(state or "")
    return _localized(STATE_TRANSLATIONS.get(text, {"uz": text, "ru": text, "en": text}), lang)


def _doc_lines(index: int, doc: dict[str, object], lang: str) -> list[str]:
    doc_type = str(doc.get("type") or "Hujjat")
    icon = DOC_ICON.get(doc_type, "📄")
    level = str(doc.get("level") or "ok")
    level_icon = "🔴" if level == "danger" else "⚠️" if level == "warn" else "✅"
    lines = [
        f"{index}. {icon} <b>{_safe(_doc_type(doc_type, lang))}</b>",
        f"   📄 {_tr(lang, 'doc_number')}: <code>{_safe(doc.get('number'))}</code>",
    ]
    if doc.get("from_post"):
        lines.append(f"   📍 {_tr(lang, 'from_post')}: {_safe(doc.get('from_post'))}")
    if doc_type != "Majburiyatnoma" and doc.get("to_post"):
        lines.append(f"   🏁 {_tr(lang, 'to_post')}: {_safe(doc.get('to_post'))}")
    if doc.get("start_date"):
        lines.append(f"   🗓 {_tr(lang, 'date')}: {_safe(doc.get('start_date'))}")
    if doc.get("deadline"):
        lines.append(f"   ⏰ {_tr(lang, 'deadline')}: {_safe(doc.get('deadline'))}")
    if doc.get("state"):
        lines.append(f"   {level_icon} {_tr(lang, 'state')}: <b>{_safe(_doc_state(doc.get('state'), lang))}</b>")
    return lines


def _primary_docs(docs: list[dict[str, object]]) -> list[dict[str, object]]:
    return [doc for doc in docs if str(doc.get("type")) in PRIMARY_DOCS]


def _conclusion(record: VehicleRecord, docs: list[dict[str, object]], lang: str) -> str:
    if record.get("system_error"):
        return _tr(lang, "system_error_2")
    if str((record.get("ban") or {}).get("level")) in {"danger", "warn"}:
        return _tr(lang, "conclusion_ban")
    primary = _primary_docs(docs)
    if any(str(doc.get("level")) == "danger" for doc in primary):
        return _tr(lang, "conclusion_doc_danger")
    if primary:
        return _tr(lang, "conclusion_doc")
    if str((record.get("fine") or {}).get("level")) in {"danger", "warn"}:
        return _tr(lang, "conclusion_fine")
    return _tr(lang, "conclusion_clear")


def build_vehicle_message(record: VehicleRecord, timezone: str = "Asia/Tashkent", lang: str = "uz") -> str:
    lang = normalize_lang(lang)
    docs = list(record.get("docs") or [])
    primary = _primary_docs(docs)
    now = datetime.now(_load_timezone(timezone)).strftime("%d.%m.%Y, %H:%M")

    lines: list[str] = [
        f"{_vehicle_icon(record.get('vehicle_type'))} <b>{_safe(record.get('plate'))}</b>",
        f"<i>{_safe(_transport_label(record, lang))}</i>",
        "━━━━━━━━━━━━━━━━━━━━",
        f"<b>{_status_title(record, lang)}</b>",
    ]

    if record.get("system_error"):
        lines.extend(["", _tr(lang, "system_error_1"), _tr(lang, "system_error_2")])
    elif docs:
        lines.append(f"📋 {_tr(lang, 'docs_count', count=len(docs))}")
        lines.append("")
        for index, doc in enumerate(docs, start=1):
            lines.extend(_doc_lines(index, doc, lang))
            lines.append("")
    else:
        lines.append(f"📋 {_tr(lang, 'cargo_doc')}: <b>{_tr(lang, 'not_found')}</b>")

    if not primary and not record.get("system_error"):
        lines.extend(["", _tr(lang, "cargo_warning")])
    elif any(str(doc.get("level")) == "danger" for doc in primary):
        lines.extend(["", _tr(lang, "doc_overdue_warning")])
    elif primary:
        lines.extend(["", _tr(lang, "doc_release_warning")])

    lines.extend(["━━━━━━━━━━━━━━━━━━━━", f"💰 {_tr(lang, 'debt')}: <b>{_check_value(record.get('debt'), lang)}</b>"])
    lines.extend(_fine_lines(record.get("fine"), lang))
    lines.append(_ban_line(record.get("ban"), lang))
    lines.extend(["━━━━━━━━━━━━━━━━━━━━", f"ℹ️ {_safe(_conclusion(record, docs, lang))}", f"🕘 {_safe(now)}"])
    return "\n".join(line for line in lines if line is not None).strip()


def build_not_found_message(plate: str, timezone: str = "Asia/Tashkent", lang: str = "uz") -> str:
    lang = normalize_lang(lang)
    now = datetime.now(_load_timezone(timezone)).strftime("%d.%m.%Y, %H:%M")
    return "\n".join(
        [
            f"🚘 <b>{_safe(plate)}</b>",
            "━━━━━━━━━━━━━━━━━━━━",
            f"ℹ️ {_tr(lang, 'not_found_message')}",
            _tr(lang, "retry_plate"),
            f"🕘 {_safe(now)}",
        ]
    )
