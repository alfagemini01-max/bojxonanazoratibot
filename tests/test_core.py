from __future__ import annotations

import unittest
import ast
import re
from pathlib import Path

from app.i18n import t
from app.services.fee_calculator import FeeCalculator
from app.services.permit import (
    Country,
    PermitResult,
    PermitRuleService,
    build_permit_message,
    country_label,
    localized_additional_conditions,
)


ROOT = Path(__file__).resolve().parents[1]


class PermitRulesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.service = PermitRuleService(ROOT / "data" / "permission_rules.json")

    def test_typo_country_search_returns_kazakhstan(self) -> None:
        matches = self.service.search_countries("Qozogstan", threshold=0.6)
        self.assertTrue(matches)
        self.assertEqual(matches[0].country.code, "398")

    def test_transport_types(self) -> None:
        uzbekistan = self.service.country_by_code("860")
        china = self.service.country_by_code("156")
        kazakhstan = self.service.country_by_code("398")
        russia = self.service.country_by_code("643")
        self.assertEqual(self.service.detect_transport_type(china, uzbekistan, china), "2")
        self.assertEqual(self.service.detect_transport_type(china, uzbekistan, kazakhstan), "5")
        self.assertEqual(self.service.detect_transport_type(russia, china, kazakhstan), "3")

    def test_empty_transport_types(self) -> None:
        uzbekistan = self.service.country_by_code("860")
        china = self.service.country_by_code("156")
        self.assertEqual(self.service.detect_transport_type(china, uzbekistan, china, "empty_entry"), "7")
        self.assertEqual(self.service.detect_transport_type(china, uzbekistan, china, "empty_transit"), "8")

    def test_country_input_profile_comes_from_rules(self) -> None:
        self.assertEqual(
            self.service.country_input_profile("762"),
            {"uses_weight": True, "uses_stay_days": False},
        )
        self.assertEqual(
            self.service.country_input_profile("031"),
            {"uses_weight": False, "uses_stay_days": True},
        )
        self.assertEqual(
            self.service.country_input_profile("036"),
            {"uses_weight": False, "uses_stay_days": False},
        )

    def test_country_names_follow_language(self) -> None:
        australia = self.service.country_by_code("036")
        self.assertEqual(country_label(australia, "uz"), "Avstraliya")
        self.assertEqual(country_label(australia, "ru"), "Австралия")
        self.assertEqual(country_label(australia, "en"), "Australia")
        unknown = self.service.country_by_code("000")
        self.assertEqual(country_label(unknown, "uz"), "Noma'lum davlat")

    def test_unknown_country_entry_and_transit_use_400_usd(self) -> None:
        calculator = FeeCalculator(ROOT / "data" / "fees_2026.json", 412000, 12600)
        for origin_code, destination_code, operation in (
            ("156", "860", "cargo"),
            ("156", "643", "cargo"),
            ("156", "860", "empty_entry"),
        ):
            result = self.service.evaluate(
                self.service.country_by_code(origin_code),
                self.service.country_by_code(destination_code),
                self.service.country_by_code("000"),
                operation,
            )
            self.assertEqual(
                calculator.entry_fee_usd_for_rule(result.rule or {}, "000", "up_to_10", "up_to_14"),
                400.0,
            )

    def test_new_fee_mode_is_translated(self) -> None:
        for lang in ("uz", "ru", "en"):
            self.assertNotEqual(t(lang, "ask_fee_mode"), "ask_fee_mode")
            self.assertNotEqual(t(lang, "button_fee_quick"), "button_fee_quick")

    def test_quick_fee_still_includes_transit_declaration(self) -> None:
        calculator = FeeCalculator(ROOT / "data" / "fees_2026.json", 412000, 12600)
        message = calculator.build_message(
            {
                "vehicle_type": "truck",
                "vehicle_country_code": "156",
                "direction": "entry",
                "origin_country_code": "156",
                "destination_country_code": "860",
                "calculation_mode": "quick",
            },
            self.service,
            lang="uz",
        )
        self.assertIn("Tranzit deklaratsiyasi", message)
        self.assertIn("Tezkor hisob", message)

    def test_additional_conditions_use_language_and_fallback(self) -> None:
        rule = {
            "additional_conditions": [
                {"enabled": True, "uz": "O'zbekcha shart", "ru": "Русское условие", "en": "English condition"},
                {"enabled": True, "uz": "Faqat o'zbekcha"},
                {"enabled": False, "uz": "Ko'rinmasligi kerak"},
            ]
        }
        self.assertEqual(
            localized_additional_conditions(rule, "ru"),
            ["Русское условие", "Faqat o'zbekcha"],
        )

    def test_additional_condition_is_in_telegram_message(self) -> None:
        result = PermitResult(
            origin=Country("156", "Xitoy"),
            destination=Country("860", "O'zbekiston"),
            vehicle_country=Country("156", "Xitoy"),
            vid_cd="2",
            vid_name="Ikki tomonlama",
            rule={
                "permission_cd": "1",
                "dues_cd": "2",
                "additional_conditions": [{"enabled": True, "uz": "Maxsus ikki tomonlama shart"}],
            },
            fee_text="",
            fee_note="",
            exceptions=[],
        )
        self.assertIn("Maxsus ikki tomonlama shart", build_permit_message(result, lang="uz"))


