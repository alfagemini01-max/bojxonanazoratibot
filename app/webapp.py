from __future__ import annotations

import asyncio
import logging
import math
import hashlib
import hmac
import json
import time
from time import monotonic
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl

from aiohttp import web

from app.config import Settings
from app.metrics import metrics
from app.portal_store import PortalStore
from app.services.fee_calculator import FeeCalculator
from app.services.permit import (
    IRAN_CODE,
    TURKMENISTAN_CODE,
    UZBEKISTAN_CODE,
    PermitRuleService,
    country_label,
    localized_additional_conditions,
    localized_exception_text,
    permit_status_text,
    transport_type_label,
    turkmenistan_extra_fee_applies,
)


STATIC_DIR = Path(__file__).resolve().parent / "static"
logger = logging.getLogger(__name__)
ISO_NUMERIC_TO_ALPHA2 = dict(
    item.split(":")
    for item in (
        "004:AF,008:AL,010:AQ,012:DZ,016:AS,020:AD,024:AO,028:AG,031:AZ,032:AR,036:AU,040:AT,"
        "044:BS,048:BH,050:BD,051:AM,052:BB,056:BE,060:BM,064:BT,068:BO,074:BV,076:BR,084:BZ,"
        "086:IO,090:SB,092:VG,096:BN,100:BG,104:MM,108:BI,112:BY,116:KH,120:CM,124:CA,132:CV,"
        "136:KY,140:CF,144:LK,148:TD,152:CL,156:CN,158:TW,162:CX,166:CC,170:CO,174:KM,178:CG,"
        "180:CD,184:CK,188:CR,191:HR,192:CU,196:CY,203:CZ,204:BJ,208:DK,212:DM,214:DO,218:EC,"
        "222:SV,226:GQ,231:ET,232:ER,233:EE,234:FO,238:FK,242:FJ,246:FI,250:FR,254:GF,258:PF,"
        "260:TF,262:DJ,266:GA,268:GE,270:GM,274:PS,276:DE,288:GH,292:GI,296:KI,300:GR,304:GL,"
        "308:GD,312:GP,316:GU,320:GT,324:GN,328:GY,332:HT,334:HM,336:VA,340:HN,344:HK,348:HU,"
        "352:IS,356:IN,360:ID,364:IR,368:IQ,372:IE,376:IL,380:IT,384:CI,388:JM,392:JP,396:UM,"
        "398:KZ,400:JO,404:KE,408:KP,410:KR,414:KW,417:KG,418:LA,422:LB,426:LS,428:LV,430:LR,"
        "434:LY,438:LI,440:LT,442:LU,496:MN,498:MD,528:NL,616:PL,643:RU,703:SK,705:SI,756:CH,"
        "762:TJ,792:TR,795:TM,804:UA,860:UZ"
    ).split(",")
)
ISO_NUMERIC_TO_ALPHA2.update(
    dict(
        item.split(":")
        for item in (
            "070:BA,072:BW,175:YT,239:GS,248:AX,275:PS,446:MO,450:MG,454:MW,458:MY,462:MV,466:ML,470:MT,474:MQ,478:MR,480:MU,"
            "484:MX,488:UM,492:MC,499:ME,500:MS,504:MA,508:MZ,512:OM,516:NA,520:NR,524:NP,530:NL,531:CW,"
            "533:AW,534:SX,535:BQ,540:NC,548:VU,554:NZ,558:NI,562:NE,566:NG,570:NU,574:NF,"
            "578:NO,580:MP,581:UM,583:FM,584:MH,585:PW,586:PK,591:PA,598:PG,600:PY,604:PE,"
            "608:PH,612:PN,620:PT,624:GW,626:TL,630:PR,634:QA,638:RE,642:RO,646:RW,652:BL,"
            "654:SH,659:KN,660:AI,662:LC,663:MF,666:PM,670:VC,674:SM,678:ST,682:SA,686:SN,"
            "688:RS,690:SC,694:SL,702:SG,704:VN,706:SO,710:ZA,716:ZW,724:ES,728:SS,729:SD,"
            "732:EH,740:SR,744:SJ,748:SZ,752:SE,760:SY,764:TH,768:TG,772:TK,776:TO,780:TT,"
            "784:AE,788:TN,796:TC,798:TV,800:UG,807:MK,818:EG,826:GB,830:GB,831:GG,832:JE,833:IM,"
            "834:TZ,840:US,850:VI,854:BF,858:UY,862:VE,872:UM,876:WF,882:WS,887:YE,891:RS,894:ZM,736:SD"
        ).split(",")
    )
)


