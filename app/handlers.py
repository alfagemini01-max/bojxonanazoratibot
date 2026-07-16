from __future__ import annotations

import asyncio
import html
import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramNetworkError
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from app.config import Settings
from app.i18n import LANGUAGES, button_texts, normalize_lang, t
from app.services.permit import PermitRuleService, build_permit_message, country_label
from app.states import CheckState, RegistrationState
from app.storage import UserStorage

logger = logging.getLogger(__name__)

CHECK_BUTTONS = button_texts("button_check")
TERMS_BUTTONS = button_texts("button_terms")
LANGUAGE_BUTTONS = button_texts("button_language")
CANCEL_BUTTONS = button_texts("button_cancel")


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label, callback_data=f"set_lang:{code}")]
            for code, label in LANGUAGES.items()
        ]
    )


def contact_keyboard(lang: str = "uz") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t(lang, "button_contact"), request_contact=True)],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder=t(lang, "contact_placeholder"),
    )


def terms_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "button_accept_terms"), callback_data="accept_terms")],
        ]
    )


def main_menu_keyboard(lang: str = "uz") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t(lang, "button_check"))],
            [KeyboardButton(text=t(lang, "button_terms"))],
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


def country_choices_keyboard(matches, slot: str, lang: str = "uz") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{country_label(match.country, lang)} ({match.country.code})",
                    callback_data=f"pick_country:{slot}:{match.country.code}",
                )
            ]
            for match in matches
        ]
    )


