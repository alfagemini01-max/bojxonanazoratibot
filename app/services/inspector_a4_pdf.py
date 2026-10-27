from __future__ import annotations

import io
from pathlib import Path
from typing import Any

from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


STATIC_DIR = Path(__file__).resolve().parents[1] / "static"
LANGUAGES = {"uz", "ru", "en"}
GREEN = colors.HexColor("#0A5547")
DEEP_GREEN = colors.HexColor("#073C33")
GOLD = colors.HexColor("#C9A052")
LIGHT_GREEN = colors.HexColor("#EDF6F2")
LIGHT_GRAY = colors.HexColor("#F5F7F6")
MID_GRAY = colors.HexColor("#66756F")


TEXT = {
    "uz": {
        "agency": "O'ZBEKISTON RESPUBLIKASI DAVLAT BOJXONA XIZMATI",
        "system": "Yagona elektron bojxona axborot tizimi",
        "invoice": "BOJXONA TO'LOVLARI INVOYSI",
        "commitment": "TRANZIT MAJBURIYATNOMASI",
        "insurance": "ELEKTRON SUG'URTA POLISI",
        "document_no": "Hujjat raqami", "issued": "Rasmiylashtirilgan sana",
        "post": "Bojxona posti", "inspector": "Rasmiylashtirgan inspektor",
        "driver": "Haydovchi / to'lovchi", "passport": "Pasport", "nationality": "Fuqaroligi",
        "phone": "Telefon", "vehicle": "Transport vositasi", "model": "Marka / model",
        "country": "Ro'yxatdan o'tgan davlat", "trailer": "Tirkama raqami",
        "cargo": "Yuk tavsifi", "route": "Yo'nalish / manzil", "details": "ASOSIY MA'LUMOTLAR",
        "payments": "HISOBLANGAN TO'LOVLAR", "payment_name": "To'lov turi", "amount": "Summa",
        "total": "JAMI TO'LOV", "paid": "TO'LANGAN", "pending": "TO'LOV KUTILMOQDA",
        "obligations": "MAJBURIYATLAR",
        "obligation_text": [
            "Belgilangan bojxona va yo'l harakati qoidalariga rioya qilish.",
            "Transport vositasi va yuk bo'yicha ma'lumotlarni o'zgartirmasdan saqlash.",
            "Bojxona xodimining qonuniy ko'rsatmalarini bajarish.",
            "QR-kodli elektron hujjatni safar davomida saqlash.",
        ],
        "insurance_info": "SUG'URTA QAYDI", "policy_holder": "Sug'urtalanuvchi",
        "premium": "Sug'urta badali", "coverage": "Elektron polis qaydi",
        "coverage_value": "Bojxona axborot tizimida ro'yxatdan o'tgan",
        "verification": "HUJJATNI TEKSHIRISH",
        "scan": "Hujjatning amaldagi ma'lumotlarini tekshirish uchun QR-kodni skanerlang.",
        "signature": "Inspektor imzosi", "seal": "Muhr joyi",
        "electronic": "Ushbu hujjat elektron tizimda shakllantirilgan.", "page": "Sahifa",
    },
    "ru": {
        "agency": "ГОСУДАРСТВЕННАЯ ТАМОЖЕННАЯ СЛУЖБА РЕСПУБЛИКИ УЗБЕКИСТАН",
        "system": "Единая электронная таможенная информационная система",
        "invoice": "ИНВОЙС ТАМОЖЕННЫХ ПЛАТЕЖЕЙ", "commitment": "ТРАНЗИТНОЕ ОБЯЗАТЕЛЬСТВО",
        "insurance": "ЭЛЕКТРОННЫЙ СТРАХОВОЙ ПОЛИС", "document_no": "Номер документа",
        "issued": "Дата оформления", "post": "Таможенный пост", "inspector": "Оформивший инспектор",
        "driver": "Водитель / плательщик", "passport": "Паспорт", "nationality": "Гражданство",
        "phone": "Телефон", "vehicle": "Транспортное средство", "model": "Марка / модель",
        "country": "Страна регистрации", "trailer": "Номер прицепа", "cargo": "Описание груза",
        "route": "Маршрут / назначение", "details": "ОСНОВНЫЕ СВЕДЕНИЯ",
        "payments": "НАЧИСЛЕННЫЕ ПЛАТЕЖИ", "payment_name": "Вид платежа", "amount": "Сумма",
        "total": "ИТОГО К ОПЛАТЕ", "paid": "ОПЛАЧЕНО", "pending": "ОЖИДАЕТ ОПЛАТЫ",
        "obligations": "ОБЯЗАТЕЛЬСТВА",
        "obligation_text": [
            "Соблюдать установленные таможенные правила и правила дорожного движения.",
            "Сохранять сведения о транспортном средстве и грузе без изменений.",
            "Выполнять законные требования сотрудника таможни.",
            "Хранить электронный документ с QR-кодом в течение поездки.",
        ],
        "insurance_info": "СТРАХОВАЯ ЗАПИСЬ", "policy_holder": "Страхователь",
        "premium": "Страховой взнос", "coverage": "Электронная запись полиса",
        "coverage_value": "Зарегистрировано в таможенной информационной системе",
        "verification": "ПРОВЕРКА ДОКУМЕНТА",
        "scan": "Отсканируйте QR-код для проверки актуальных данных документа.",
        "signature": "Подпись инспектора", "seal": "Место печати",
        "electronic": "Документ сформирован в электронной системе.", "page": "Страница",
    },
    "en": {
        "agency": "STATE CUSTOMS SERVICE OF THE REPUBLIC OF UZBEKISTAN",
        "system": "Unified electronic customs information system",
        "invoice": "CUSTOMS PAYMENT INVOICE", "commitment": "TRANSIT UNDERTAKING",
        "insurance": "ELECTRONIC INSURANCE POLICY", "document_no": "Document number",
        "issued": "Issue date", "post": "Customs post", "inspector": "Issuing inspector",
        "driver": "Driver / payer", "passport": "Passport", "nationality": "Nationality",
        "phone": "Phone", "vehicle": "Vehicle", "model": "Make / model",
        "country": "Registration country", "trailer": "Trailer plate", "cargo": "Cargo description",
        "route": "Route / destination", "details": "KEY DETAILS", "payments": "ASSESSED PAYMENTS",
        "payment_name": "Payment type", "amount": "Amount", "total": "TOTAL DUE",
        "paid": "PAID", "pending": "PAYMENT PENDING", "obligations": "UNDERTAKINGS",
        "obligation_text": [
            "Comply with applicable customs and road safety rules.",
            "Keep vehicle and cargo information unchanged during transit.",
            "Follow lawful instructions issued by customs officers.",
            "Keep the QR-coded electronic document available throughout the journey.",
        ],
        "insurance_info": "INSURANCE RECORD", "policy_holder": "Policyholder",
        "premium": "Insurance premium", "coverage": "Electronic policy record",
        "coverage_value": "Registered in the customs information system", "verification": "DOCUMENT VERIFICATION",
        "scan": "Scan the QR code to verify the current document record.",
        "signature": "Inspector signature", "seal": "Seal",
        "electronic": "This document was generated by the electronic system.", "page": "Page",
    },
}