def _lang(value: object) -> str:
    return str(value or "uz") if str(value or "uz") in {"uz", "ru", "en"} else "uz"


def _bool(value: object) -> bool:
    return value is True or str(value or "").lower() in {"1", "true", "yes", "on"}


def _number(value: object, minimum: float = 0.0, maximum: float = 1_000_000_000.0) -> float:
    try:
        result = float(str(value or 0).replace(" ", "").replace(",", "."))
    except ValueError as exc:
        raise web.HTTPBadRequest(text="Raqamli qiymat noto'g'ri.") from exc
    if not math.isfinite(result) or result < minimum or result > maximum:
        raise web.HTTPBadRequest(text="Raqamli qiymat ruxsat etilgan oraliqda emas.")
    return result


def _days(value: object) -> int:
    number = _number(value, 0, 10_000)
    if not number.is_integer():
        raise web.HTTPBadRequest(text="Kunlar soni butun son bo'lishi kerak.")
    return int(number)


def _country(service: PermitRuleService, value: object):
    text = str(value or "").strip()
    if not text.isdigit():
        raise web.HTTPBadRequest(text="Davlat kodi noto'g'ri.")
    country = service.country_by_code(text.zfill(3))
    if not country:
        raise web.HTTPBadRequest(text="Davlat topilmadi.")
    return country


def _route_rule_set_compatible(
    service: PermitRuleService,
    origin: object,
    destination: object,
    vehicle: object,
) -> list[object]:
    """Support rolling deploys where webapp.py starts before permit.py is updated."""
    route_rule_set = getattr(service, "route_rule_set", None)
    if callable(route_rule_set):
        return list(route_rule_set(origin, destination, vehicle))

    logger.warning(
        "Permit service is missing route_rule_set; using compatibility fallback. "
        "Deploy app/services/permit.py from the same release."
    )
    results = [service.evaluate(origin, destination, vehicle)]
    for operation in ("empty_entry", "empty_transit"):
        try:
            results.append(service.evaluate(origin, destination, vehicle, operation))
        except TypeError:
            logger.warning(
                "Permit service does not support operation=%s; update app/services/permit.py",
                operation,
            )

    uzbekistan = service.country_by_code(UZBEKISTAN_CODE)
    if uzbekistan:
        results.append(service.evaluate(uzbekistan, uzbekistan, vehicle))

    unique: dict[str, object] = {}
    for item in results:
        code = str(getattr(item, "base_vid_cd", None) or getattr(item, "vid_cd", ""))
        unique.setdefault(code, item)
    return list(unique.values())


def _weight_category(weight: float) -> str:
    if weight <= 10:
        return "up_to_10"
    if weight <= 20:
        return "from_10_to_20"
    return "over_20"


def _stay_duration(days: int) -> str:
    return "up_to_14" if days <= 14 else "over_14"


