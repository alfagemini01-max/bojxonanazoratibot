from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

CONTACT_BUTTON = "📱 Telefon raqamni yuborish"
ACCEPT_TERMS_BUTTON = "✅ Shartlarga roziman"
CHECK_BUTTON = "🔎 Tekshirish"
TERMS_BUTTON = "📄 Foydalanish shartlari"
CANCEL_BUTTON = "Bekor qilish"


def contact_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=CONTACT_BUTTON, request_contact=True)],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Telefon raqamingizni yuboring",
    )


def terms_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=ACCEPT_TERMS_BUTTON, callback_data="accept_terms")],
        ]
    )


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=CHECK_BUTTON)],
            [KeyboardButton(text=TERMS_BUTTON)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Kerakli bo‘limni tanlang",
    )


def cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=CANCEL_BUTTON)]],
        resize_keyboard=True,
    )
