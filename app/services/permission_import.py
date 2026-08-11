from __future__ import annotations

import json
import time
import zipfile
import xml.etree.ElementTree as ET
from collections.abc import Callable
from pathlib import Path
from typing import Any


NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REQUIRED_COLUMNS = {
    "COUNTRY_CD",
    "COUNTRY_NM",
    "VID_CD",
    "VID_NM",
    "PERMISSION_CD",
    "PERMISSION_NM",
    "DUES_CD",
    "DUES_NM",
}
MAX_UNCOMPRESSED_BYTES = 50 * 1024 * 1024
MAX_ROWS = 100_000
RULE_SOURCE_FIELDS = (
    "vid_cd",
    "vid_name_ru",
    "permission_cd",
    "permission_name_ru",
    "exception_cd",
    "exception_name_ru",
    "dues_cd",
    "dues_name_ru",
    "dues_amount_usd",
)
PRESERVED_FIELDS = (
    "admin_note",
    "dues_amount_note_uz",
    "dues_amount_note_ru",
    "dues_amount_note_en",
)


class PermissionImportError(ValueError):
    pass


def default_dues_amount(country_code: str) -> str:
    if country_code == "364":
        return "0"
    if country_code == "004":
        return "50"
    if country_code in {"398", "417"}:
        return "300"
    if country_code == "762":
        return "100/150/200"
    if country_code == "795":
        return "130/180/250"
    if country_code in {
        "031", "040", "056", "100", "191", "196", "203", "208", "233", "246",
        "250", "276", "300", "348", "372", "380", "428", "440", "442", "470",
        "528", "616", "620", "642", "703", "705", "724", "752",
    }:
        return "80/280"
    return "400"


def _progress(callback: Callable[[int, str], None] | None, percent: int, message: str) -> None:
    if callback:
        callback(max(0, min(100, percent)), message)


def _column_index(cell_ref: str) -> int:
    letters = "".join(ch for ch in cell_ref if ch.isalpha())
    index = 0
    for char in letters:
        index = index * 26 + ord(char.upper()) - ord("A") + 1
    return index - 1


