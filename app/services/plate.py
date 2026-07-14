from __future__ import annotations

import re


_KEEP_PLATE_CHARS = re.compile(r"[^0-9A-Z]")


def normalize_plate(value: str) -> str:
    """Normalize plate text for lookup: uppercase, without spaces and symbols."""
    return _KEEP_PLATE_CHARS.sub("", value.upper())


def looks_like_plate(value: str) -> bool:
    plate = normalize_plate(value)
    return 4 <= len(plate) <= 12