def _register_fonts() -> tuple[str, str]:
    font_dir = STATIC_DIR / "fonts"
    regular_name, bold_name = "OfficialUbuntu", "OfficialUbuntuBold"
    if regular_name not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(regular_name, str(font_dir / "Ubuntu-R.ttf")))
    if bold_name not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(bold_name, str(font_dir / "Ubuntu-B.ttf")))
    return regular_name, bold_name


def _money(value: Any) -> str:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = 0
    return f"{number:,}".replace(",", " ") + " UZS"


def _qr_drawing(value: str, size: float = 29 * mm) -> Drawing:
    widget = QrCodeWidget(value, barLevel="H")
    x1, y1, x2, y2 = widget.getBounds()
    drawing = Drawing(size, size, transform=[size / (x2 - x1), 0, 0, size / (y2 - y1), 0, 0])
    drawing.add(widget)
    return drawing


def _kind(document: dict[str, Any], index: int) -> str:
    value = f"{document.get('code', '')} {document.get('title', '')} {document.get('type', '')}".lower()
    if "sug'urta" in value or "insurance" in value or "страх" in value or "etsd" in value or index == 2:
        return "insurance"
    if "majbur" in value or "transit" in value or "обяз" in value or index == 1:
        return "commitment"
    return "invoice"


def _inspector_name(value: Any, language: str) -> str:
    raw = str(value or "").strip()
    if raw.lower() in {"bojxona inspektori", "navbatchi inspektor"}:
        return {"uz": "Bojxona inspektori", "ru": "Таможенный инспектор", "en": "Customs inspector"}[language]
    return raw or "-"


def _field_table(rows: list[tuple[str, Any]], styles: dict[str, ParagraphStyle]) -> Table:
    data = [[Paragraph(label, styles["label"]), Paragraph(str(value or "-"), styles["value"])] for label, value in rows]
    table = Table(data, colWidths=[52 * mm, 128 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_GRAY),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCD6D2")),
        ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D7E0DC")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table


def _section_title(text: str, styles: dict[str, ParagraphStyle]) -> Table:
    return Table([[Paragraph(text, styles["section"])]], colWidths=[180 * mm], style=TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), DEEP_GREEN),
        ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))