class AdminTemplateTests(unittest.TestCase):
    def test_simple_admin_assets_and_condition_editor_exist(self) -> None:
        html = (ROOT / "app" / "static" / "admin.html").read_text(encoding="utf-8")
        login = (ROOT / "app" / "static" / "admin-login.html").read_text(encoding="utf-8")
        script = (ROOT / "app" / "static" / "admin.js").read_text(encoding="utf-8")
        self.assertIn('id="transport-tabs"', html)
        self.assertIn('id="condition-list"', html)
        self.assertIn("additional_conditions", script)
        self.assertNotIn("Raw JSON", html)
        self.assertIn("uzbekistan-emblem.png", login)

    def test_rendered_javascript_preserves_apostrophe_escapes(self) -> None:
        tree = ast.parse((ROOT / "app" / "admin_panel.py").read_text(encoding="utf-8"))
        page_function = next(
            node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_admin_page_v2"
        )
        html = next(
            node.value.value
            for node in ast.walk(page_function)
            if isinstance(node, ast.Return)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        )
        self.assertIn("Qo\\'shiladi", html)
        self.assertIn("Avtomatik faol", html)
        self.assertNotIn('onclick="publishDraft()"', html)
        self.assertNotIn('onclick="discardDraft()"', html)
        self.assertNotIn("?'➕ Qo'shiladi'", html)


class WebAppAssetTests(unittest.TestCase):
    def test_country_flags_are_local_and_complete(self) -> None:
        webapp_source = (ROOT / "app" / "webapp.py").read_text(encoding="utf-8")
        mapped_codes = set(re.findall(r"(?<!\d)(\d{3}):([A-Z]{2})", webapp_source))
        alpha2 = {code: iso.lower() for code, iso in mapped_codes}
        permission = __import__("json").loads(
            (ROOT / "data" / "permission_rules.json").read_text(encoding="utf-8")
        )
        missing = [
            code for code in permission["countries"]
            if code != "000" and not (ROOT / "app" / "static" / "flags" / f"{alpha2.get(code, '')}.svg").exists()
        ]
        self.assertEqual(missing, [])

    def test_webapp_uses_svg_icons_and_local_flags(self) -> None:
        html = (ROOT / "app" / "static" / "webapp.html").read_text(encoding="utf-8")
        script = (ROOT / "app" / "static" / "webapp.js").read_text(encoding="utf-8")
        self.assertIn('id="icon-file-check"', html)
        self.assertIn('/static/webapp/flags/${code}.svg', script)
        self.assertNotIn("flagcdn.com", script)
        self.assertIn("loading=\"eager\"", script)
        self.assertIn("permit-operation", html)
        self.assertIn('data-operation="cargo"', html)
        self.assertNotIn('data-operation="cargo_entry"', html)
        self.assertIn("country_input_profile", (ROOT / "app" / "webapp.py").read_text(encoding="utf-8"))

    def test_admin_can_manage_transport_types(self) -> None:
        html = (ROOT / "app" / "static" / "admin.html").read_text(encoding="utf-8")
        script = (ROOT / "app" / "static" / "admin.js").read_text(encoding="utf-8")
        backend = (ROOT / "app" / "admin_panel.py").read_text(encoding="utf-8")
        self.assertIn("manage-transport-types", html)
        self.assertIn("openTransportTypes", script)
        self.assertIn("/admin/api/transport-type", backend)
if __name__ == "__main__":
    unittest.main()