def _permit_payload(
    body: dict[str, Any],
    permit_service: PermitRuleService,
    fee_calculator: FeeCalculator,
) -> dict[str, Any]:
    permit_service.reload_if_changed()
    fee_calculator.reload_if_changed()
    lang = _lang(body.get("lang"))
    origin = _country(permit_service, body.get("origin"))
    destination = _country(permit_service, body.get("destination"))
    vehicle = _country(permit_service, body.get("vehicle"))
    if origin.code == destination.code == vehicle.code and origin.code != UZBEKISTAN_CODE:
        raise web.HTTPBadRequest(text="Ushbu tashuv O'zbekiston hududiga aloqador emas.")

    result = permit_service.evaluate(origin, destination, vehicle)
    rule = result.rule or {}
    permission_code = str(rule.get("permission_cd", "0"))
    dues_code = str(rule.get("dues_cd", "0"))
    weight = _number(body.get("weight", 20), 0.01, 1_000)
    stay_days = _days(body.get("stay_days", 14)) or 14
    base_fee = 0.0
    fee_known = dues_code in {"1", "2"}
    if dues_code == "1":
        base_fee = fee_calculator.entry_fee_usd_for_rule(
            rule,
            vehicle.code,
            _weight_category(weight),
            _stay_duration(stay_days),
        )
    before_discount = base_fee
    humanitarian = _bool(body.get("humanitarian"))
    if humanitarian and base_fee > 0:
        base_fee *= 0.5
    extra_fee = 0.0
    if turkmenistan_extra_fee_applies(result):
        extra_fee = float(fee_calculator.data["entry_fee"]["turkmenistan_extra_usd"])
    purchase_fee = 0.0
    if _bool(body.get("permit_purchase")) and vehicle.code != UZBEKISTAN_CODE and permission_code != "3":
        base_vid = result.base_vid_cd or result.vid_cd
        purchase_fee = 200.0 if base_vid == "3" else 800.0 if base_vid in {"4", "5"} else 400.0

    warnings: list[str] = []
    if _bool(body.get("heavy")):
        warnings.append("heavy")
    if humanitarian and extra_fee:
        warnings.append("humanitarian_extra")
    if str(rule.get("source", "")).startswith(("manual:", "fallback:")):
        warnings.append("source_review")
    if not result.rule:
        warnings.append("rule_missing")
    if vehicle.code == "000":
        warnings.append("other_country")

    related_rules = []
    for item in _route_rule_set_compatible(permit_service, origin, destination, vehicle):
        item_rule = item.rule or {}
        item_dues_code = str(item_rule.get("dues_cd", "0"))
        item_base_fee = 0.0
        if item_dues_code == "1":
            item_base_fee = fee_calculator.entry_fee_usd_for_rule(
                item_rule,
                vehicle.code,
                _weight_category(weight),
                _stay_duration(stay_days),
            )
            if humanitarian:
                item_base_fee *= 0.5
        item_extra_fee = (
            float(fee_calculator.data["entry_fee"]["turkmenistan_extra_usd"])
            if turkmenistan_extra_fee_applies(item)
            else 0.0
        )
        base_code = item.base_vid_cd or item.vid_cd
        primary_code = result.base_vid_cd or result.vid_cd
        related_rules.append(
            {
                "role": "route" if base_code == primary_code else "reference",
                "selected": base_code == primary_code,
                "transport_type": {
                    "code": item.vid_cd,
                    "base_code": base_code,
                    "name": transport_type_label(item.vid_cd, item.vid_name, lang, item.vid_labels),
                },
                "permission": {
                    "code": str(item_rule.get("permission_cd", "0")),
                    "text": permit_status_text(item.rule, lang),
                },
                "permit_exempt_goods": {
                    "code": str(item_rule.get("exception_cd", "0")),
                    "listed": bool(item.exceptions),
                    "count": len(item.exceptions),
                },
                "fee": {
                    "dues_code": item_dues_code,
                    "known": item_dues_code in {"1", "2"},
                    "base_usd": round(item_base_fee, 2),
                    "extra_usd": round(item_extra_fee, 2),
                    "total_usd": round(item_base_fee + item_extra_fee, 2),
                },
                "additional_conditions": localized_additional_conditions(item.rule, lang),
                "exceptions": [localized_exception_text(row, lang) for row in item.exceptions],
            }
        )

    return {
        "ok": True,
        "lang": lang,
        "route": {
            "origin": {"code": origin.code, "name": country_label(origin, lang)},
            "destination": {"code": destination.code, "name": country_label(destination, lang)},
            "vehicle": {"code": vehicle.code, "name": country_label(vehicle, lang)},
        },
        "transport_type": {
            "code": result.vid_cd,
            "base_code": result.base_vid_cd or result.vid_cd,
            "name": transport_type_label(result.vid_cd, result.vid_name, lang, result.vid_labels),
            "operation": "cargo",
        },
        "permission": {"code": permission_code, "text": permit_status_text(result.rule, lang)},
        "fee": {
            "dues_code": dues_code,
            "known": fee_known,
            "base_usd": round(base_fee, 2),
            "base_before_discount_usd": round(before_discount, 2),
            "extra_usd": round(extra_fee, 2),
            "permit_purchase_usd": round(purchase_fee, 2),
            "total_usd": round(base_fee + extra_fee + purchase_fee, 2),
        },
        "conditions": {"weight": weight, "stay_days": stay_days, "humanitarian": humanitarian},
        "exceptions": [localized_exception_text(row, lang) for row in result.exceptions],
        "additional_conditions": localized_additional_conditions(rule, lang),
        "notes": {
            "uz": str(rule.get("dues_amount_note_uz") or ""),
            "ru": str(rule.get("dues_amount_note_ru") or ""),
            "en": str(rule.get("dues_amount_note_en") or ""),
        },
        "warnings": warnings,
        "related_rules": related_rules,
    }


