from __future__ import annotations

import sys
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter
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
    values: list[str] = []
    for item in root.findall("m:si", NS):
        values.append("".join(node.text or "" for node in item.findall(".//m:t", NS)))
    return values


def cell_value(cell: ET.Element, shared: list[str]) -> str:
    value = cell.find("m:v", NS)
    if value is None:
        inline = cell.find(".//m:t", NS)
        return inline.text if inline is not None and inline.text else ""
    text = value.text or ""
    if cell.get("t") == "s" and text.isdigit():
        return shared[int(text)]
    return text


def read_sheet(zf: zipfile.ZipFile, sheet_name: str, shared: list[str]) -> list[list[str]]:
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


def main() -> None:
    path = Path(sys.argv[1])
    with zipfile.ZipFile(path) as zf:
        shared = read_shared(zf)
        sheets = [name for name in zf.namelist() if name.startswith("xl/worksheets/sheet")]
        for sheet in sheets:
            rows = read_sheet(zf, sheet, shared)
            print(f"\nSHEET: {sheet} rows={len(rows)}")
            for row in rows[:12]:
                print(row)
            header = max(rows[:20], key=len, default=[])
            if header:
                print("HEADER_CANDIDATE:", header)
            flat = [value for row in rows for value in row if value]
            print("COMMON:", Counter(flat).most_common(15))


if __name__ == "__main__":
    main()
