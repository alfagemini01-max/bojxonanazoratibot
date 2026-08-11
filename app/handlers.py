from __future__ import annotations

import html
import logging
import re
from time import perf_counter

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)

from app.config import Settings
from app.i18n import LANGUAGES, button_texts, normalize_lang, t
from app.metrics import metrics
from app.middleware import UserRateLimitMiddleware
from app.services.fee_calculator import FeeCalculator, TAJIKISTAN_CODE
from app.services.permit import PermitRuleService, UZBEKISTAN_CODE, build_permit_message, country_label, turkmenistan_extra_fee_applies
from app.services.permit import TURKMENISTAN_CODE, is_eu_or_azerbaijan
from app.states import CheckState, FeeCalcState
from app.storage import UserStorage

logger = logging.getLogger(__name__)
MAX_TELEGRAM_TEXT_LENGTH = 3800

CHECK_BUTTONS = button_texts("button_check")
FEE_BUTTONS = button_texts("button_fees")
LANGUAGE_BUTTONS = button_texts("button_language")
CANCEL_BUTTONS = button_texts("button_cancel")

QUICK_COUNTRIES = {
    "uz": [("860", "🇺🇿 O'zbekiston"), ("398", "🇰🇿 Qozog'iston"), ("417", "🇰🇬 Qirg'iziston"), ("643", "🇷🇺 Rossiya"), ("156", "🇨🇳 Xitoy"), ("795", "🇹🇲 Turkmaniston"), ("762", "🇹🇯 Tojikiston"), ("004", "🇦🇫 Afg'oniston")],
    "ru": [("860", "🇺🇿 Узбекистан"), ("398", "🇰🇿 Казахстан"), ("417", "🇰🇬 Кыргызстан"), ("643", "🇷🇺 Россия"), ("156", "🇨🇳 Китай"), ("795", "🇹🇲 Туркменистан"), ("762", "🇹🇯 Таджикистан"), ("004", "🇦🇫 Афганистан")],
    "en": [("860", "🇺🇿 Uzbekistan"), ("398", "🇰🇿 Kazakhstan"), ("417", "🇰🇬 Kyrgyzstan"), ("643", "🇷🇺 Russia"), ("156", "🇨🇳 China"), ("795", "🇹🇲 Turkmenistan"), ("762", "🇹🇯 Tajikistan"), ("004", "🇦🇫 Afghanistan")],
}


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label, callback_data=f"set_lang:{code}")]
            for code, label in LANGUAGES.items()
        ]
    )


def main_menu_keyboard(lang: str = "uz") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t(lang, "button_check")), KeyboardButton(text=t(lang, "button_fees"))],
            [KeyboardButton(text=t(lang, "button_language"))],
        ],
        resize_keyboard=True,
        input_field_placeholder=t(lang, "menu_placeholder"),
    )


def cancel_keyboard(lang: str = "uz") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t(lang, "button_cancel"))]],
        resize_keyboard=True,
    )


def simple_options_keyboard(lang: str, keys: list[str], columns: int = 2) -> ReplyKeyboardMarkup:
    rows: list[list[KeyboardButton]] = []
    for index in range(0, len(keys), columns):
        rows.append([KeyboardButton(text=t(lang, key)) for key in keys[index : index + columns]])
    rows.append([KeyboardButton(text=t(lang, "button_cancel"))])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def yes_no_keyboard(lang: str) -> ReplyKeyboardMarkup:
    return simple_options_keyboard(lang, ["button_yes", "button_no"])


def button_value(lang: str, key_to_value: dict[str, str], text: str | None) -> str | None:
    value = (text or "").strip()
    for key, mapped_value in key_to_value.items():
        if value == t(lang, key):
            return mapped_value
    return None


def _country_from_match(match):
    return getattr(match, "country", match)


def country_choices_keyboard(matches, slot: str, lang: str = "uz") -> InlineKeyboardMarkup:
    rows = []
    seen_codes = set()
    for match in matches:
        country = _country_from_match(match)
        if not country or country.code in seen_codes:
            continue
        seen_codes.add(country.code)
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{country_label(country, lang)} ({country.code})",
                    callback_data=f"pick_country:{slot}:{country.code}",
                )
            ]
        )

    if "000" not in seen_codes:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t(lang, "button_other_country") + " (000)",
                    callback_data=f"pick_country:{slot}:000",
                )
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def other_country_keyboard(slot: str, lang: str = "uz") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "button_other_country") + " (000)", callback_data=f"pick_country:{slot}:000")]
        ]
    )


