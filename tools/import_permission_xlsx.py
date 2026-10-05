from __future__ import annotations

import json
import sys
import time
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path


NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def col_index(cell_ref: str) -> int:
    letters = "".join(ch for ch in cell_ref if ch.isalpha())
    index = 0
    for char in letters:
        index = index * 26 + ord(char.upper()) - ord("A") + 1
    return index - 1


def read_shared(zf: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    return ["".join(node.text or "" for node in item.findall(".//m:t", NS)) for item in root.findall("m:si", NS)]


def cell_value(cell: ET.Element, shared: list[str]) -> str:
    value = cell.find("m:v", NS)
    if value is None:
        inline = cell.find(".//m:t", NS)
        return inline.text if inline is not None and inline.text else ""
    text = value.text or ""
    if cell.get("t") == "s" and text.isdigit():
        return shared[int(text)]
    return text


def rows_from_sheet(zf: zipfile.ZipFile, sheet_name: str, shared: list[str]) -> list[list[str]]:
    root = ET.fromstring(zf.read(sheet_name))
    rows: list[list[str]] = []
    for row in root.findall(".//m:row", NS):
        values: list[str] = []
        for cell in row.findall("m:c", NS):
            index = col_index(cell.get("r", "A1"))
            while len(values) <= index:
                values.append("")
            values[index] = cell_value(cell, shared)
        rows.append(values)
    return rows


def normalize_row(header: list[str], row: list[str]) -> dict[str, str]:
    return {key: row[index] if index < len(row) else "" for index, key in enumerate(header)}


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


def main() -> None:
    xlsx_path = Path(sys.argv[1])
    json_path = Path(sys.argv[2])
    data = json.loads(json_path.read_text(encoding="utf-8"))
    with zipfile.ZipFile(xlsx_path) as zf:
        shared = read_shared(zf)
        rows = rows_from_sheet(zf, "xl/worksheets/sheet1.xml", shared)

    header = rows[0]
    countries: dict[str, str] = {}
    rules: dict[str, dict[str, dict[str, str]]] = {}
    vid_types: dict[str, str] = dict(data.get("vid_types", {}))
    for raw in rows[1:]:
        row = normalize_row(header, raw)
        if row.get("ISDELETED") not in {"", "0", "(null)"}:
            continue
        code = row.get("COUNTRY_CD", "").zfill(3)
        vid = row.get("VID_CD", "")
        if not code or not vid:
            continue
        countries[code] = row.get("COUNTRY_NM", "")
        vid_types.setdefault(vid, row.get("VID_NM", ""))
        rule = {
            "vid_cd": vid,
            "vid_name_ru": row.get("VID_NM", ""),
            "permission_cd": row.get("PERMISSION_CD", ""),
            "permission_name_ru": row.get("PERMISSION_NM", ""),
            "exception_cd": row.get("EXCEPTION_CD", ""),
            "exception_name_ru": row.get("EXCEPTION_NM", ""),
            "dues_cd": row.get("DUES_CD", ""),
            "dues_name_ru": row.get("DUES_NM", ""),
            "dues_amount_usd": "",
            "dues_amount_note_uz": "",
            "dues_amount_note_ru": "",
            "dues_amount_note_en": "",
            "source": xlsx_path.name,
        }
        if rule["dues_cd"] == "1":
            rule["dues_amount_usd"] = default_dues_amount(code)
        rules.setdefault(code, {})[vid] = rule

    old_countries = data.get("countries", {})
    old_rules = data.get("rules", {})
    for code, name in old_countries.items():
        countries.setdefault(code, name)
    for code, country_rules in old_rules.items():
        if code not in rules:
            rules[code] = country_rules
            for rule in rules[code].values():
                if str(rule.get("dues_cd")) == "1" and not rule.get("dues_amount_usd"):
                    rule["dues_amount_usd"] = default_dues_amount(code)
            continue
        for vid, rule in country_rules.items():
            if vid not in rules[code]:
                rules[code][vid] = rule
                if str(rules[code][vid].get("dues_cd")) == "1" and not rules[code][vid].get("dues_amount_usd"):
                    rules[code][vid]["dues_amount_usd"] = default_dues_amount(code)
                continue
            for key in ("admin_note", "dues_amount_usd", "dues_amount_note_uz", "dues_amount_note_ru", "dues_amount_note_en"):
                if rule.get(key):
                    rules[code][vid][key] = rule[key]
            if str(rules[code][vid].get("dues_cd")) == "1" and not rules[code][vid].get("dues_amount_usd"):
                rules[code][vid]["dues_amount_usd"] = default_dues_amount(code)

    data["vid_types"] = vid_types
    data["countries"] = dict(sorted(countries.items()))
    data["rules"] = {code: dict(sorted(country_rules.items(), key=lambda item: int(item[0]))) for code, country_rules in sorted(rules.items())}
    data.setdefault("source", {})["permission"] = str(xlsx_path)
    data.setdefault("source", {})["last_permission_import"] = int(time.time())
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"imported countries={len(countries)} rules={sum(len(v) for v in rules.values())}")


if __name__ == "__main__":
    main()