def _shared_strings(archive: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    return ["".join(node.text or "" for node in item.findall(".//m:t", NS)) for item in root.findall("m:si", NS)]


def _cell_value(cell: ET.Element, shared: list[str]) -> str:
    value = cell.find("m:v", NS)
    if value is None:
        inline = cell.find(".//m:t", NS)
        return inline.text if inline is not None and inline.text else ""
    text = value.text or ""
    if cell.get("t") == "s" and text.isdigit():
        index = int(text)
        return shared[index] if index < len(shared) else ""
    return text


def _sheet_rows(archive: zipfile.ZipFile, sheet_path: str, shared: list[str]) -> list[list[str]]:
    root = ET.fromstring(archive.read(sheet_path))
    rows: list[list[str]] = []
    for row in root.findall(".//m:row", NS):
        values: list[str] = []
        for cell in row.findall("m:c", NS):
            index = _column_index(cell.get("r", "A1"))
            while len(values) <= index:
                values.append("")
            values[index] = _cell_value(cell, shared).strip()
        rows.append(values)
        if len(rows) > MAX_ROWS:
            raise PermissionImportError("Excel faylida ruxsat etilganidan ko'p satr mavjud.")
    return rows


def _find_permission_sheet(archive: zipfile.ZipFile, shared: list[str]) -> tuple[list[str], list[list[str]]]:
    sheet_paths = sorted(
        name for name in archive.namelist()
        if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")
    )
    for sheet_path in sheet_paths:
        rows = _sheet_rows(archive, sheet_path, shared)
        for index, row in enumerate(rows[:30]):
            header = [value.strip().upper() for value in row]
            if REQUIRED_COLUMNS.issubset(set(header)):
                return header, rows[index + 1 :]
    raise PermissionImportError(
        "Excelda COUNTRY_CD, COUNTRY_NM, VID_CD, PERMISSION_CD va DUES_CD ustunlari topilmadi."
    )


def _row_dict(header: list[str], row: list[str]) -> dict[str, str]:
    return {name: row[index].strip() if index < len(row) else "" for index, name in enumerate(header)}


def _integer_text(value: object) -> str:
    text = str(value or "").strip()
    if "." in text:
        whole, fraction = text.split(".", 1)
        if whole.isdigit() and fraction and set(fraction) == {"0"}:
            return whole
    return text


def _rule_from_row(row: dict[str, str], old_rule: dict[str, Any] | None, source_name: str) -> dict[str, str]:
    country_code = _integer_text(row["COUNTRY_CD"]).zfill(3)
    dues_cd = _integer_text(row.get("DUES_CD", ""))
    old_rule = old_rule or {}
    amount = ""
    if dues_cd == "1":
        amount = str(old_rule.get("dues_amount_usd") or default_dues_amount(country_code))
    rule = {
        "vid_cd": _integer_text(row.get("VID_CD", "")),
        "vid_name_ru": row.get("VID_NM", ""),
        "permission_cd": _integer_text(row.get("PERMISSION_CD", "")),
        "permission_name_ru": row.get("PERMISSION_NM", ""),
        "exception_cd": _integer_text(row.get("EXCEPTION_CD", "")),
        "exception_name_ru": row.get("EXCEPTION_NM", ""),
        "dues_cd": dues_cd,
        "dues_name_ru": row.get("DUES_NM", ""),
        "dues_amount_usd": amount,
        "dues_amount_note_uz": "",
        "dues_amount_note_ru": "",
        "dues_amount_note_en": "",
        "source": source_name,
    }
    for field in PRESERVED_FIELDS:
        if old_rule.get(field):
            rule[field] = str(old_rule[field])
    return rule


def _rule_view(rule: dict[str, Any] | None) -> dict[str, str]:
    rule = rule or {}
    return {field: str(rule.get(field) or "") for field in RULE_SOURCE_FIELDS + PRESERVED_FIELDS}


def build_permission_import_preview(
    xlsx_path: Path,
    current_rules_path: Path,
    source_name: str,
    progress_callback: Callable[[int, str], None] | None = None,
) -> dict[str, Any]:
    _progress(progress_callback, 3, "Excel fayli tekshirilmoqda")
    try:
        with zipfile.ZipFile(xlsx_path) as archive:
            total_size = sum(item.file_size for item in archive.infolist())
            if total_size > MAX_UNCOMPRESSED_BYTES:
                raise PermissionImportError("Excel faylining ochilgan hajmi 50 MB dan oshmasligi kerak.")
            shared = _shared_strings(archive)
            _progress(progress_callback, 12, "Excel varaqlari aniqlanmoqda")
            header, raw_rows = _find_permission_sheet(archive, shared)
    except zipfile.BadZipFile as exc:
        raise PermissionImportError("Tanlangan fayl haqiqiy .xlsx fayli emas.") from exc

    current = json.loads(current_rules_path.read_text(encoding="utf-8"))
    old_countries: dict[str, str] = current.get("countries", {})
    old_rules: dict[str, dict[str, dict[str, Any]]] = current.get("rules", {})
    active_rows: dict[tuple[str, str], dict[str, str]] = {}
    deleted_rows: dict[tuple[str, str], dict[str, str]] = {}
    invalid_rows = 0
    duplicates = 0

    total_rows = max(1, len(raw_rows))
    for index, raw_row in enumerate(raw_rows):
        row = _row_dict(header, raw_row)
        code = _integer_text(row.get("COUNTRY_CD", "")).zfill(3)
        vid = _integer_text(row.get("VID_CD", ""))
        if not code.isdigit() or vid not in {str(value) for value in range(1, 9)}:
            invalid_rows += 1
            continue
        key = (code, vid)
        deleted = _integer_text(row.get("ISDELETED", "")) not in {"", "0", "(null)"}
        target = deleted_rows if deleted else active_rows
        if key in target:
            duplicates += 1
        target[key] = row
        if index % 25 == 0:
            _progress(progress_callback, 15 + int((index / total_rows) * 45), "Excel satrlari o'qilmoqda")

    changes: list[dict[str, Any]] = []
    seen_countries: set[str] = set()
    unchanged_rules = 0
    for index, ((code, vid), row) in enumerate(active_rows.items()):
        country_name = row.get("COUNTRY_NM", "").strip()
        if code not in seen_countries:
            old_name = str(old_countries.get(code) or "")
            if not old_name:
                changes.append({
                    "id": f"country:{code}", "kind": "country", "action": "add", "selected": True,
                    "country_code": code, "country_name": country_name,
                    "before": {"name": ""}, "after": {"name": country_name},
                })
            elif country_name and old_name != country_name:
                changes.append({
                    "id": f"country:{code}", "kind": "country", "action": "update", "selected": True,
                    "country_code": code, "country_name": country_name,
                    "before": {"name": old_name}, "after": {"name": country_name},
                })
            seen_countries.add(code)

        old_rule = old_rules.get(code, {}).get(vid)
        new_rule = _rule_from_row(row, old_rule, source_name)
        before = _rule_view(old_rule)
        after = _rule_view(new_rule)
        if old_rule and before == after:
            unchanged_rules += 1
        else:
            changed_fields = [field for field in RULE_SOURCE_FIELDS if before.get(field) != after.get(field)]
            changes.append({
                "id": f"rule:{code}:{vid}", "kind": "rule", "action": "update" if old_rule else "add",
                "selected": True, "country_code": code, "country_name": country_name, "vid_cd": vid,
                "vid_name": row.get("VID_NM", ""), "changed_fields": changed_fields,
                "before": before, "after": {**new_rule},
            })
        if index % 25 == 0:
            _progress(progress_callback, 62 + int((index / max(1, len(active_rows))) * 28), "Qoidalar taqqoslanmoqda")

    for (code, vid), row in deleted_rows.items():
        if (code, vid) in active_rows:
            continue
        old_rule = old_rules.get(code, {}).get(vid)
        if not old_rule:
            continue
        changes.append({
            "id": f"delete-rule:{code}:{vid}", "kind": "rule", "action": "delete", "selected": False,
            "country_code": code, "country_name": row.get("COUNTRY_NM", ""), "vid_cd": vid,
            "vid_name": row.get("VID_NM", ""), "changed_fields": ["ISDELETED"],
            "before": _rule_view(old_rule), "after": {},
        })

    action_counts = {
        action: sum(1 for change in changes if change["action"] == action)
        for action in ("add", "update", "delete")
    }
    _progress(progress_callback, 100, "Taqqoslash yakunlandi")
    return {
        "changes": changes,
        "summary": {
            "excel_rows": len(raw_rows),
            "active_rules": len(active_rows),
            "deleted_rows": len(deleted_rows),
            "countries": len({code for code, _ in active_rows}),
            "unchanged_rules": unchanged_rules,
            "invalid_rows": invalid_rows,
            "duplicates": duplicates,
            **action_counts,
        },
    }


def apply_permission_import_changes(
    data: dict[str, Any],
    original_changes: list[dict[str, Any]],
    submitted_changes: list[dict[str, Any]],
    source_name: str,
) -> int:
    originals = {str(change.get("id")): change for change in original_changes}
    applied = 0
    for submitted in submitted_changes:
        change_id = str(submitted.get("id") or "")
        original = originals.get(change_id)
        if not original:
            raise PermissionImportError(f"Noma'lum o'zgarish: {change_id}")
        code = str(original.get("country_code") or "").zfill(3)
        action = str(original.get("action") or "")
        kind = str(original.get("kind") or "")
        edited_after = submitted.get("after") if isinstance(submitted.get("after"), dict) else {}

        if kind == "country":
            name = str(edited_after.get("name") or original.get("after", {}).get("name") or "").strip()
            if len(name) < 2:
                raise PermissionImportError(f"{code} davlat nomi bo'sh bo'lishi mumkin emas.")
            data.setdefault("countries", {})[code] = name
            data.setdefault("rules", {}).setdefault(code, {})
        elif kind == "rule" and action == "delete":
            vid = str(original.get("vid_cd") or "")
            data.setdefault("rules", {}).setdefault(code, {}).pop(vid, None)
        elif kind == "rule":
            vid = str(original.get("vid_cd") or "")
            if vid not in {str(value) for value in range(1, 9)}:
                raise PermissionImportError("Tashuv turi 1-8 oralig'ida bo'lishi kerak.")
            after = dict(original.get("after") or {})
            for field in RULE_SOURCE_FIELDS + PRESERVED_FIELDS:
                if field in edited_after:
                    after[field] = str(edited_after[field] or "").strip()
            if after.get("permission_cd") not in {"1", "2", "3"}:
                raise PermissionImportError(f"{code}/{vid}: ruxsatnoma holati noto'g'ri.")
            if after.get("dues_cd") not in {"0", "1", "2", "3"}:
                raise PermissionImportError(f"{code}/{vid}: yig'im holati noto'g'ri.")
            if after.get("dues_cd") != "1":
                after["dues_amount_usd"] = ""
            after["vid_cd"] = vid
            after["source"] = source_name
            if code not in data.setdefault("countries", {}):
                raise PermissionImportError(
                    f"{code} davlati bazada yo'q. Avval ushbu davlatni qo'shish o'zgarishini ham tanlang."
                )
            data.setdefault("rules", {}).setdefault(code, {})[vid] = after
            data.setdefault("vid_types", {}).setdefault(vid, after.get("vid_name_ru", ""))
        else:
            raise PermissionImportError(f"Qo'llab bo'lmaydigan o'zgarish: {change_id}")
        applied += 1

    data["countries"] = dict(sorted(data.get("countries", {}).items()))
    data["rules"] = {
        code: dict(sorted(rules.items(), key=lambda item: int(item[0])))
        for code, rules in sorted(data.get("rules", {}).items())
    }
    data.setdefault("source", {})["permission"] = source_name
    data.setdefault("source", {})["last_permission_import"] = int(time.time())
    return applied
