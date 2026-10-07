from __future__ import annotations

import argparse
import json
import time
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any

from app.services.permission_import import (
    _find_permission_sheet,
    _integer_text,
    _row_dict,
    _rule_from_row,
    _shared_strings,
    _sheet_rows,
)


EXCEPTION_COLUMNS = {
    "COUNTRY_CD",
    "COUNTRY_NM",
    "EXCEPTION_CD",
    "EXCEPTION_DESC",
    "EXCEPTION_FOR",
}


UZBEK_CYRILLIC_MARKERS = set("ўқғҳЎҚҒҲ")


def _source_language(text: str) -> str:
    return "uz" if any(character in UZBEK_CYRILLIC_MARKERS for character in text) else "ru"


def _active(row: dict[str, str]) -> bool:
    return _integer_text(row.get("ISDELETED", "")) in {"", "0", "(null)", "None"}


def _exception_rows(path: Path) -> list[dict[str, str]]:
    with zipfile.ZipFile(path) as archive:
        shared = _shared_strings(archive)
        sheet_paths = sorted(
            name
            for name in archive.namelist()
            if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")
        )
        for sheet_path in sheet_paths:
            rows = _sheet_rows(archive, sheet_path, shared)
            for index, row in enumerate(rows[:30]):
                header = [value.strip().upper() for value in row]
                if EXCEPTION_COLUMNS.issubset(set(header)):
                    return [_row_dict(header, item) for item in rows[index + 1 :]]
    raise ValueError("Istisnolar Excel faylida zarur ustunlar topilmadi.")


def sync_reference(
    permission_xlsx: Path,
    exception_xlsx: Path,
    current_json: Path,
    translations_json: Path,
    output_json: Path,
) -> dict[str, int]:
    current = json.loads(current_json.read_text(encoding="utf-8"))
    translations = (
        json.loads(translations_json.read_text(encoding="utf-8"))
        if translations_json.exists()
        else {}
    )

    with zipfile.ZipFile(permission_xlsx) as archive:
        shared = _shared_strings(archive)
        header, raw_rows = _find_permission_sheet(archive, shared)

    active_permission_rows: dict[tuple[str, str], dict[str, str]] = {}
    for raw_row in raw_rows:
        row = _row_dict(header, raw_row)
        if not _active(row):
            continue
        code = _integer_text(row.get("COUNTRY_CD", "")).zfill(3)
        vid = _integer_text(row.get("VID_CD", ""))
        if code.isdigit() and vid in {str(value) for value in range(1, 9)}:
            active_permission_rows[(code, vid)] = row

    countries: dict[str, str] = {}
    rules: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    old_rules = current.get("rules", {})
    source_name = permission_xlsx.name
    for (code, vid), row in sorted(active_permission_rows.items()):
        countries[code] = row.get("COUNTRY_NM", "").strip()
        rules[code][vid] = _rule_from_row(
            row,
            old_rules.get(code, {}).get(vid),
            source_name,
        )

    exception_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    active_exception_count = 0
    for row in _exception_rows(exception_xlsx):
        if not _active(row):
            continue
        code = _integer_text(row.get("COUNTRY_CD", "")).zfill(3)
        if not code.isdigit():
            continue
        source_text = row.get("EXCEPTION_DESC", "").strip()
        localized = translations.get(source_text, {})
        source_language = _source_language(source_text)
        item = {
            "exception_cd": _integer_text(row.get("EXCEPTION_CD", "")),
            "exception_desc": source_text,
            "source_language": source_language,
            "exception_for": _integer_text(row.get("EXCEPTION_FOR", "")).zfill(8),
            "source": exception_xlsx.name,
        }
        # Never label a source text as a translation. Language-specific keys are
        # emitted only for the source language or a reviewed translation.
        item[f"exception_desc_{source_language}"] = source_text
        for language in ("uz", "ru", "en"):
            translated = str(localized.get(language) or "").strip()
            if translated:
                item[f"exception_desc_{language}"] = translated
        exception_groups[code].append(item)
        active_exception_count += 1

    result = dict(current)
    result["countries"] = dict(sorted(countries.items()))
    result["rules"] = {
        code: dict(sorted(country_rules.items(), key=lambda item: int(item[0])))
        for code, country_rules in sorted(rules.items())
    }
    result["exceptions"] = {
        code: rows for code, rows in sorted(exception_groups.items())
    }
    result["source"] = {
        "permission": permission_xlsx.name,
        "exceptions": exception_xlsx.name,
        "note": "Full active permission and exception reference tables supplied on 2026-10-07.",
        "dataset_revision": "2026-10-07-full-permission-v1",
        "last_permission_import": int(time.time()),
    }
    result["metadata"] = {
        "country_count": len(countries),
        "rule_count": len(active_permission_rows),
        "exception_country_count": len(exception_groups),
        "exception_count": active_exception_count,
        "languages": ["uz", "ru", "en"],
    }
    output_json.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return {
        "countries": len(countries),
        "rules": len(active_permission_rows),
        "exception_countries": len(exception_groups),
        "exceptions": active_exception_count,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("permission_xlsx", type=Path)
    parser.add_argument("exception_xlsx", type=Path)
    parser.add_argument("--current", type=Path, default=Path("data/permission_rules.json"))
    parser.add_argument(
        "--translations",
        type=Path,
        default=Path("data/exception_translations.json"),
    )
    parser.add_argument("--output", type=Path, default=Path("data/permission_rules.json"))
    args = parser.parse_args()
    summary = sync_reference(
        args.permission_xlsx,
        args.exception_xlsx,
        args.current,
        args.translations,
        args.output,
    )
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