def _page_footer(canvas: Any, doc: Any, regular: str, bold: str, tr: dict[str, Any]) -> None:
    canvas.saveState()
    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(0.8)
    canvas.line(15 * mm, 13 * mm, 195 * mm, 13 * mm)
    canvas.setFillColor(MID_GRAY)
    canvas.setFont(regular, 7.5)
    canvas.drawString(15 * mm, 8.5 * mm, tr["electronic"])
    canvas.setFont(bold, 7.5)
    canvas.drawRightString(195 * mm, 8.5 * mm, f"{tr['page']} {doc.page}")
    canvas.restoreState()


def build_inspector_document_pdf(
    item: dict[str, Any], *, public_url: str, document_index: int = 0, language: str = "uz"
) -> bytes:
    """Build a document-specific, single-page A4 customs PDF."""
    language = language if language in LANGUAGES else "uz"
    tr = TEXT[language]
    regular, bold = _register_fonts()
    payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}
    documents = payload.get("documents") if isinstance(payload.get("documents"), list) else []
    if documents:
        document_index = min(max(int(document_index), 0), len(documents) - 1)
        selected = documents[document_index] if isinstance(documents[document_index], dict) else {}
    else:
        selected = {"code": item.get("document_no"), "title": "Document"}
    kind = _kind(selected, document_index)
    doc_code = str(selected.get("code") or item.get("document_no") or "DOC")
    title_text = tr[kind]
    paid = payload.get("payment_status") == "paid"

    styles = {
        "agency": ParagraphStyle("agency", fontName=bold, fontSize=12.5, leading=15, textColor=DEEP_GREEN),
        "document_title": ParagraphStyle("document-title", fontName=bold, fontSize=16, leading=19, textColor=colors.white),
        "document_code": ParagraphStyle("document-code", fontName=bold, fontSize=9.5, leading=12, textColor=colors.white, alignment=TA_RIGHT),
        "section": ParagraphStyle("section", fontName=bold, fontSize=9, leading=11, textColor=colors.white),
        "label": ParagraphStyle("label", fontName=regular, fontSize=8.5, leading=10.5, textColor=MID_GRAY),
        "value": ParagraphStyle("value", fontName=bold, fontSize=9, leading=11, textColor=colors.HexColor("#16221E")),
        "body": ParagraphStyle("body", fontName=regular, fontSize=9, leading=13, textColor=colors.HexColor("#273530")),
        "center": ParagraphStyle("center", fontName=regular, fontSize=8, leading=10, alignment=TA_CENTER),
        "status": ParagraphStyle("status", fontName=bold, fontSize=8.5, leading=10, alignment=TA_CENTER, textColor=GREEN if paid else colors.HexColor("#8A5A00")),
    }

    buffer = io.BytesIO()
    pdf = SimpleDocTemplate(
        buffer, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm, topMargin=13 * mm, bottomMargin=17 * mm,
        title=f"{doc_code} - {title_text}", author=tr["agency"], subject=title_text,
    )
    story: list[Any] = []
    emblem_path = STATIC_DIR / "customs-emblem.png"
    emblem = Image(str(emblem_path), width=23 * mm, height=23 * mm) if emblem_path.exists() else Spacer(23 * mm, 23 * mm)
    header = Table([[emblem, Paragraph(f"{tr['agency']}<br/><font size='8' color='#66756F'>{tr['system']}</font>", styles["agency"]), Paragraph(f"{tr['document_no']}<br/><b>{doc_code}</b>", styles["document_code"])]], colWidths=[28 * mm, 105 * mm, 47 * mm])
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("BACKGROUND", (2, 0), (2, 0), DEEP_GREEN),
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -1), 1.4, GOLD),
    ]))
    story.extend([header, Spacer(1, 7 * mm)])

    title_bar = Table([[Paragraph(title_text, styles["document_title"]), Paragraph(tr["paid"] if paid else tr["pending"], styles["status"])]], colWidths=[137 * mm, 43 * mm])
    title_bar.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), DEEP_GREEN),
        ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#EAF8F2") if paid else colors.HexColor("#FFF5D8")),
        ("BOX", (0, 0), (-1, -1), 0.8, DEEP_GREEN), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
    ]))
    story.extend([title_bar, Spacer(1, 5 * mm), _section_title(tr["details"], styles), Spacer(1, 1.5 * mm)])
    common_rows = [
        (tr["issued"], str(item.get("crossing_at") or "-").replace("T", " ")[:19]),
        (tr["post"], item.get("post_name")), (tr["inspector"], _inspector_name(item.get("inspector_name"), language)),
        (tr["driver"], item.get("driver_name")), (tr["passport"], payload.get("passport")),
        (tr["vehicle"], item.get("vehicle_plate")), (tr["model"], payload.get("vehicle_model")),
    ]
    story.extend([_field_table(common_rows, styles), Spacer(1, 4 * mm)])

    if kind == "invoice":
        story.extend([_section_title(tr["payments"], styles), Spacer(1, 1.5 * mm)])
        payment_rows = [[Paragraph("#", styles["value"]), Paragraph(tr["payment_name"], styles["value"]), Paragraph(tr["amount"], styles["value"])]]
        payments = payload.get("payments") if isinstance(payload.get("payments"), list) else []
        for index, payment in enumerate(payments, start=1):
            if not isinstance(payment, dict):
                continue
            payment_rows.append([Paragraph(str(index), styles["body"]), Paragraph(str(payment.get(f"title_{language}") or payment.get("title_uz") or payment.get("code") or "-"), styles["body"]), Paragraph(_money(payment.get("amount_uzs")), ParagraphStyle(f"amount-{index}", parent=styles["body"], alignment=TA_RIGHT))])
        payment_rows.append(["", Paragraph(tr["total"], styles["value"]), Paragraph(_money(payload.get("payment_total_uzs")), ParagraphStyle("total", parent=styles["value"], alignment=TA_RIGHT))])
        payment_table = Table(payment_rows, colWidths=[12 * mm, 118 * mm, 50 * mm], repeatRows=1)
        payment_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), LIGHT_GREEN), ("BACKGROUND", (0, -1), (-1, -1), LIGHT_GRAY),
            ("BOX", (0, 0), (-1, -1), 0.7, GREEN), ("INNERGRID", (0, 0), (-1, -2), 0.35, colors.HexColor("#D2DDD8")),
            ("LINEABOVE", (0, -1), (-1, -1), 0.8, GREEN), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(payment_table)
    elif kind == "commitment":
        transit_rows = [(tr["nationality"], payload.get("nationality")), (tr["country"], payload.get("vehicle_country")), (tr["trailer"], payload.get("trailer_plate")), (tr["cargo"], payload.get("cargo")), (tr["route"], payload.get("location"))]
        story.extend([_section_title(tr["obligations"], styles), Spacer(1, 1.5 * mm)])
        obligation_text = "<br/>".join(f"<b>{index}.</b> {text}" for index, text in enumerate(tr["obligation_text"], start=1))
        obligation_box = Table([[Paragraph(obligation_text, styles["body"])]], colWidths=[180 * mm])
        obligation_box.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#C9D7D1")), ("BACKGROUND", (0, 0), (-1, 0), LIGHT_GRAY),
            ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.extend([obligation_box, Spacer(1, 2 * mm), _field_table(transit_rows, styles)])
    else:
        payments = payload.get("payments") if isinstance(payload.get("payments"), list) else []
        osago_amount = next((p.get("amount_uzs") for p in payments if isinstance(p, dict) and p.get("code") == "osago-insurance"), 0)
        insurance_rows = [(tr["policy_holder"], item.get("driver_name")), (tr["passport"], payload.get("passport")), (tr["vehicle"], item.get("vehicle_plate")), (tr["model"], payload.get("vehicle_model")), (tr["country"], payload.get("vehicle_country")), (tr["premium"], _money(osago_amount)), (tr["coverage"], tr["coverage_value"])]
        story.extend([_section_title(tr["insurance_info"], styles), Spacer(1, 1.5 * mm), _field_table(insurance_rows, styles)])

    story.extend([Spacer(1, 4 * mm), _section_title(tr["verification"], styles), Spacer(1, 1.5 * mm)])
    verify = Table([[_qr_drawing(public_url), Paragraph(f"<b>{tr['scan']}</b><br/><br/>{public_url}<br/><br/><font color='#66756F'>{tr['electronic']}</font>", styles["body"])]], colWidths=[38 * mm, 142 * mm])
    verify.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#C9D7D1")), ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GRAY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9), ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.extend([verify, Spacer(1, 4 * mm)])
    signatures = Table([[Paragraph(f"______________________________<br/>{tr['signature']}", styles["center"]), Paragraph(f"______________________________<br/>{tr['seal']}", styles["center"])]], colWidths=[90 * mm, 90 * mm])
    story.append(signatures)

    footer = lambda canvas, doc: _page_footer(canvas, doc, regular, bold, tr)
    pdf.build(story, onFirstPage=footer, onLaterPages=footer)
    return buffer.getvalue()
