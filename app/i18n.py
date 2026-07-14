from __future__ import annotations


DEFAULT_LANG = "uz"
LANGUAGES = {
    "uz": "🇺🇿 O'zbek",
    "ru": "🇷🇺 Русский",
    "en": "🇬🇧 English",
}


TEXTS = {
    "uz": {
        "choose_language": "🌐 Iltimos, bot tilini tanlang.",
        "language_saved": "✅ Til tanlandi: O'zbek.",
        "language_changed": "✅ Til sozlamasi yangilandi.",
        "ask_name": "Assalomu alaykum.\n\nBotdan foydalanish uchun avval ismingizni kiriting.",
        "short_name": "Iltimos, ismingizni to'liqroq kiriting.",
        "ask_contact_after_name": "Rahmat. Endi telefon raqamingizni yuboring.",
        "ask_contact": "📱 Telefon raqamingizni Telegram orqali yuboring.",
        "contact_expected": "Telefon raqamni pastdagi maxsus tugma orqali yuboring.",
        "wrong_contact": "Iltimos, o'zingizning Telegram kontakt raqamingizni yuboring.",
        "contact_saved": "Telefon raqamingiz qabul qilindi.",
        "contact_updated": "Telefon raqamingiz yangilandi.\n\nKerakli amalni tanlang.",
        "registered": "✅ Ro'yxatdan o'tish yakunlangan.\n\nKerakli amalni tanlang.",
        "terms_caption": "📄 Foydalanish shartlari bilan tanishing.\n\nBotdan foydalanishni davom ettirish uchun shartlarga rozilik bildirish talab etiladi.",
        "terms_missing": "Hozircha foydalanish shartlari rasmi joylanmagan. Keyinchalik fayl <code>{path}</code> manziliga qo'yiladi.",
        "accept_first": "Avval ro'yxatdan o'tishni yakunlang.",
        "accept_terms_answer": "Rozilik qabul qilindi.",
        "terms_accepted": "✅ Foydalanish shartlariga roziligingiz saqlandi.\n🕘 Rozilik vaqti: <code>{accepted_at}</code>\n\nEndi transport vositasi bo'yicha tekshiruvdan foydalanishingiz mumkin.",
        "ask_plate": "🚘 Tekshiriladigan transport vositasining davlat raqamini yuboring.\nMasalan: <code>01A123BB</code>",
        "bad_plate": "Davlat raqami noto'g'ri ko'rinishda yuborildi. Iltimos, qayta kiriting.\nMasalan: <code>01A123BB</code>",
        "help": "Bot transport vositasi davlat raqami bo'yicha bojxona nazoratidagi hujjatlarni tekshiradi.\n\nTekshiruv uchun menyudan <b>Tekshirish</b> tugmasini tanlang.",
        "fallback": "Kerakli amalni menyudan tanlang.",
        "cancelled": "Amal bekor qilindi.",
        "button_contact": "📱 Telefon raqamni yuborish",
        "button_accept_terms": "✅ Shartlarga roziman",
        "button_check": "🔎 Tekshirish",
        "button_terms": "📄 Foydalanish shartlari",
        "button_language": "🌐 Tilni o'zgartirish",
        "button_cancel": "Bekor qilish",
        "menu_placeholder": "Kerakli bo'limni tanlang",
        "contact_placeholder": "Telefon raqamingizni yuboring",
    },
    "ru": {
        "choose_language": "🌐 Пожалуйста, выберите язык бота.",
        "language_saved": "✅ Язык выбран: русский.",
        "language_changed": "✅ Настройка языка обновлена.",
        "ask_name": "Здравствуйте.\n\nДля использования бота сначала введите ваше имя.",
        "short_name": "Пожалуйста, введите имя более полно.",
        "ask_contact_after_name": "Спасибо. Теперь отправьте номер телефона.",
        "ask_contact": "📱 Отправьте номер телефона через Telegram.",
        "contact_expected": "Отправьте номер телефона с помощью специальной кнопки ниже.",
        "wrong_contact": "Пожалуйста, отправьте именно свой Telegram-контакт.",
        "contact_saved": "Ваш номер телефона принят.",
        "contact_updated": "Ваш номер телефона обновлен.\n\nВыберите нужное действие.",
        "registered": "✅ Регистрация завершена.\n\nВыберите нужное действие.",
        "terms_caption": "📄 Ознакомьтесь с условиями использования.\n\nДля продолжения работы с ботом необходимо подтвердить согласие с условиями.",
        "terms_missing": "Изображение с условиями использования пока не размещено. Позже файл будет размещен по адресу <code>{path}</code>.",
        "accept_first": "Сначала завершите регистрацию.",
        "accept_terms_answer": "Согласие принято.",
        "terms_accepted": "✅ Ваше согласие с условиями использования сохранено.\n🕘 Время согласия: <code>{accepted_at}</code>\n\nТеперь вы можете пользоваться проверкой транспортного средства.",
        "ask_plate": "🚘 Отправьте государственный номер проверяемого транспортного средства.\nНапример: <code>01A123BB</code>",
        "bad_plate": "Государственный номер отправлен в неверном формате. Пожалуйста, введите повторно.\nНапример: <code>01A123BB</code>",
        "help": "Бот проверяет документы таможенного контроля по государственному номеру транспортного средства.\n\nДля проверки выберите в меню кнопку <b>Проверка</b>.",
        "fallback": "Выберите нужное действие в меню.",
        "cancelled": "Действие отменено.",
        "button_contact": "📱 Отправить номер телефона",
        "button_accept_terms": "✅ Согласен с условиями",
        "button_check": "🔎 Проверка",
        "button_terms": "📄 Условия использования",
        "button_language": "🌐 Изменить язык",
        "button_cancel": "Отмена",
        "menu_placeholder": "Выберите нужный раздел",
        "contact_placeholder": "Отправьте номер телефона",
    },
    "en": {
        "choose_language": "🌐 Please select the bot language.",
        "language_saved": "✅ Language selected: English.",
        "language_changed": "✅ Language setting has been updated.",
        "ask_name": "Hello.\n\nPlease enter your name before using the bot.",
        "short_name": "Please enter your name more completely.",
        "ask_contact_after_name": "Thank you. Now please send your phone number.",
        "ask_contact": "📱 Please send your phone number via Telegram.",
        "contact_expected": "Please send your phone number using the special button below.",
        "wrong_contact": "Please send your own Telegram contact.",
        "contact_saved": "Your phone number has been accepted.",
        "contact_updated": "Your phone number has been updated.\n\nPlease select an action.",
        "registered": "✅ Registration has been completed.\n\nPlease select an action.",
        "terms_caption": "📄 Please review the Terms of Use.\n\nTo continue using the bot, you must confirm your consent to the terms.",
        "terms_missing": "The Terms of Use image has not been uploaded yet. The file will later be placed at <code>{path}</code>.",
        "accept_first": "Please complete registration first.",
        "accept_terms_answer": "Consent has been accepted.",
        "terms_accepted": "✅ Your consent to the Terms of Use has been saved.\n🕘 Consent time: <code>{accepted_at}</code>\n\nYou can now use vehicle checks.",
        "ask_plate": "🚘 Send the state plate number of the vehicle to be checked.\nExample: <code>01A123BB</code>",
        "bad_plate": "The state plate number was sent in an incorrect format. Please try again.\nExample: <code>01A123BB</code>",
        "help": "The bot checks customs control documents by vehicle state plate number.\n\nTo check, select <b>Check</b> from the menu.",
        "fallback": "Please select an action from the menu.",
        "cancelled": "The action has been cancelled.",
        "button_contact": "📱 Send phone number",
        "button_accept_terms": "✅ I agree to the terms",
        "button_check": "🔎 Check",
        "button_terms": "📄 Terms of Use",
        "button_language": "🌐 Change language",
        "button_cancel": "Cancel",
        "menu_placeholder": "Select a section",
        "contact_placeholder": "Send your phone number",
    },
}


def normalize_lang(lang: str | None) -> str:
    return lang if lang in LANGUAGES else DEFAULT_LANG


def t(lang: str | None, key: str, **kwargs: object) -> str:
    code = normalize_lang(lang)
    template = TEXTS[code].get(key) or TEXTS[DEFAULT_LANG][key]
    return template.format(**kwargs)


def button_texts(key: str) -> set[str]:
    return {texts[key] for texts in TEXTS.values()}