def quick_country_keyboard(slot: str, lang: str = "uz") -> InlineKeyboardMarkup:
    choices = QUICK_COUNTRIES.get(normalize_lang(lang), QUICK_COUNTRIES["uz"])
    rows = [
        [
            InlineKeyboardButton(text=label, callback_data=f"pick_country:{slot}:{code}")
            for code, label in choices[index : index + 2]
        ]
        for index in range(0, len(choices), 2)
    ]
    rows.append([InlineKeyboardButton(text=t(lang, "button_cancel"), callback_data="cancel_flow")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def split_telegram_text(text: str, limit: int = MAX_TELEGRAM_TEXT_LENGTH) -> list[str]:
    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    current: list[str] = []
    current_length = 0
    for line in text.splitlines():
        line_length = len(line) + 1
        if current and current_length + line_length > limit:
            chunks.append("\n".join(current))
            current = []
            current_length = 0
        if line_length > limit:
            chunks.append(line[:limit])
            continue
        current.append(line)
        current_length += line_length

    if current:
        chunks.append("\n".join(current))
    return chunks


def build_router(user_storage: UserStorage, settings: Settings) -> Router:
    router = Router(name="nazoratbot")
    limiter = UserRateLimitMiddleware()
    router.message.middleware(limiter)
    router.callback_query.middleware(limiter)
    permit_service = PermitRuleService(settings.permission_rules_path)
    fee_calculator = FeeCalculator(settings.fees_rules_path, settings.bhm_value, settings.usd_fallback_rate)

    async def profile_lang(user_id: int | None) -> str:
        if user_id is None:
            return "uz"
        profile = await user_storage.get_profile(user_id)
        return normalize_lang(profile.language_code if profile else None)

    async def ask_language(message: Message) -> None:
        await message.answer(t("uz", "choose_language"), reply_markup=language_keyboard())

    async def answer_country_not_found(message: Message, lang: str, raw_country: str, slot: str) -> None:
        await message.answer(
            t(lang, "country_no_match", country=html.escape(raw_country.strip())),
            reply_markup=other_country_keyboard(slot, lang),
        )

    def country_by_code(code: str):
        finder = getattr(permit_service, "country_by_code", None)
        if callable(finder):
            return finder(code)
        return permit_service.find_country(str(code).zfill(3))

    def search_country_matches(raw_country: str, limit: int = 8):
        searcher = getattr(permit_service, "search_countries", None)
        if callable(searcher):
            return searcher(raw_country, threshold=0.6, limit=limit)

        suggester = getattr(permit_service, "suggest_countries", None)
        if not callable(suggester):
            return []

        countries = []
        seen_codes = set()
        for suggestion in suggester(raw_country, limit=limit):
            match = re.search(r"\((\d{3})\)\s*$", str(suggestion))
            if not match:
                continue
            code = match.group(1)
            if code in seen_codes:
                continue
            country = country_by_code(code)
            if country:
                countries.append(country)
                seen_codes.add(code)
        return countries

    async def show_country_choices(message: Message, lang: str, raw_country: str, slot: str) -> None:
        matches = search_country_matches(raw_country, limit=8)
        if not matches:
            await answer_country_not_found(message, lang, raw_country, slot)
            return
        await message.answer(
            t(lang, "country_choose"),
            reply_markup=country_choices_keyboard(matches, slot, lang),
        )

    async def answer_long(message: Message, text: str, *, reply_markup=None) -> None:
        chunks = split_telegram_text(text)
        for index, chunk in enumerate(chunks):
            await message.answer(
                chunk,
                reply_markup=reply_markup if index == len(chunks) - 1 else None,
            )

    async def evaluate_route(message: Message, state: FSMContext, lang: str, vehicle_country_code: str, user_id: int | None = None) -> None:
        started = perf_counter()
        data = await state.get_data()
        origin = permit_service.find_country(str(data.get("origin_country_code", "")))
        destination = permit_service.find_country(str(data.get("destination_country_code", "")))
        vehicle_country = country_by_code(vehicle_country_code)
        if not origin or not destination or not vehicle_country:
            await state.clear()
            await message.answer(t(lang, "route_session_expired"), reply_markup=main_menu_keyboard(lang))
            return
        if (
            origin.code == destination.code == vehicle_country.code
            and origin.code != UZBEKISTAN_CODE
        ):
            await state.clear()
            await message.answer(t(lang, "route_not_related_to_uzbekistan"), reply_markup=main_menu_keyboard(lang))
            return

        try:
            result = permit_service.evaluate(origin, destination, vehicle_country)
            metrics.increment("permit_checks")
            logger.info(
                "Permit check requested user_id=%s origin=%s destination=%s vehicle_country=%s vid=%s permission=%s dues=%s",
                user_id or (message.from_user.id if message.from_user else None),
                origin.code,
                destination.code,
                vehicle_country.code,
                result.vid_cd,
                result.rule.get("permission_cd") if result.rule else None,
                result.rule.get("dues_cd") if result.rule else None,
            )
            await state.clear()
            await answer_long(
                message,
                build_permit_message(result, settings.timezone, lang),
                reply_markup=main_menu_keyboard(lang),
            )
        except Exception:
            metrics.increment("errors")
            logger.exception(
                "Permit check failed user_id=%s origin=%s destination=%s vehicle_country=%s",
                user_id or (message.from_user.id if message.from_user else None),
                origin.code,
                destination.code,
                vehicle_country.code,
            )
            await state.clear()
            await message.answer(t(lang, "technical_error"), reply_markup=main_menu_keyboard(lang))
        finally:
            metrics.observe("permit_check", perf_counter() - started)

    def is_cargo_vehicle(data: dict[str, object]) -> bool:
        return str(data.get("fee_vehicle_type", "")) in {"truck", "truck_trailer"}

    def fee_yes_no_value(lang: str, text: str | None) -> str | None:
        return button_value(lang, {"button_yes": "yes", "button_no": "no"}, text)

    def fee_rule_needs_rate(data: dict[str, object]) -> bool:
        if not is_cargo_vehicle(data):
            return False
        if str(data.get("fee_direction")) not in {"entry", "transit"}:
            return False
        vehicle_country = country_by_code(str(data.get("fee_vehicle_country_code", "")))
        origin = country_by_code(str(data.get("fee_origin_country_code", ""))) if data.get("fee_origin_country_code") else None
        destination = country_by_code(str(data.get("fee_destination_country_code", ""))) if data.get("fee_destination_country_code") else None
        if not vehicle_country or vehicle_country.code == UZBEKISTAN_CODE or not origin or not destination:
            return False
        result = permit_service.evaluate(origin, destination, vehicle_country)
        rule = result.rule or {}
        return str(rule.get("dues_cd", "0")) == "1" or turkmenistan_extra_fee_applies(result)

    async def finish_fee_calculation(message: Message, state: FSMContext, lang: str) -> None:
        started = perf_counter()
        data = await state.get_data()
        payload = {
            "vehicle_type": data.get("fee_vehicle_type"),
            "vehicle_country_code": data.get("fee_vehicle_country_code"),
            "direction": data.get("fee_direction"),
            "origin_country_code": data.get("fee_origin_country_code"),
            "destination_country_code": data.get("fee_destination_country_code"),
            "weight_category": data.get("fee_weight_category"),
            "stay_duration": data.get("fee_stay_duration"),
            "declared": data.get("fee_declared"),
            "customs_value_usd": data.get("fee_customs_value_usd"),
            "transit_declaration": data.get("fee_transit_declaration"),
            "tinted": data.get("fee_tinted"),
            "osago_missing": "yes" if data.get("fee_osago") == "no" else "no",
            "osago_period": data.get("fee_osago_period"),
            "heavy": data.get("fee_heavy"),
            "humanitarian": data.get("fee_humanitarian"),
            "animal": data.get("fee_animal"),
            "temp_overstay_days": data.get("fee_temp_overstay_days"),
            "delivery_overdue_days": data.get("fee_delivery_overdue_days"),
            "calculation_mode": data.get("fee_mode", "detailed"),
        }
        await state.clear()
        try:
            result_text = fee_calculator.build_message(payload, permit_service, settings.timezone, lang)
            metrics.increment("fee_checks")
            await answer_long(message, result_text, reply_markup=main_menu_keyboard(lang))
        except Exception:
            metrics.increment("errors")
            logger.exception("Fee calculation failed user_id=%s", message.from_user.id if message.from_user else None)
            await message.answer(t(lang, "technical_error"), reply_markup=main_menu_keyboard(lang))
        finally:
            metrics.observe("fee_check", perf_counter() - started)

    async def continue_fee_questions(message: Message, state: FSMContext, lang: str) -> None:
        data = await state.get_data()
        vehicle_country = country_by_code(str(data.get("fee_vehicle_country_code", "")))
        direction = str(data.get("fee_direction", ""))
        foreign_vehicle = bool(vehicle_country and vehicle_country.code != UZBEKISTAN_CODE)
        needs_rate = fee_rule_needs_rate(data)

        if (
            needs_rate
            and vehicle_country
            and vehicle_country.code in {TAJIKISTAN_CODE, TURKMENISTAN_CODE}
            and not data.get("fee_weight_category")
        ):
            await state.set_state(FeeCalcState.waiting_for_weight_category)
            await message.answer(
                t(lang, "ask_fee_weight"),
                reply_markup=simple_options_keyboard(
                    lang,
                    ["button_weight_up_to_10", "button_weight_10_20", "button_weight_over_20"],
                    columns=1,
                ),
            )
            return

        if (
            needs_rate
            and vehicle_country
            and is_eu_or_azerbaijan(vehicle_country.code)
            and not data.get("fee_stay_duration")
        ):
            await state.set_state(FeeCalcState.waiting_for_stay_duration)
            await message.answer(
                t(lang, "ask_fee_stay_duration"),
                reply_markup=simple_options_keyboard(lang, ["button_stay_up_to_14", "button_stay_over_14"], columns=1),
            )
            return

        if data.get("fee_mode") == "quick":
            await state.update_data(
                fee_declared="no",
                fee_transit_declaration="yes" if is_cargo_vehicle(data) and direction in {"entry", "transit"} else "no",
                fee_tinted="no",
                fee_osago="yes",
                fee_heavy="no",
                fee_humanitarian="no",
                fee_animal="no",
                fee_temp_overstay="no",
                fee_delivery_overdue="no",
            )
            await finish_fee_calculation(message, state, lang)
            return

        if is_cargo_vehicle(data) and not data.get("fee_declared"):
            await state.set_state(FeeCalcState.waiting_for_declaration)
            await message.answer(t(lang, "ask_fee_declaration"), reply_markup=yes_no_keyboard(lang))
            return

        if data.get("fee_declared") == "yes" and not data.get("fee_customs_value_usd"):
            await state.set_state(FeeCalcState.waiting_for_customs_value)
            await message.answer(t(lang, "ask_fee_customs_value"), reply_markup=cancel_keyboard(lang))
            return

        if not data.get("fee_tinted"):
            await state.set_state(FeeCalcState.waiting_for_tinted)
            await message.answer(t(lang, "ask_fee_tinted"), reply_markup=yes_no_keyboard(lang))
            return

        if foreign_vehicle and direction in {"entry", "transit"} and not data.get("fee_osago"):
            await state.set_state(FeeCalcState.waiting_for_osago)
            await message.answer(t(lang, "ask_fee_osago"), reply_markup=yes_no_keyboard(lang))
            return

        if foreign_vehicle and direction in {"entry", "transit"} and data.get("fee_osago") == "no" and not data.get("fee_osago_period"):
            await state.set_state(FeeCalcState.waiting_for_osago_period)
            await message.answer(
                t(lang, "ask_fee_osago_period"),
                reply_markup=simple_options_keyboard(lang, ["button_osago_15", "button_osago_1m", "button_osago_more"], columns=1),
            )
            return

        if is_cargo_vehicle(data) and not data.get("fee_heavy"):
            await state.set_state(FeeCalcState.waiting_for_heavy)
            await message.answer(t(lang, "ask_fee_heavy"), reply_markup=yes_no_keyboard(lang))
            return

        if is_cargo_vehicle(data) and not data.get("fee_humanitarian"):
            await state.set_state(FeeCalcState.waiting_for_humanitarian)
            await message.answer(t(lang, "ask_fee_humanitarian"), reply_markup=yes_no_keyboard(lang))
            return

        if is_cargo_vehicle(data) and not data.get("fee_animal"):
            await state.set_state(FeeCalcState.waiting_for_animal)
            await message.answer(t(lang, "ask_fee_animal"), reply_markup=yes_no_keyboard(lang))
            return

        if foreign_vehicle and direction == "exit" and not data.get("fee_temp_overstay"):
            await state.set_state(FeeCalcState.waiting_for_temp_overstay)
            await message.answer(t(lang, "ask_fee_temp_overstay"), reply_markup=yes_no_keyboard(lang))
            return

        if data.get("fee_temp_overstay") == "yes" and not data.get("fee_temp_overstay_days"):
            await state.set_state(FeeCalcState.waiting_for_temp_overstay_days)
            await message.answer(t(lang, "ask_fee_temp_overstay_days"), reply_markup=cancel_keyboard(lang))
            return

        if is_cargo_vehicle(data) and direction in {"transit", "exit"} and not data.get("fee_delivery_overdue"):
            await state.set_state(FeeCalcState.waiting_for_delivery_overdue)
            await message.answer(t(lang, "ask_fee_delivery_overdue"), reply_markup=yes_no_keyboard(lang))
            return

        if data.get("fee_delivery_overdue") == "yes" and not data.get("fee_delivery_overdue_days"):
            await state.set_state(FeeCalcState.waiting_for_delivery_overdue_days)
            await message.answer(t(lang, "ask_fee_delivery_overdue_days"), reply_markup=cancel_keyboard(lang))
            return

        await finish_fee_calculation(message, state, lang)

    async def continue_registration(message: Message, state: FSMContext) -> None:
        if not message.from_user:
            return

        profile = await user_storage.get_profile(message.from_user.id)
        if not profile or not profile.language_code:
            await state.clear()
            await ask_language(message)
            return
        lang = normalize_lang(profile.language_code)
        await state.clear()
        await message.answer(t(lang, "registered"), reply_markup=main_menu_keyboard(lang))

    @router.message(Command("start"))
    async def start(message: Message, state: FSMContext) -> None:
        metrics.increment("starts")
        await continue_registration(message, state)

    @router.message(Command("language"))
    async def language_command(message: Message) -> None:
        await ask_language(message)

    @router.message(F.text.in_(LANGUAGE_BUTTONS))
    async def language_button(message: Message) -> None:
        await ask_language(message)

    @router.message(Command("cancel"))
    async def cancel_command(message: Message, state: FSMContext) -> None:
        lang = await profile_lang(message.from_user.id if message.from_user else None)
        await state.clear()
        await message.answer(t(lang, "cancelled"), reply_markup=main_menu_keyboard(lang))

    @router.message(F.text.in_(CANCEL_BUTTONS))
    async def cancel_button(message: Message, state: FSMContext) -> None:
        await cancel_command(message, state)

    @router.callback_query(F.data.startswith("set_lang:"))
    async def set_language(callback: CallbackQuery, state: FSMContext) -> None:
        if not callback.from_user or not callback.message or not callback.data:
            return
        lang = normalize_lang(callback.data.split(":", 1)[1])
        await user_storage.set_language(callback.from_user.id, lang)
        await state.clear()
        await callback.answer(t(lang, "language_changed"))
        await callback.message.answer(
            t(lang, "language_saved"),
            reply_markup=main_menu_keyboard(lang),
        )

    @router.callback_query(F.data == "cancel_flow")
    async def cancel_flow(callback: CallbackQuery, state: FSMContext) -> None:
        lang = await profile_lang(callback.from_user.id if callback.from_user else None)
        await state.clear()
        await callback.answer()
        if callback.message:
            await callback.message.answer(t(lang, "cancelled"), reply_markup=main_menu_keyboard(lang))

    @router.message(Command("fees"))
    @router.message(F.text.in_(FEE_BUTTONS))
    async def ask_fee_vehicle_type(message: Message, state: FSMContext) -> None:
        if not message.from_user:
            return

        profile = await user_storage.get_profile(message.from_user.id)
        lang = normalize_lang(profile.language_code if profile else None)
        if not profile or not profile.is_registered:
            await continue_registration(message, state)
            return

        await state.clear()
        await state.set_state(FeeCalcState.waiting_for_mode)
        await message.answer(
            t(lang, "ask_fee_mode"),
            reply_markup=simple_options_keyboard(lang, ["button_fee_quick", "button_fee_detailed"], columns=1),
        )

    @router.message(StateFilter(FeeCalcState.waiting_for_mode))
    async def receive_fee_mode(message: Message, state: FSMContext) -> None:
        lang = await profile_lang(message.from_user.id if message.from_user else None)
        mode = button_value(lang, {"button_fee_quick": "quick", "button_fee_detailed": "detailed"}, message.text)
        if not mode:
            await message.answer(t(lang, "ask_fee_mode"))
            return
        await state.update_data(fee_mode=mode)
        await state.set_state(FeeCalcState.waiting_for_vehicle_type)
        await message.answer(
            t(lang, "ask_fee_vehicle_type"),
            reply_markup=simple_options_keyboard(
                lang,
                ["button_vehicle_light", "button_vehicle_bus", "button_vehicle_truck", "button_vehicle_trailer"],
                columns=2,
            ),
        )

    @router.message(StateFilter(FeeCalcState.waiting_for_vehicle_type))
    async def receive_fee_vehicle_type(message: Message, state: FSMContext) -> None:
        lang = await profile_lang(message.from_user.id if message.from_user else None)
        vehicle_type = button_value(
            lang,
            {
                "button_vehicle_light": "light",
                "button_vehicle_bus": "bus",
                "button_vehicle_truck": "truck",
                "button_vehicle_trailer": "truck_trailer",
            },
            message.text,
        )
        if not vehicle_type:
            await message.answer(t(lang, "ask_fee_vehicle_type"))
            return
        await state.update_data(fee_vehicle_type=vehicle_type)
        await state.set_state(FeeCalcState.waiting_for_vehicle_country)
        await message.answer(t(lang, "ask_fee_vehicle_country"), reply_markup=quick_country_keyboard("fee_vehicle", lang))

    @router.message(StateFilter(FeeCalcState.waiting_for_vehicle_country))
    async def receive_fee_vehicle_country(message: Message, state: FSMContext) -> None:
        lang = await profile_lang(message.from_user.id if message.from_user else None)
        await show_country_choices(message, lang, message.text or "", "fee_vehicle")

    @router.message(StateFilter(FeeCalcState.waiting_for_direction))
    async def receive_fee_direction(message: Message, state: FSMContext) -> None:
        lang = await profile_lang(message.from_user.id if message.from_user else None)
        direction = button_value(
            lang,
            {
                "button_direction_entry": "entry",
                "button_direction_transit": "transit",
                "button_direction_exit": "exit",
            },
            message.text,
        )
        if not direction:
            await message.answer(t(lang, "ask_fee_direction"))
            return
        await state.update_data(fee_direction=direction)
        data = await state.get_data()
        if is_cargo_vehicle(data):
            await state.set_state(FeeCalcState.waiting_for_origin_country)
            await message.answer(t(lang, "ask_fee_origin"), reply_markup=quick_country_keyboard("fee_origin", lang))
            return
        await continue_fee_questions(message, state, lang)

    @router.message(StateFilter(FeeCalcState.waiting_for_origin_country))
    async def receive_fee_origin_country(message: Message, state: FSMContext) -> None:
        lang = await profile_lang(message.from_user.id if message.from_user else None)
        await show_country_choices(message, lang, message.text or "", "fee_origin")

    @router.message(StateFilter(FeeCalcState.waiting_for_destination_country))
    async def receive_fee_destination_country(message: Message, state: FSMContext) -> None:
        lang = await profile_lang(message.from_user.id if message.from_user else None)
        await show_country_choices(message, lang, message.text or "", "fee_destination")

    @router.message(StateFilter(FeeCalcState.waiting_for_weight_category))
    async def receive_fee_weight(message: Message, state: FSMContext) -> None:
        lang = await profile_lang(message.from_user.id if message.from_user else None)
        weight = button_value(
            lang,
            {
                "button_weight_up_to_10": "up_to_10",
                "button_weight_10_20": "from_10_to_20",
                "button_weight_over_20": "over_20",
            },
            message.text,
        )
        if not weight:
            await message.answer(t(lang, "ask_fee_weight"))
            return
        await state.update_data(fee_weight_category=weight)
        await continue_fee_questions(message, state, lang)

    @router.message(StateFilter(FeeCalcState.waiting_for_stay_duration))
    async def receive_fee_stay_duration(message: Message, state: FSMContext) -> None:
        lang = await profile_lang(message.from_user.id if message.from_user else None)
        stay = button_value(
            lang,
            {"button_stay_up_to_14": "up_to_14", "button_stay_over_14": "over_14"},
            message.text,
        )
        if not stay:
            await message.answer(t(lang, "ask_fee_stay_duration"))
            return
        await state.update_data(fee_stay_duration=stay)
        await continue_fee_questions(message, state, lang)

    @router.message(StateFilter(FeeCalcState.waiting_for_declaration))
    async def receive_fee_declaration(message: Message, state: FSMContext) -> None:
        lang = await profile_lang(message.from_user.id if message.from_user else None)
        value = fee_yes_no_value(lang, message.text)
        if not value:
            await message.answer(t(lang, "ask_fee_declaration"), reply_markup=yes_no_keyboard(lang))
            return
        await state.update_data(fee_declared=value)
        await continue_fee_questions(message, state, lang)

    @router.message(StateFilter(FeeCalcState.waiting_for_customs_value))
    async def receive_fee_customs_value(message: Message, state: FSMContext) -> None:
        lang = await profile_lang(message.from_user.id if message.from_user else None)
        raw_value = (message.text or "").replace(" ", "").replace(",", ".")
        try:
            value = float(raw_value)
        except ValueError:
            await message.answer(t(lang, "invalid_number"))
            return
        if value <= 0:
            await message.answer(t(lang, "invalid_number"))
            return
        await state.update_data(fee_customs_value_usd=value)
        await continue_fee_questions(message, state, lang)

    @router.message(StateFilter(FeeCalcState.waiting_for_transit_declaration))
    async def receive_fee_transit_declaration(message: Message, state: FSMContext) -> None:
        lang = await profile_lang(message.from_user.id if message.from_user else None)
        value = fee_yes_no_value(lang, message.text)
        if not value:
            await message.answer(t(lang, "ask_fee_transit_declaration"), reply_markup=yes_no_keyboard(lang))
            return
        await state.update_data(fee_transit_declaration=value)
        await continue_fee_questions(message, state, lang)

    @router.message(StateFilter(FeeCalcState.waiting_for_tinted))
    async def receive_fee_tinted(message: Message, state: FSMContext) -> None:
        lang = await profile_lang(message.from_user.id if message.from_user else None)
        value = fee_yes_no_value(lang, message.text)
        if not value:
            await message.answer(t(lang, "ask_fee_tinted"), reply_markup=yes_no_keyboard(lang))
            return
        await state.update_data(fee_tinted=value)
        await continue_fee_questions(message, state, lang)

    @router.message(StateFilter(FeeCalcState.waiting_for_osago))
    async def receive_fee_osago(message: Message, state: FSMContext) -> None:
        lang = await profile_lang(message.from_user.id if message.from_user else None)
        value = fee_yes_no_value(lang, message.text)
        if not value:
            await message.answer(t(lang, "ask_fee_osago"), reply_markup=yes_no_keyboard(lang))
            return
        await state.update_data(fee_osago=value)
        await continue_fee_questions(message, state, lang)

    @router.message(StateFilter(FeeCalcState.waiting_for_osago_period))
    async def receive_fee_osago_period(message: Message, state: FSMContext) -> None:
        lang = await profile_lang(message.from_user.id if message.from_user else None)
        period = button_value(
            lang,
            {"button_osago_15": "up_to_15", "button_osago_1m": "one_month", "button_osago_more": "over_one_month"},
            message.text,
        )
        if not period:
            await message.answer(t(lang, "ask_fee_osago_period"))
            return
        await state.update_data(fee_osago_period=period)
        await continue_fee_questions(message, state, lang)

    @router.message(StateFilter(FeeCalcState.waiting_for_heavy))
    async def receive_fee_heavy(message: Message, state: FSMContext) -> None:
        lang = await profile_lang(message.from_user.id if message.from_user else None)
        value = fee_yes_no_value(lang, message.text)
        if not value:
            await message.answer(t(lang, "ask_fee_heavy"), reply_markup=yes_no_keyboard(lang))
            return
        await state.update_data(fee_heavy=value)
        await continue_fee_questions(message, state, lang)

    @router.message(StateFilter(FeeCalcState.waiting_for_humanitarian))
    async def receive_fee_humanitarian(message: Message, state: FSMContext) -> None:
        lang = await profile_lang(message.from_user.id if message.from_user else None)
        value = fee_yes_no_value(lang, message.text)
        if not value:
            await message.answer(t(lang, "ask_fee_humanitarian"), reply_markup=yes_no_keyboard(lang))
            return
        await state.update_data(fee_humanitarian=value)
        await continue_fee_questions(message, state, lang)

    @router.message(StateFilter(FeeCalcState.waiting_for_animal))
    async def receive_fee_animal(message: Message, state: FSMContext) -> None:
        lang = await profile_lang(message.from_user.id if message.from_user else None)
        value = fee_yes_no_value(lang, message.text)
        if not value:
            await message.answer(t(lang, "ask_fee_animal"), reply_markup=yes_no_keyboard(lang))
            return
        await state.update_data(fee_animal=value)
        await continue_fee_questions(message, state, lang)

    @router.message(StateFilter(FeeCalcState.waiting_for_temp_overstay))
    async def receive_fee_temp_overstay(message: Message, state: FSMContext) -> None:
        lang = await profile_lang(message.from_user.id if message.from_user else None)
        value = fee_yes_no_value(lang, message.text)
        if not value:
            await message.answer(t(lang, "ask_fee_temp_overstay"), reply_markup=yes_no_keyboard(lang))
            return
        await state.update_data(fee_temp_overstay=value)
        await continue_fee_questions(message, state, lang)

    @router.message(StateFilter(FeeCalcState.waiting_for_temp_overstay_days))
    async def receive_fee_temp_overstay_days(message: Message, state: FSMContext) -> None:
        lang = await profile_lang(message.from_user.id if message.from_user else None)
        raw_value = (message.text or "").strip()
        if not raw_value.isdigit() or int(raw_value) <= 0:
            await message.answer(t(lang, "invalid_number"))
            return
        await state.update_data(fee_temp_overstay_days=int(raw_value))
        await continue_fee_questions(message, state, lang)

    @router.message(StateFilter(FeeCalcState.waiting_for_delivery_overdue))
    async def receive_fee_delivery_overdue(message: Message, state: FSMContext) -> None:
        lang = await profile_lang(message.from_user.id if message.from_user else None)
        value = fee_yes_no_value(lang, message.text)
        if not value:
            await message.answer(t(lang, "ask_fee_delivery_overdue"), reply_markup=yes_no_keyboard(lang))
            return
        await state.update_data(fee_delivery_overdue=value)
        await continue_fee_questions(message, state, lang)

    @router.message(StateFilter(FeeCalcState.waiting_for_delivery_overdue_days))
    async def receive_fee_delivery_overdue_days(message: Message, state: FSMContext) -> None:
        lang = await profile_lang(message.from_user.id if message.from_user else None)
        raw_value = (message.text or "").strip()
        if not raw_value.isdigit() or int(raw_value) <= 0:
            await message.answer(t(lang, "invalid_number"))
            return
        await state.update_data(fee_delivery_overdue_days=int(raw_value))
        await continue_fee_questions(message, state, lang)

    @router.message(Command("check"))
    @router.message(F.text.in_(CHECK_BUTTONS))
    async def ask_route_origin(message: Message, state: FSMContext) -> None:
        if not message.from_user:
            return

        profile = await user_storage.get_profile(message.from_user.id)
        lang = normalize_lang(profile.language_code if profile else None)
        if not profile or not profile.is_registered:
            await continue_registration(message, state)
            return

        await state.set_state(CheckState.waiting_for_origin_country)
        await message.answer(
            t(lang, "ask_origin_country"),
            reply_markup=quick_country_keyboard("origin", lang),
        )

    @router.message(StateFilter(CheckState.waiting_for_origin_country))
    async def receive_origin_country(message: Message, state: FSMContext) -> None:
        lang = await profile_lang(message.from_user.id if message.from_user else None)
        raw_country = message.text or ""
        await show_country_choices(message, lang, raw_country, "origin")

    @router.message(StateFilter(CheckState.waiting_for_destination_country))
    async def receive_destination_country(message: Message, state: FSMContext) -> None:
        lang = await profile_lang(message.from_user.id if message.from_user else None)
        raw_country = message.text or ""
        await show_country_choices(message, lang, raw_country, "destination")

    @router.message(StateFilter(CheckState.waiting_for_vehicle_country))
    async def receive_vehicle_country(message: Message, state: FSMContext) -> None:
        lang = await profile_lang(message.from_user.id if message.from_user else None)
        raw_country = message.text or ""
        await show_country_choices(message, lang, raw_country, "vehicle")

    @router.callback_query(F.data.startswith("pick_country:"))
    async def pick_country(callback: CallbackQuery, state: FSMContext) -> None:
        if not callback.from_user or not callback.message or not callback.data:
            return
        parts = callback.data.split(":")
        if len(parts) != 3:
            return
        _, slot, code = parts
        country = country_by_code(code)
        lang = await profile_lang(callback.from_user.id)
        if not country:
            await callback.answer(t(lang, "route_session_expired"), show_alert=True)
            return

        await callback.answer(country_label(country, lang))
        if slot == "origin":
            await state.update_data(origin_country_code=country.code)
            await state.set_state(CheckState.waiting_for_destination_country)
            await callback.message.answer(t(lang, "ask_destination_country"), reply_markup=quick_country_keyboard("destination", lang))
            return
        if slot == "destination":
            await state.update_data(destination_country_code=country.code)
            await state.set_state(CheckState.waiting_for_vehicle_country)
            await callback.message.answer(t(lang, "ask_vehicle_country"), reply_markup=quick_country_keyboard("vehicle", lang))
            return
        if slot == "vehicle":
            await evaluate_route(callback.message, state, lang, country.code, user_id=callback.from_user.id)
            return
        if slot == "fee_vehicle":
            await state.update_data(fee_vehicle_country_code=country.code)
            await state.set_state(FeeCalcState.waiting_for_direction)
            await callback.message.answer(
                t(lang, "ask_fee_direction"),
                reply_markup=simple_options_keyboard(
                    lang,
                    ["button_direction_entry", "button_direction_transit", "button_direction_exit"],
                    columns=1,
                ),
            )
            return
        if slot == "fee_origin":
            await state.update_data(fee_origin_country_code=country.code)
            await state.set_state(FeeCalcState.waiting_for_destination_country)
            await callback.message.answer(t(lang, "ask_fee_destination"), reply_markup=quick_country_keyboard("fee_destination", lang))
            return
        if slot == "fee_destination":
            await state.update_data(fee_destination_country_code=country.code)
            await continue_fee_questions(callback.message, state, lang)
            return

    @router.message(Command("help"))
    async def help_command(message: Message) -> None:
        lang = await profile_lang(message.from_user.id if message.from_user else None)
        await message.answer(
            t(lang, "help"),
            reply_markup=main_menu_keyboard(lang),
        )

    @router.message()
    async def fallback(message: Message, state: FSMContext) -> None:
        if not message.from_user:
            return
        profile = await user_storage.get_profile(message.from_user.id)
        if not profile or not profile.is_registered:
            await continue_registration(message, state)
            return
        lang = normalize_lang(profile.language_code)
        if message.text:
            await state.set_state(CheckState.waiting_for_origin_country)
            await show_country_choices(message, lang, message.text, "origin")
            return
        await message.answer(t(lang, "fallback"), reply_markup=main_menu_keyboard(lang))

    return router
