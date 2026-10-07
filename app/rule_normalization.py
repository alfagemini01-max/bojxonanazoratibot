from __future__ import annotations

from typing import Any


PERMISSION_NAMES = {
    "1": "Обязательно",
    "2": "Не обязательно",
    "3": "Запрещен",
}

DUES_NAMES = {
    "0": "-не выбрано-",
    "1": "Сбор обязательно",
    "2": "Сбор не обязательно",
    "3": "Сбор зависит от вида разрешения",
}

EXCEPTION_NAMES = {
    "0": "-не выбрано-",
    "1": "Недоступен",
    "2": "Перечень в соответствии Соглашения",
}


def repair_broken_rule_labels(permission_data: dict[str, Any]) -> int:
    """Normalize derived Russian labels without changing legal rule codes."""
    changed_rules = 0
    for country_rules in permission_data.get("rules", {}).values():
        if not isinstance(country_rules, dict):
            continue
        for rule in country_rules.values():
            if not isinstance(rule, dict):
                continue
            changed = False
            canonical = {
                "permission_name_ru": PERMISSION_NAMES.get(str(rule.get("permission_cd") or "")),
                "dues_name_ru": DUES_NAMES.get(str(rule.get("dues_cd") or "")),
                "exception_name_ru": EXCEPTION_NAMES.get(str(rule.get("exception_cd") or "")),
            }
            for field, value in canonical.items():
                if value is not None and rule.get(field) != value:
                    rule[field] = value
                    changed = True
            if changed:
                changed_rules += 1
    return changed_rules