def _fee_payload(
    body: dict[str, Any],
    permit_service: PermitRuleService,
    calculator: FeeCalculator,
) -> dict[str, Any]:
    calculator.reload_if_changed()
    lang = _lang(body.get("lang"))
    vehicle = _country(permit_service, body.get("vehicle_country"))
    vehicle_type = str(body.get("vehicle_type") or "truck")
    direction = str(body.get("direction") or "entry")
    if vehicle_type not in {"light", "bus", "truck", "truck_trailer"}:
        raise web.HTTPBadRequest(text="Transport turi noto'g'ri.")
    if direction not in {"entry", "transit", "exit"}:
        raise web.HTTPBadRequest(text="Yo'nalish noto'g'ri.")

    cargo = vehicle_type in {"truck", "truck_trailer"}
    origin = _country(permit_service, body.get("origin")) if cargo else None
    destination = _country(permit_service, body.get("destination")) if cargo else None
    permit_result = permit_service.evaluate(origin, destination, vehicle) if origin and destination else None
    foreign = vehicle.code != UZBEKISTAN_CODE
    weight = _number(body.get("weight", 20), 0.01, 1_000)
    stay_days = _days(body.get("stay_days", 14)) or 14
    items: list[dict[str, Any]] = []
    warnings: list[str] = []

    def add_item(key: str, title: str, amount_som: int, amount_usd: float | None, basis: str, note: str = "") -> None:
        items.append({
            "key": key,
            "title": title,
            "amount_som": int(round(amount_som)),
            "amount_usd": round(amount_usd, 2) if amount_usd is not None else None,
            "basis": basis,
            "note": note,
        })

    if foreign and cargo and direction in {"entry", "transit"} and permit_result:
        rule = permit_result.rule or {}
        if str(rule.get("dues_cd", "0")) == "1":
            usd = calculator.entry_fee_usd_for_rule(
                rule, vehicle.code, _weight_category(weight), _stay_duration(stay_days)
            )
            if _bool(body.get("humanitarian")):
                usd *= 0.5
            if turkmenistan_extra_fee_applies(permit_result):
                usd += float(calculator.data["entry_fee"]["turkmenistan_extra_usd"])
            if usd > 0 or vehicle.code == IRAN_CODE:
                add_item(
                    "entry_fee",
                    "Kirish/tranzit yig'imi",
                    int(round(usd * calculator.usd_rate)),
                    usd,
                    calculator.legal_basis["entry_transit_fee"],
                )

    if _bool(body.get("declared")):
        customs_value = _number(body.get("customs_value_usd"), 0.01)
        bhm, amount = calculator.customs_clearance_amount(customs_value)
        add_item(
            "customs_clearance",
            "Bojxona rasmiylashtiruvi yig'imi",
            amount,
            None,
            calculator.legal_basis["customs_clearance"],
            f"{customs_value:g} USD; {bhm:g} BHM",
        )

    if cargo and direction in {"entry", "transit"}:
        bhm = float(calculator.data["fixed"]["transit_declaration_bhm"])
        add_item(
            "transit_declaration",
            "Tranzit deklaratsiyasi rasmiylashtiruvi",
            int(round(bhm * calculator.bhm_value)),
            None,
            calculator.legal_basis["transit_declaration"],
            f"{bhm:g} BHM",
        )

    if _bool(body.get("tinted")):
        if foreign and direction in {"entry", "transit"}:
            usd = float(calculator.data["fixed"]["tinted_foreign_usd"])
            add_item(
                "tinted",
                "Qoraytirilgan oyna uchun yig'im",
                int(round(usd * calculator.usd_rate)),
                usd,
                calculator.legal_basis["tinted_foreign"],
            )
        else:
            warnings.append("tinted_domestic")
    if foreign and direction in {"entry", "transit"} and _bool(body.get("osago_missing")):
        warnings.append("osago")
    if _bool(body.get("heavy")):
        warnings.append("heavy")
    if _bool(body.get("humanitarian")):
        warnings.append("humanitarian")
    if _bool(body.get("animal")):
        warnings.append("veterinary")

    temp_days = _days(body.get("temp_overstay_days", 0))
    if temp_days:
        add_item(
            "temp_overstay",
            "Vaqtincha olib kirish muddatini o'tkazish",
            temp_days * calculator.bhm_value,
            None,
            calculator.legal_basis["temporary_import_overstay"],
            f"{temp_days} kun; 1 BHM/kun",
        )
    delivery_days = _days(body.get("delivery_overdue_days", 0))
    if delivery_days:
        add_item(
            "delivery_overdue",
            "Yukni muddatida yetkazmaganlik yig'imi",
            delivery_days * calculator.bhm_value,
            None,
            calculator.legal_basis["overdue_delivery"],
            f"{delivery_days} kun; 1 BHM/kun",
        )

    return {
        "ok": True,
        "lang": lang,
        "route": {
            "vehicle": {"code": vehicle.code, "name": country_label(vehicle, lang)},
            "origin": {"code": origin.code, "name": country_label(origin, lang)} if origin else None,
            "destination": {"code": destination.code, "name": country_label(destination, lang)} if destination else None,
            "direction": direction,
            "vehicle_type": vehicle_type,
        },
        "transport_type": (
            {"code": permit_result.vid_cd, "name": transport_type_label(permit_result.vid_cd, permit_result.vid_name, lang, permit_result.vid_labels)}
            if permit_result else None
        ),
        "items": items,
        "totals": {
            "som": sum(item["amount_som"] for item in items),
            "usd": round(sum(item["amount_usd"] or 0 for item in items), 2),
            "usd_rate": calculator.usd_rate,
            "bhm": calculator.bhm_value,
        },
        "warnings": warnings,
    }


