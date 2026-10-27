from __future__ import annotations

import io
from pathlib import Path
from typing import Any

from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


STATIC_DIR = Path(__file__).resolve().parents[1] / "static"
PAGE_WIDTH = 72 * mm
PAGE_HEIGHT = 205 * mm
LANGUAGES = {"uz", "ru", "en"}


def _register_fonts() -> tuple[str, str]:
    """Use the bundled Unicode fonts on every deployment."""
    font_dir = STATIC_DIR / "fonts"
    regular_name = "ReceiptUbuntu"
    bold_name = "ReceiptUbuntuBold"
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


def _gray_emblem() -> io.BytesIO | None:
    path = STATIC_DIR / "customs-emblem.png"
    if not path.exists():
        return None
    try:
        from PIL import Image as PillowImage

        output = io.BytesIO()
        with PillowImage.open(path) as source:
            source.convert("L").save(output, format="PNG", optimize=True)
        output.seek(0)
        return output
    except Exception:
        return None


def _qr_drawing(value: str, size: float = 37 * mm) -> Drawing:
    widget = QrCodeWidget(value, barLevel="H")
    bounds = widget.getBounds()
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    drawing = Drawing(size, size, transform=[size / width, 0, 0, size / height, 0, 0])
    drawing.add(widget)
    return drawing


def _document_title(doc: dict[str, Any], lang: str) -> str:
    explicit = str(doc.get(f"title_{lang}") or "").strip()
    return explicit or str(doc.get("title") or doc.get("code") or "Hujjat").strip()


