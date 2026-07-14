from __future__ import annotations

import asyncio
import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramNetworkError
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message, ReplyKeyboardRemove

from app.config import Settings
from app.keyboards import (
    CANCEL_BUTTON,
    CHECK_BUTTON,
    TERMS_BUTTON,
    cancel_keyboard,
    contact_keyboard,
    main_menu_keyboard,
    terms_keyboard,
)
from app.repositories.base import VehicleRepository
from app.services.message_templates import build_not_found_message, build_vehicle_message
from app.services.plate import looks_like_plate, normalize_plate
from app.states import CheckState, RegistrationState
from app.storage import UserStorage

logger = logging.getLogger(__name__)


def build_router(user_storage: UserStorage, vehicle_repository: VehicleRepository, settings: Settings) -> Router:
    router = Router(name="nazoratbot")

    async def send_safely(send_action, *, retries: int = 2) -> bool:
        for attempt in range(retries + 1):
            try:
                await send_action()
                return True
            except TelegramNetworkError as exc:
                if attempt >= retries:
                    logger.warning("Telegram message was not sent after retries: %s", exc)
                    return False
                await asyncio.sleep(1 + attempt)
        return False

    async def save_telegram_user(message: Message) -> None:
        if not message.from_user:
            return
        await user_storage.upsert_telegram_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.full_name,
        )

    async def send_terms(message: Message, show_accept_button: bool = True) -> None:
        reply_markup = terms_keyboard() if show_accept_button else None
        caption = (
            "📄 Foydalanish shartlari bilan tanishing.\n\n"
            "Botdan foydalanishni davom ettirish uchun shartlarga rozilik bildirish talab etiladi."
        )

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
                + "Hozircha PDF fayl joylanmagan. Keyinchalik foydalanish shartlari "
                + f"<code>{settings.terms_pdf_path.as_posix()}</code> manziliga qo'yiladi.",
                reply_markup=reply_markup,
            )
        )

    async def process_contact(message: Message, state: FSMContext) -> None:
        if not message.from_user or not message.contact:
            return
        await save_telegram_user(message)

        if message.contact.user_id and message.contact.user_id != message.from_user.id:
            await message.answer("Iltimos, o'zingizning Telegram kontakt raqamingizni yuboring.")
            return

        await user_storage.set_phone(message.from_user.id, message.contact.phone_number)
        logger.info("Contact saved for user_id=%s", message.from_user.id)
        await state.clear()
        profile = await user_storage.get_profile(message.from_user.id)
        if profile and profile.terms_accepted_at:
            await message.answer(
                "Telefon raqamingiz yangilandi.\n\nKerakli amalni tanlang.",
                reply_markup=main_menu_keyboard(),
            )
            return
        await message.answer("Telefon raqamingiz qabul qilindi.", reply_markup=ReplyKeyboardRemove())
        await send_terms(message, show_accept_button=True)

    async def process_plate(message: Message, state: FSMContext) -> None:
        raw_plate = message.text or ""
        if not looks_like_plate(raw_plate):
            await message.answer(
                "Davlat raqami noto'g'ri ko'rinishda yuborildi. Iltimos, qayta kiriting.\n"
                "Masalan: <code>01A123BB</code>",
                reply_markup=cancel_keyboard(),
            )
            return

        plate = normalize_plate(raw_plate)
        logger.info("Vehicle check requested by user_id=%s plate=%s", message.from_user.id if message.from_user else None, plate)
        record = await vehicle_repository.find_by_plate(plate)

        if record is None:
            await message.answer(
                build_not_found_message(plate, settings.timezone),
                reply_markup=main_menu_keyboard(),
            )
        else:
            await message.answer(
                build_vehicle_message(record, settings.timezone),
                reply_markup=main_menu_keyboard(),
            )
        await state.clear()

    async def continue_registration(message: Message, state: FSMContext) -> None:
        if not message.from_user:
            return

        await save_telegram_user(message)
        profile = await user_storage.get_profile(message.from_user.id)

        if profile and profile.is_registered:
            await state.clear()
            await message.answer(
                "✅ Ro'yxatdan o'tish yakunlangan.\n\n"
                "Kerakli amalni tanlang.",
                reply_markup=main_menu_keyboard(),
            )
            return

        if not profile or not profile.full_name:
            await state.set_state(RegistrationState.waiting_for_name)
            await message.answer(
                "Assalomu alaykum.\n\n"
                "Botdan foydalanish uchun avval ismingizni kiriting.",
                reply_markup=ReplyKeyboardRemove(),
            )
            return

        if not profile.phone:
            await state.set_state(RegistrationState.waiting_for_contact)
            await message.answer(
                "📱 Telefon raqamingizni Telegram orqali yuboring.",
                reply_markup=contact_keyboard(),
            )
            return

        await state.clear()
        await send_terms(message, show_accept_button=True)

    @router.message(Command("start"))
    async def start(message: Message, state: FSMContext) -> None:
        await continue_registration(message, state)

    @router.message(Command("cancel"))
    async def cancel_command(message: Message, state: FSMContext) -> None:
        await state.clear()
        await message.answer("Amal bekor qilindi.", reply_markup=main_menu_keyboard())

    @router.message(F.text == CANCEL_BUTTON)
    async def cancel_button(message: Message, state: FSMContext) -> None:
        await cancel_command(message, state)

    @router.message(StateFilter(RegistrationState.waiting_for_name))
    async def receive_name(message: Message, state: FSMContext) -> None:
        if not message.from_user:
            return
        await save_telegram_user(message)
        name = (message.text or "").strip()
        if len(name) < 2:
            await message.answer("Iltimos, ismingizni to'liqroq kiriting.")
            return

        await user_storage.set_full_name(message.from_user.id, name)
        await state.set_state(RegistrationState.waiting_for_contact)
        await message.answer(
            "Rahmat. Endi telefon raqamingizni yuboring.",
            reply_markup=contact_keyboard(),
        )

    @router.message(StateFilter(RegistrationState.waiting_for_contact), F.contact)
    async def receive_contact(message: Message, state: FSMContext) -> None:
        await process_contact(message, state)

    @router.message(F.contact)
    async def receive_contact_without_state(message: Message, state: FSMContext) -> None:
        await process_contact(message, state)

    @router.message(StateFilter(RegistrationState.waiting_for_contact))
    async def contact_expected(message: Message) -> None:
        await message.answer(
            "Telefon raqamni pastdagi maxsus tugma orqali yuboring.",
            reply_markup=contact_keyboard(),
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
        if not profile or not profile.full_name or not profile.phone:
            await callback.answer("Avval ro'yxatdan o'tishni yakunlang.", show_alert=True)
            await state.set_state(RegistrationState.waiting_for_name)
            await callback.message.answer("Iltimos, ismingizni kiriting.", reply_markup=ReplyKeyboardRemove())
            return

        accepted_at = await user_storage.accept_terms(callback.from_user.id)
        await state.clear()
        await callback.answer("Rozilik qabul qilindi.")
        await callback.message.answer(
            "✅ Foydalanish shartlariga roziligingiz saqlandi.\n"
            f"🕘 Rozilik vaqti: <code>{accepted_at}</code>\n\n"
            "Endi transport vositasi bo'yicha tekshiruvdan foydalanishingiz mumkin.",
            reply_markup=main_menu_keyboard(),
        )

    @router.message(Command("terms"))
    @router.message(F.text == TERMS_BUTTON)
    async def terms(message: Message) -> None:
        if not message.from_user:
            return
        profile = await user_storage.get_profile(message.from_user.id)
        await send_terms(message, show_accept_button=not bool(profile and profile.terms_accepted_at))

    @router.message(F.text == CHECK_BUTTON)
    async def ask_plate(message: Message, state: FSMContext) -> None:
        if not message.from_user:
            return

        profile = await user_storage.get_profile(message.from_user.id)
        if not profile or not profile.is_registered:
            await continue_registration(message, state)
            return

        await state.set_state(CheckState.waiting_for_plate)
        await message.answer(
            "🚘 Tekshiriladigan transport vositasining davlat raqamini yuboring.\n"
            "Masalan: <code>01A123BB</code>",
            reply_markup=cancel_keyboard(),
        )

    @router.message(StateFilter(CheckState.waiting_for_plate))
    async def check_plate(message: Message, state: FSMContext) -> None:
        await process_plate(message, state)

    @router.message(Command("help"))
    async def help_command(message: Message) -> None:
        await message.answer(
            "Bot transport vositasi davlat raqami bo'yicha bojxona nazoratidagi hujjatlarni tekshiradi.\n\n"
            "Tekshiruv uchun menyudan <b>Tekshirish</b> tugmasini tanlang.",
            reply_markup=main_menu_keyboard(),
        )

    @router.message()
    async def fallback(message: Message, state: FSMContext) -> None:
        if not message.from_user:
            return
        profile = await user_storage.get_profile(message.from_user.id)
        if not profile or not profile.is_registered:
            await continue_registration(message, state)
            return
        if message.text and looks_like_plate(message.text):
            await process_plate(message, state)
            return
        await message.answer("Kerakli amalni menyudan tanlang.", reply_markup=main_menu_keyboard())

    return router
