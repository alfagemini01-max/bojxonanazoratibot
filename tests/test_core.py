from __future__ import annotations

import unittest
import ast
from pathlib import Path

from app.i18n import t
from app.services.fee_calculator import FeeCalculator
from app.services.permit import PermitRuleService


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


class AdminTemplateTests(unittest.TestCase):
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
        self.assertIn("E\\'lon qilinmagan", html)
        self.assertNotIn("?'➕ Qo'shiladi'", html)
if __name__ == "__main__":
    unittest.main()