async def webapp_page(_: web.Request) -> web.FileResponse:
    return web.FileResponse(
        STATIC_DIR / "webapp.html",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


def _telegram_user_id(init_data: str, bot_token: str) -> int | None:
    if not init_data or not bot_token:
        return None
    values = dict(parse_qsl(init_data, keep_blank_values=True))
    supplied = values.pop("hash", "")
    try:
        if time.time() - int(values.get("auth_date", "0")) > 86400:
            return None
    except ValueError:
        return None
    check = "\n".join(f"{key}={values[key]}" for key in sorted(values))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    if not supplied or not hmac.compare_digest(supplied, expected):
        return None
    try:
        return int(json.loads(values.get("user", "{}"))["id"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None


def setup_webapp_routes(app: web.Application, settings: Settings, portal_store: PortalStore | None = None) -> None:
    permit_service = PermitRuleService(settings.permission_rules_path)
    fee_calculator = FeeCalculator(settings.fees_rules_path, settings.bhm_value, settings.usd_fallback_rate)
    countries_cache: dict[str, tuple[int, dict[str, Any]]] = {}

    def rule_version() -> int:
        try:
            return int(settings.permission_rules_path.stat().st_mtime_ns)
        except OSError:
            return 0

    async def countries(request: web.Request) -> web.Response:
        lang = _lang(request.query.get("lang"))
        permit_service.reload_if_changed()
        current_version = rule_version()
        cached = countries_cache.get(lang)
        if cached and cached[0] == current_version:
            return web.json_response(cached[1], headers={"Cache-Control": "public, max-age=300", "ETag": f'"countries-{lang}-{current_version}"'})
        rows = []
        def sort_name(code: str) -> str:
            country = permit_service.country_by_code(code)
            return country_label(country, lang).casefold() if country else code

        ordered_codes = sorted(permit_service.countries, key=sort_name)
        if "000" in ordered_codes:
            ordered_codes.remove("000")
            ordered_codes.insert(0, "000")
        for code in ordered_codes:
            country = permit_service.country_by_code(code)
            if country:
                profile = permit_service.country_input_profile(code)
                rows.append(
                    {
                        "code": code,
                        "name": country_label(country, lang),
                        "labels": {
                            language: country_label(country, language)
                            for language in ("uz", "ru", "en")
                        },
                        "iso": ISO_NUMERIC_TO_ALPHA2.get(code, ""),
                        **profile,
                    }
                )
        payload = {"ok": True, "countries": rows, "version": current_version}
        countries_cache[lang] = (current_version, payload)
        return web.json_response(payload, headers={"Cache-Control": "public, max-age=300", "ETag": f'"countries-{lang}-{current_version}"'})

    async def permit_check(request: web.Request) -> web.Response:
        started = monotonic()
        try:
            body = await request.json()
            response = _permit_payload(body, permit_service, fee_calculator)
            response["rule_version"] = rule_version()
            metrics.increment("webapp_permit_checks")
            if portal_store:
                asyncio.create_task(portal_store.record_event(
                    "permit_check", origin_code=body.get("origin"), destination_code=body.get("destination"),
                    vehicle_code=body.get("vehicle"), transport_type=response["transport_type"]["base_code"],
                    rule_version=response["rule_version"],
                    error_code="rule_missing" if "rule_missing" in response.get("warnings", []) else None,
                    metadata={"visitor_id": body.get("visitor_id"), "lang": body.get("lang")},
                ))
            return web.json_response(response)
        except web.HTTPException as exc:
            if portal_store:
                asyncio.create_task(portal_store.record_event("error", error_code=f"http_{exc.status}"))
            raise
        except Exception:
            metrics.increment("errors")
            if portal_store:
                asyncio.create_task(portal_store.record_event("error", error_code="permit_internal"))
            logger.exception("Web App permit check failed")
            raise web.HTTPInternalServerError(text="Tekshiruv vaqtida texnik xatolik yuz berdi.")
        finally:
            metrics.observe("webapp_permit", monotonic() - started)

    async def fee_check(request: web.Request) -> web.Response:
        started = monotonic()
        try:
            body = await request.json()
            response = _fee_payload(body, permit_service, fee_calculator)
            response["rule_version"] = rule_version()
            metrics.increment("webapp_fee_checks")
            if portal_store:
                asyncio.create_task(portal_store.record_event(
                    "fee_check", origin_code=body.get("origin"), destination_code=body.get("destination"),
                    vehicle_code=body.get("vehicle_country"), transport_type=(response.get("transport_type") or {}).get("base_code"),
                    rule_version=response["rule_version"], metadata={"visitor_id": body.get("visitor_id"), "lang": body.get("lang")},
                ))
            return web.json_response(response)
        except web.HTTPException:
            raise
        except Exception:
            metrics.increment("errors")
            if portal_store:
                asyncio.create_task(portal_store.record_event("error", error_code="fees_internal"))
            logger.exception("Web App fee calculation failed")
            raise web.HTTPInternalServerError(text="Hisoblash vaqtida texnik xatolik yuz berdi.")
        finally:
            metrics.observe("webapp_fees", monotonic() - started)

    async def public_posts(request: web.Request) -> web.Response:
        if not portal_store:
            raise web.HTTPServiceUnavailable(text="Postlar katalogi ishga tushmagan.")
        lang = _lang(request.query.get("lang"))
        rows = await portal_store.list_posts()
        for row in rows:
            row["name"] = row.get(f"name_{lang}") or row.get("name_uz")
        return web.json_response({"ok": True, "posts": rows}, headers={"Cache-Control": "public, max-age=120"})

    async def uzbekistan_border(_: web.Request) -> web.StreamResponse:
        border_path = settings.permission_rules_path.parent / "uzbekistan_border.geojson"
        if not border_path.exists():
            raise web.HTTPServiceUnavailable(text="O'zbekiston chegarasi fayli topilmadi.")
        return web.FileResponse(
            border_path,
            headers={"Cache-Control": "public, max-age=86400, immutable"},
        )

    async def feedback(request: web.Request) -> web.Response:
        if not portal_store:
            raise web.HTTPServiceUnavailable(text="Murojaatlar ombori ishga tushmagan.")
        body = await request.json()
        body["telegram_user_id"] = _telegram_user_id(str(body.get("init_data") or ""), settings.bot_token)
        try:
            feedback_id = await portal_store.create_feedback(body)
        except ValueError as exc:
            raise web.HTTPBadRequest(text=str(exc)) from exc
        await portal_store.record_event("feedback", origin_code=body.get("origin"), destination_code=body.get("destination"), vehicle_code=body.get("vehicle"), transport_type=body.get("transport_type"), rule_version=body.get("rule_version"), metadata={"visitor_id": body.get("visitor_id")})
        return web.json_response({"ok": True, "id": feedback_id})

    async def save_route(request: web.Request) -> web.Response:
        if not portal_store:
            raise web.HTTPServiceUnavailable(text="Yo'nalishlar ombori ishga tushmagan.")
        body = await request.json()
        user_id = _telegram_user_id(str(body.get("init_data") or ""), settings.bot_token)
        if not user_id:
            raise web.HTTPUnauthorized(text="Yo'nalishni saqlash faqat Telegram ichida mavjud.")
        for key in ("origin", "destination", "vehicle"):
            _country(permit_service, body.get(key))
        await portal_store.save_route(user_id, body)
        return web.json_response({"ok": True})

    app.router.add_get("/app", webapp_page)
    app.router.add_get("/webapp", webapp_page)
    app.router.add_get("/api/webapp/countries", countries)
    app.router.add_post("/api/webapp/permit", permit_check)
    app.router.add_post("/api/webapp/fees", fee_check)
    app.router.add_get("/api/webapp/posts", public_posts)
    app.router.add_get("/api/webapp/uzbekistan-border", uzbekistan_border)
    app.router.add_post("/api/webapp/feedback", feedback)
    app.router.add_post("/api/webapp/saved-routes", save_route)
    app.router.add_static("/static/webapp", STATIC_DIR, show_index=False, append_version=True)