def build_router(user_storage: UserStorage, settings: Settings) -> Router:
    router = Router(name="nazoratbot")
    terms_photo_file_id = settings.terms_photo_file_id
    permit_service = PermitRuleService(settings.permission_rules_path)

    async def profile_lang(user_id: int | None) -> str:
        if user_id is None:
            return "uz"
        profile = await user_storage.get_profile(user_id)
        return normalize_lang(profile.language_code if profile else None)

    async def ask_language(message: Message) -> None:
        await message.answer(t("uz", "choose_language"), reply_markup=language_keyboard())

    async def send_safely(send_action, *, retries: int = 2):
        for attempt in range(retries + 1):
            try:
                return await send_action()
            except TelegramNetworkError as exc:
                if attempt >= retries:
                    logger.warning("Telegram message was not sent after retries: %s", exc)
                    return None
                await asyncio.sleep(1 + attempt)
        return None

    async def save_telegram_user(message: Message) -> None:
        if not message.from_user:
            return
        await user_storage.upsert_telegram_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.full_name,
        )

    async def send_terms(message: Message, show_accept_button: bool = True, lang: str | None = None) -> None:
        nonlocal terms_photo_file_id
        lang = normalize_lang(lang) if lang else await profile_lang(message.from_user.id if message.from_user else None)
        reply_markup = terms_keyboard(lang) if show_accept_button else None
        caption = t(lang, "terms_caption")

        if terms_photo_file_id or settings.terms_image_path.exists():
            photo = terms_photo_file_id or FSInputFile(settings.terms_image_path)
            sent_message = await send_safely(
                lambda: message.answer_photo(
                    photo,
                    caption=caption,
                    reply_markup=reply_markup,
                )
            )
            if not terms_photo_file_id and sent_message and sent_message.photo:
                terms_photo_file_id = sent_message.photo[-1].file_id
                logger.info("Terms photo file_id cached: %s", terms_photo_file_id)
            return

        if settings.terms_pdf_path.exists():
            await send_safely(
                lambda: message.answer_document(
                    FSInputFile(settings.terms_pdf_path),
                    caption=caption,
                    reply_markup=reply_markup,
                )
            )
            return

        await send_safely(
            lambda: message.answer(
                caption
                + "\n\n"
                + t(lang, "terms_missing", path=settings.terms_image_path.as_posix()),
                reply_markup=reply_markup,
            )
        )

    async def process_contact(message: Message, state: FSMContext) -> None:
        if not message.from_user or not message.contact:
            return
        await save_telegram_user(message)

        if message.contact.user_id and message.contact.user_id != message.from_user.id:
            lang = await profile_lang(message.from_user.id)
            await message.answer(t(lang, "wrong_contact"))
            return

        await user_storage.set_phone(message.from_user.id, message.contact.phone_number)
        logger.info("Contact saved for user_id=%s", message.from_user.id)
        await state.clear()
        profile = await user_storage.get_profile(message.from_user.id)
        lang = normalize_lang(profile.language_code if profile else None)
        if profile and profile.terms_accepted_at:
            await message.answer(
                t(lang, "contact_updated"),
                reply_markup=main_menu_keyboard(lang),
            )
            return
        await message.answer(t(lang, "contact_saved"), reply_markup=ReplyKeyboardRemove())
        await send_terms(message, show_accept_button=True, lang=lang)

    async def answer_country_not_found(message: Message, lang: str, raw_country: str) -> None:
        await message.answer(
            t(lang, "country_no_match", country=html.escape(raw_country.strip())),
            reply_markup=cancel_keyboard(lang),
        )

    async def show_country_choices(message: Message, lang: str, raw_country: str, slot: str) -> None:
        matches = permit_service.search_countries(raw_country, threshold=0.75, limit=8)
        if not matches:
            await answer_country_not_found(message, lang, raw_country)
            return
        await message.answer(
            t(lang, "country_choose"),
            reply_markup=country_choices_keyboard(matches, slot, lang),
        )

    async def evaluate_route(message: Message, state: FSMContext, lang: str, vehicle_country_code: str, user_id: int | None = None) -> None:
        data = await state.get_data()
        origin = permit_service.find_country(str(data.get("origin_country_code", "")))
        destination = permit_service.find_country(str(data.get("destination_country_code", "")))
        vehicle_country = permit_service.find_country(vehicle_country_code)
        if not origin or not destination or not vehicle_country:
            await state.clear()
            await message.answer(t(lang, "route_session_expired"), reply_markup=main_menu_keyboard(lang))
            return

        result = permit_service.evaluate(origin, destination, vehicle_country)
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
        await message.answer(
            build_permit_message(result, settings.timezone, lang),
            reply_markup=main_menu_keyboard(lang),
        )

    async def continue_registration(message: Message, state: FSMContext) -> None:
        if not message.from_user:
            return

        await save_telegram_user(message)
        profile = await user_storage.get_profile(message.from_user.id)

        if not profile or not profile.language_code:
            await state.clear()
            await ask_language(message)
            return

        lang = normalize_lang(profile.language_code)
        if profile and profile.is_registered:
            await state.clear()
            await message.answer(
                t(lang, "registered"),
                reply_markup=main_menu_keyboard(lang),
            )
            return

        if not profile or not profile.full_name:
            await state.set_state(RegistrationState.waiting_for_name)
            await message.answer(
                t(lang, "ask_name"),
                reply_markup=ReplyKeyboardRemove(),
            )
            return

        if not profile.phone:
            await state.set_state(RegistrationState.waiting_for_contact)
            await message.answer(
                t(lang, "ask_contact"),
                reply_markup=contact_keyboard(lang),
            )
            return

        await state.clear()
        await send_terms(message, show_accept_button=True)

    @router.message(Command("start"))
    async def start(message: Message, state: FSMContext) -> None:
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
        await user_storage.upsert_telegram_user(
            callback.from_user.id,
            callback.from_user.username,
            callback.from_user.full_name,
        )
        await user_storage.set_language(callback.from_user.id, lang)
        await callback.answer(t(lang, "language_changed"))
        await callback.message.answer(t(lang, "language_saved"), reply_markup=ReplyKeyboardRemove())

        profile = await user_storage.get_profile(callback.from_user.id)
        if profile and profile.is_registered:
            await state.clear()
            await callback.message.answer(t(lang, "registered"), reply_markup=main_menu_keyboard(lang))
        elif not profile or not profile.full_name:
            await state.set_state(RegistrationState.waiting_for_name)
            await callback.message.answer(t(lang, "ask_name"), reply_markup=ReplyKeyboardRemove())
        elif not profile.phone:
            await state.set_state(RegistrationState.waiting_for_contact)
            await callback.message.answer(t(lang, "ask_contact"), reply_markup=contact_keyboard(lang))
        else:
            await state.clear()
            await send_terms(callback.message, show_accept_button=True, lang=lang)

    @router.message(StateFilter(RegistrationState.waiting_for_name))
    async def receive_name(message: Message, state: FSMContext) -> None:
        if not message.from_user:
            return
        await save_telegram_user(message)
        lang = await profile_lang(message.from_user.id)
        name = (message.text or "").strip()
        if len(name) < 2:
            await message.answer(t(lang, "short_name"))
            return

        await user_storage.set_full_name(message.from_user.id, name)
        await state.set_state(RegistrationState.waiting_for_contact)
        await message.answer(
            t(lang, "ask_contact_after_name"),
            reply_markup=contact_keyboard(lang),
        )

    @router.message(StateFilter(RegistrationState.waiting_for_contact), F.contact)
    async def receive_contact(message: Message, state: FSMContext) -> None:
        await process_contact(message, state)

    @router.message(F.contact)
    async def receive_contact_without_state(message: Message, state: FSMContext) -> None:
        await process_contact(message, state)

    @router.message(StateFilter(RegistrationState.waiting_for_contact))
    async def contact_expected(message: Message) -> None:
        lang = await profile_lang(message.from_user.id if message.from_user else None)
        await message.answer(
            t(lang, "contact_expected"),
            reply_markup=contact_keyboard(lang),
        )

    @router.callback_query(F.data == "accept_terms")
    async def accept_terms(callback: CallbackQuery, state: FSMContext) -> None:
        if not callback.from_user or not callback.message:
            return

        await user_storage.upsert_telegram_user(
            callback.from_user.id,
            callback.from_user.username,
            callback.from_user.full_name,
        )
        profile = await user_storage.get_profile(callback.from_user.id)
        lang = normalize_lang(profile.language_code if profile else None)
        if not profile or not profile.full_name or not profile.phone:
            await callback.answer(t(lang, "accept_first"), show_alert=True)
            await state.set_state(RegistrationState.waiting_for_name)
            await callback.message.answer(t(lang, "ask_name"), reply_markup=ReplyKeyboardRemove())
            return

        accepted_at = await user_storage.accept_terms(callback.from_user.id)
        await state.clear()
        await callback.answer(t(lang, "accept_terms_answer"))
        await callback.message.answer(
            t(lang, "terms_accepted", accepted_at=accepted_at),
            reply_markup=main_menu_keyboard(lang),
        )

    @router.message(Command("terms"))
    @router.message(F.text.in_(TERMS_BUTTONS))
    async def terms(message: Message) -> None:
        if not message.from_user:
            return
        profile = await user_storage.get_profile(message.from_user.id)
        lang = normalize_lang(profile.language_code if profile else None)
        await send_terms(message, show_accept_button=not bool(profile and profile.terms_accepted_at), lang=lang)

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
            reply_markup=cancel_keyboard(lang),
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
        country = permit_service.country_by_code(code)
        lang = await profile_lang(callback.from_user.id)
        if not country:
            await callback.answer(t(lang, "route_session_expired"), show_alert=True)
            return

        await callback.answer(country_label(country, lang))
        if slot == "origin":
            await state.update_data(origin_country_code=country.code)
            await state.set_state(CheckState.waiting_for_destination_country)
            await callback.message.answer(t(lang, "ask_destination_country"), reply_markup=cancel_keyboard(lang))
            return
        if slot == "destination":
            await state.update_data(destination_country_code=country.code)
            await state.set_state(CheckState.waiting_for_vehicle_country)
            await callback.message.answer(t(lang, "ask_vehicle_country"), reply_markup=cancel_keyboard(lang))
            return
        if slot == "vehicle":
            await evaluate_route(callback.message, state, lang, country.code, user_id=callback.from_user.id)
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
        await message.answer(t(lang, "fallback"), reply_markup=main_menu_keyboard(lang))

    return router