def build_inspector_document_pdf(
    item: dict[str, Any],
    *,
    public_url: str,
    document_index: int = 0,
    language: str = "uz",
) -> bytes:
    """Build a compact monochrome thermal-receipt PDF for direct download."""
    language = language if language in LANGUAGES else "uz"
    regular, bold = _register_fonts()
    payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}
    documents = payload.get("documents") if isinstance(payload.get("documents"), list) else []
    if documents:
        document_index = min(max(int(document_index), 0), len(documents) - 1)
        selected_document = documents[document_index] if isinstance(documents[document_index], dict) else {}
    else:
        selected_document = {"code": item.get("document_no"), "title": "Bojxona hujjati"}

    buffer = io.BytesIO()
    pdf = SimpleDocTemplate(
        buffer,
        pagesize=(PAGE_WIDTH, PAGE_HEIGHT),
        leftMargin=4.5 * mm,
        rightMargin=4.5 * mm,
        topMargin=4 * mm,
        bottomMargin=4 * mm,
        title=f"{item.get('document_no', '')} — Bojxona kvitansiyasi",
        author="Bojxona nazorati axborot tizimi",
        subject="QR-kodli elektron nazorat kvitansiyasi",
    )

    base = ParagraphStyle(
        "receipt",
        fontName=regular,
        fontSize=6.7,
        leading=8.3,
        textColor=colors.black,
        spaceAfter=0,
    )
    centered = ParagraphStyle("receipt-center", parent=base, alignment=TA_CENTER)
    title = ParagraphStyle("receipt-title", parent=centered, fontName=bold, fontSize=9.2, leading=10.5)
    small = ParagraphStyle("receipt-small", parent=centered, fontSize=5.8, leading=7)
    notice = ParagraphStyle("receipt-notice", parent=base, fontSize=6.1, leading=7.6)
    story: list[Any] = []

    emblem = _gray_emblem()
    if emblem:
        story.append(Image(emblem, width=15 * mm, height=15 * mm, hAlign="CENTER"))
        story.append(Spacer(1, 1.2 * mm))
    story.extend(
        [
            Paragraph("O‘ZBEKISTON RESPUBLIKASI<br/>DAVLAT BOJXONA XIZMATI", title),
            Spacer(1, 1.3 * mm),
            Paragraph("ELEKTRON NAZORAT KVITANSIYASI", ParagraphStyle("receipt-subtitle", parent=centered, fontName=bold, fontSize=7.1, leading=8.5)),
            Spacer(1, 1.5 * mm),
            Table([[Paragraph(str(item.get("document_no") or "—"), ParagraphStyle("receipt-number", parent=centered, fontName=bold, fontSize=7.2))]], colWidths=[63 * mm], style=TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.8, colors.black),
                ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
            ])),
            Spacer(1, 2 * mm),
        ]
    )

    meta_rows = [
        ("Sana / Date", str(item.get("crossing_at") or "—").replace("T", " ")[:19]),
        ("Punkt / Post", str(item.get("post_name") or "—")),
        ("T/r vositasi / Vehicle", str(item.get("vehicle_plate") or "—")),
        ("Haydovchi / Driver", str(item.get("driver_name") or "—")),
    ]
    meta_table = Table(
        [[Paragraph(label, base), Paragraph(value, ParagraphStyle("receipt-value", parent=base, fontName=bold, alignment=2))] for label, value in meta_rows],
        colWidths=[24 * mm, 39 * mm],
        style=TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#888888")),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]),
    )
    story.extend([meta_table, Spacer(1, 2 * mm)])

    doc_code = str(selected_document.get("code") or item.get("document_no") or "DOC")
    story.append(Paragraph("YUKLAB OLINAYOTGAN HUJJAT", ParagraphStyle("section", parent=centered, fontName=bold, fontSize=6.3)))
    story.append(Paragraph(f"{doc_code} — {_document_title(selected_document, language)}", ParagraphStyle("selected-document", parent=centered, fontName=bold, fontSize=7, leading=8.4)))
    story.append(Spacer(1, 2 * mm))

    payments = payload.get("payments") if isinstance(payload.get("payments"), list) else []
    payment_rows = [[Paragraph("AVTOMATIK HISOBLANGAN TO‘LOVLAR", ParagraphStyle("payment-head", parent=base, fontName=bold)), ""]]
    for index, payment in enumerate(payments, start=1):
        if not isinstance(payment, dict):
            continue
        payment_rows.append([
            Paragraph(f"{index}. {payment.get(f'title_{language}') or payment.get('title_uz') or payment.get('code') or 'Yig‘im'}", base),
            Paragraph(_money(payment.get("amount_uzs")), ParagraphStyle("money", parent=base, fontName=bold, alignment=2)),
        ])
    payment_rows.append([
        Paragraph("JAMI / TOTAL", ParagraphStyle("total-label", parent=base, fontName=bold)),
        Paragraph(_money(payload.get("payment_total_uzs")), ParagraphStyle("total-value", parent=base, fontName=bold, alignment=2)),
    ])
    payments_table = Table(payment_rows, colWidths=[41 * mm, 22 * mm], repeatRows=1)
    payments_table.setStyle(TableStyle([
        ("SPAN", (0, 0), (1, 0)),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("BOX", (0, 0), (-1, -1), 0.7, colors.black),
        ("LINEBELOW", (0, 0), (-1, 0), 0.7, colors.black),
        ("LINEABOVE", (0, -1), (-1, -1), 0.7, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2.2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2.2),
        ("TOPPADDING", (0, 0), (-1, -1), 2.1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.1),
    ]))
    story.extend([payments_table, Spacer(1, 2 * mm)])

    person = str(item.get("driver_name") or "tashrif buyuruvchi")
    day = str(item.get("crossing_at") or "shu sana").replace("T", " ")[:16]
    post = str(item.get("post_name") or "bojxona posti")
    notices = [
        ("UZ", f"Hurmatli <b>{person}</b>! Siz {day} kuni {post} orqali chegarani kesib o‘tdingiz. To‘liq ma’lumot va hujjatlaringizni olish uchun QR-kodni skanerlang."),
        ("RU", f"Уважаемый(ая) <b>{person}</b>! Вы пересекли границу {day} через пункт {post}. Отсканируйте QR-код, чтобы получить полную информацию и документы."),
        ("EN", f"Dear <b>{person}</b>! You crossed the border on {day} through {post}. Scan the QR code to view full details and download your documents."),
    ]
    notice_rows = []
    for code, message in notices:
        notice_rows.append([
            Paragraph(code, ParagraphStyle(f"lang-{code}", parent=centered, fontName=bold, fontSize=6.4, textColor=colors.white)),
            Paragraph(message, notice),
        ])
    notice_table = Table(notice_rows, colWidths=[8 * mm, 55 * mm])
    notice_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#777777")),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 2.6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.6),
    ]))
    story.extend([notice_table, Spacer(1, 2 * mm)])

    qr_block = KeepTogether([
        _qr_drawing(public_url),
        Spacer(1, 0.8 * mm),
        Paragraph("QR-KODNI SKANERLANG / SCAN QR CODE", ParagraphStyle("qr-label", parent=centered, fontName=bold, fontSize=6.2)),
        Paragraph(public_url, ParagraphStyle("qr-url", parent=small, fontSize=4.7, leading=5.6)),
    ])
    story.extend([qr_block, Spacer(1, 1.5 * mm)])
    story.append(Paragraph("O‘zbekiston Respublikasi qonunchiligi talablariga rioya qiling.", ParagraphStyle("footer", parent=centered, fontName=bold, fontSize=5.5, leading=6.8)))

    pdf.build(story)
    return buffer.getvalue()

