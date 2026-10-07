from __future__ import annotations

import unittest
import ast
import re
from pathlib import Path

from app.i18n import t
from app.rule_normalization import repair_broken_rule_labels
from app.services.fee_calculator import FeeCalculator
from app.services.permit import (
    Country,
    PermitResult,
    PermitRuleService,
    build_permit_message,
    country_label,
    localized_additional_conditions,
    turkmenistan_extra_fee_applies,
)


ROOT = Path(__file__).resolve().parents[1]


class RuleDataMigrationTests(unittest.TestCase):
    def test_broken_derived_labels_are_repaired_from_codes(self) -> None:
        permission = {
            "rules": {
                "398": {
                    "3": {
                        "permission_cd": "2",
                        "permission_name_ru": "????",
                        "exception_cd": "2",
                        "exception_name_ru": "????????",
                        "dues_cd": "1",
                        "dues_name_ru": "????",
                    }
                }
            }
        }
        self.assertEqual(repair_broken_rule_labels(permission), 1)
        rule = permission["rules"]["398"]["3"]
        self.assertEqual(rule["permission_name_ru"], "Не обязательно")
        self.assertEqual(rule["exception_name_ru"], "Перечень в соответствии Соглашения")
        self.assertEqual(rule["dues_name_ru"], "Сбор обязательно")
        self.assertEqual(repair_broken_rule_labels(permission), 0)


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

    def test_route_rule_set_contains_all_eight_rules(self) -> None:
        china = self.service.country_by_code("156")
        uzbekistan = self.service.country_by_code("860")
        kazakhstan = self.service.country_by_code("398")
        results = self.service.route_rule_set(china, uzbekistan, kazakhstan)
        self.assertEqual([result.base_vid_cd for result in results], ["5", "1", "2", "3", "4", "6", "7", "8"])
        domestic = next(result for result in results if result.base_vid_cd == "6")
        self.assertEqual(domestic.rule.get("permission_cd"), "3")

    def test_every_country_has_all_eight_core_rules(self) -> None:
        expected = {str(index) for index in range(1, 9)}
        incomplete = {
            code: sorted(expected - set(country_rules))
            for code, country_rules in self.service.rules.items()
            if not expected.issubset(country_rules)
        }
        self.assertEqual(incomplete, {})
        self.assertTrue(
            all(
                country_rules["6"].get("permission_cd") == "3"
                for code, country_rules in self.service.rules.items()
                if code != "860"
            )
        )

    def test_afghanistan_reference_table_matches_all_published_rows(self) -> None:
        expected = {
            "1": ("2", "2"),
            "2": ("2", "1"),
            "3": ("2", "1"),
            "4": ("2", "1"),
            "5": ("2", "1"),
            "6": ("3", "0"),
            "7": ("2", "1"),
            "8": ("2", "1"),
        }
        actual = {
            vid: (str(rule.get("permission_cd")), str(rule.get("dues_cd")))
            for vid, rule in self.service.rules["004"].items()
            if vid in expected
        }
        self.assertEqual(actual, expected)

    def test_related_rules_are_in_telegram_message(self) -> None:
        china = self.service.country_by_code("156")
        uzbekistan = self.service.country_by_code("860")
        kazakhstan = self.service.country_by_code("398")
        results = self.service.route_rule_set(china, uzbekistan, kazakhstan)
        message = build_permit_message(results[0], lang="uz", related_results=results[1:])
        self.assertIn("Majburiyatnoma asosida yuksiz kirish", message)
        self.assertIn("Majburiyatnoma asosida yuksiz tranzit", message)
        self.assertIn("Ichki tashuv", message)

    def test_turkmenistan_extra_fee_only_applies_to_third_country_loaded_rule(self) -> None:
        china = self.service.country_by_code("156")
        uzbekistan = self.service.country_by_code("860")
        turkmenistan = self.service.country_by_code("795")
        results = self.service.route_rule_set(china, uzbekistan, turkmenistan)
        self.assertTrue(turkmenistan_extra_fee_applies(results[0]))
        self.assertTrue(
            all(
                not turkmenistan_extra_fee_applies(item)
                for item in results[1:]
                if item.base_vid_cd not in {"4", "5"}
            )
        )

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
        self.assertIn("loading=\"lazy\"", script)
        self.assertNotIn("preloadFlags", script)
        self.assertNotIn("permit-operation", html)
        self.assertNotIn("data-operation=", html)
        self.assertIn("related_rules", script)
        self.assertIn("permit_exempt_goods", (ROOT / "app" / "webapp.py").read_text(encoding="utf-8"))
        self.assertIn("rule-detail-grid", script)
        self.assertIn("country_input_profile", (ROOT / "app" / "webapp.py").read_text(encoding="utf-8"))

    def test_admin_can_manage_transport_types(self) -> None:
        html = (ROOT / "app" / "static" / "admin.html").read_text(encoding="utf-8")
        script = (ROOT / "app" / "static" / "admin.js").read_text(encoding="utf-8")
        backend = (ROOT / "app" / "admin_panel.py").read_text(encoding="utf-8")
        self.assertIn("manage-transport-types", html)
        self.assertIn("openTransportTypes", script)
        self.assertIn("/admin/api/transport-type", backend)

    def test_portal_services_are_available(self) -> None:
        html = (ROOT / "app" / "static" / "webapp.html").read_text(encoding="utf-8")
        script = (ROOT / "app" / "static" / "webapp.js").read_text(encoding="utf-8")
        backend = (ROOT / "app" / "webapp.py").read_text(encoding="utf-8")
        self.assertIn('data-view="posts"', html)
        self.assertIn('id="posts-map"', html)
        self.assertNotIn('id="public-post-list"', html)
        self.assertIn('/static/webapp/leaflet-local.css', html)
        self.assertIn("map-mode", script)
        self.assertIn("saveCurrentRoute", script)
        self.assertIn("openFeedback", script)
        self.assertIn('/api/webapp/posts', backend)
        self.assertIn('/api/webapp/feedback', backend)
        self.assertIn('/api/webapp/saved-routes', backend)
        self.assertIn('/api/webapp/uzbekistan-border', backend)
        self.assertIn("L.geoJSON", script)
        self.assertNotIn("const UZ_BORDER", script)
        self.assertIn("leaflet@1.9.4", html)
        self.assertNotIn("integrity=", html)
        self.assertIn("World_Imagery", script)
        self.assertIn("postVisual", script)
        for post_type in ("CHBP", "TIF", "AERO", "RW", "PORT"):
            self.assertIn(post_type, script)

    def test_admin_post_editor_supports_map_coordinates(self) -> None:
        html = (ROOT / "app" / "static" / "admin.html").read_text(encoding="utf-8")
        script = (ROOT / "app" / "static" / "admin.js").read_text(encoding="utf-8")
        backend = (ROOT / "app" / "admin_panel.py").read_text(encoding="utf-8")
        self.assertIn("leaflet@1.9.4", html)
        self.assertIn("parseCoordinates", script)
        self.assertIn('id="post-coordinates"', script)
        self.assertIn('id="post-coordinate-map"', script)
        self.assertIn("openCoordinatePicker", script)
        self.assertIn("World_Imagery", script)
        self.assertIn("AbortController", script)
        self.assertIn("asyncio.wait_for(portal_store.save_post", backend)
        self.assertIn('asyncio.create_task(audit("customs_post_save"', backend)
        self.assertNotIn('id="post-lat"', script)
        self.assertNotIn('id="post-lon"', script)

    def test_uzbekistan_border_is_valid_multipolygon(self) -> None:
        import json

        border = json.loads((ROOT / "data" / "uzbekistan_border.geojson").read_text(encoding="utf-8"))
        self.assertEqual(border["type"], "FeatureCollection")
        self.assertTrue(border["features"])
        self.assertIn(border["features"][0]["geometry"]["type"], {"Polygon", "MultiPolygon"})

    def test_admin_has_operations_dashboard(self) -> None:
        html = (ROOT / "app" / "static" / "admin.html").read_text(encoding="utf-8")
        script = (ROOT / "app" / "static" / "admin.js").read_text(encoding="utf-8")
        backend = (ROOT / "app" / "admin_panel.py").read_text(encoding="utf-8")
        for screen in ("analytics", "posts", "feedback"):
            self.assertIn(f'id="screen-{screen}"', html)
        self.assertIn("loadAnalytics", script)
        self.assertIn("system-status", html)
        self.assertIn('/admin/api/analytics', backend)
if __name__ == "__main__":
    unittest.main()
