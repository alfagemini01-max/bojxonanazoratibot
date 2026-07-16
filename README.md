# NazoratBot Telegram Python

Bu papka xorijiy yuk avtotransport vositalarining O'zbekiston Respublikasiga kirishi yoki hududi orqali tranzit o'tishi bo'yicha ruxsatnoma va yig'im shartlarini tekshiradigan Telegram bot uchun tayyorlandi.

Bot oqimi:

1. `/start` bosilganda foydalanuvchidan bot tilini tanlash so'raladi.
2. Foydalanuvchidan ism so'raladi.
3. Telefon raqamini Telegram kontakt tugmasi orqali yuborish so'raladi.
4. Foydalanish shartlari rasm ko'rinishida yuboriladi. Rasm hali bo'lmasa, bot PDF fallback yoki matnli ogohlantirish beradi.
5. Foydalanuvchi `Shartlarga roziman` tugmasini bosadi.
6. Rozilik vaqti foydalanuvchi bazasida saqlanadi. Render uchun tashqi Postgres ishlatish tavsiya etiladi.
7. Asosiy menyuda `Tekshirish` tugmasi orqali tashuv boshlangan davlat, tashuv tugaydigan davlat va avtotransport ro'yxatdan o'tgan davlat ketma-ket kiritiladi.
8. Bot tashuv turini avtomatik aniqlaydi va ruxsatnoma talab etilishi hamda yig'im undirilishi bo'yicha xabar qaytaradi.

Bot O'zbek, Rus va Ingliz tillarida ishlaydi. Tilni asosiy menyudagi `Tilni o'zgartirish` tugmasi yoki `/language` buyrug'i orqali almashtirish mumkin.

## Ishga tushirish

Python 3.11 yoki undan yuqori versiya tavsiya etiladi.

```bash
pip install -r requirements.txt
copy .env.example .env
python -m app.main
```

`.env` ichida kamida `BOT_TOKEN` qiymatini kiriting.

## Render orqali joylash

Render uchun `render.yaml` va `Procfile` tayyor.

Render sozlamalarida Environment Variables:

```text
BOT_TOKEN=Telegram BotFather bergan token
BOT_MODE=polling
PERMISSION_RULES_PATH=data/permission_rules.json
TZ=Asia/Tashkent
```

Tavsiya qilingan servis turi: `Web Service`.

Bot `polling` rejimida Telegramdan xabarlarni olib turadi. Shu bilan birga Render Web Service uchun kichik HTTP server ham ochiladi.

Render uchun kichik HTTP tekshiruv endpointlari ham ochiladi:

```text
/
/health
```

Render Free Web Service 15 daqiqa kiruvchi trafik bo'lmasa uxlab qoladi. Botni uyg'oq saqlash uchun UptimeRobot orqali quyidagi URLga 5 daqiqada bir marta HTTP GET so'rov yuborish mumkin:

```text
https://SIZNING-RENDER-NOMINGIZ.onrender.com/health
```

Foydalanuvchi ma'lumotlari restart/redeploydan keyin ham saqlanishi uchun tashqi Postgres URL kiriting:

```text
USER_DATABASE_URL=postgresql://user:password@host:5432/dbname?sslmode=require
```

`USER_DATABASE_URL` bo'lmasa bot SQLite faylga yozadi. Render Free Web Service redeploy/restart bo'lganda local fayllar o'chishi mumkin, shu sababli ishlab turgan bot uchun Postgres tavsiya etiladi.

## Foydalanish shartlari rasmi

Bot foydalanish shartlarini Telegram photo ko'rinishida yuboradi. Rasm quyidagi manzilda bo'lishi kerak:

```text
assets/foydalanish_shartlari.png
```

Kerak bo'lsa `.env` yoki Render Environment Variables orqali boshqa rasm yo'lini ko'rsatish mumkin:

```text
TERMS_IMAGE_PATH=assets/foydalanish_shartlari.png
```

Bot rasmni birinchi marta yuborgandan keyin Render logida `Terms photo file_id cached: ...` degan yozuv chiqadi. Shu `file_id` ni Render envga qo'ysangiz, keyingi deploylardan keyin ham rasm Telegram serveridan juda tez yuboriladi:

```text
TERMS_PHOTO_FILE_ID=telegram_file_id
```

PDF fallback sifatida qoldirilgan:

```text
TERMS_PDF_PATH=assets/foydalanish_shartlari.pdf
```

## Ma'lumot manbai

Bot `data/permission_rules.json` faylidagi spravochnik orqali ishlaydi. JSON fayl `Dazvollar davlatlar kesimida.xlsx` va `Dazvol istisnolar.xlsx` fayllari asosida tayyorlangan.

Kerak bo'lsa Render Environment Variables orqali boshqa JSON yo'lini ko'rsatish mumkin:

```text
PERMISSION_RULES_PATH=data/permission_rules.json
```

## Tekshiruv mantiqi

Bot foydalanuvchidan 3 ta davlatni so'raydi:

1. Tashuv boshlangan davlat.
2. Tashuv tugaydigan davlat.
3. Avtotransport ro'yxatdan o'tgan davlat.

Shundan keyin tashuv turi avtomatik aniqlanadi:

| Shart | Aniqlanadigan tashuv turi |
|---|---|
| Boshlangan davlat O'zbekiston, transport davlati tugaydigan davlat bilan bir xil | Ikki tomonlama, tashuv O'zbekistonda boshlanadi |
| Tugaydigan davlat O'zbekiston, transport davlati boshlangan davlat bilan bir xil | Ikki tomonlama, tashuv O'zbekistonda tugaydi |
| Tugaydigan davlat O'zbekiston, transport davlati boshlangan davlatdan boshqa | Uchinchi davlatdan tashuv |
| Boshlangan davlat O'zbekiston, transport davlati tugaydigan davlatdan boshqa | Uchinchi davlatga tashuv |
| Boshlangan va tugaydigan davlatlar O'zbekiston emas | Tranzit tashuv |
| Boshlangan va tugaydigan davlat O'zbekiston | Ichki tashuv |

Yig'im faqat Excel spravochnikda `Сбор обязательно` deb belgilangan holatda hisoblanadi. Agar Excelda `Сбор не обязательно` bo'lsa, stavka jadvalida miqdor mavjud bo'lsa ham bot yig'im undirilmasligini ko'rsatadi.

## Sinov uchun namunalar

| Boshlangan davlat | Tugaydigan davlat | Transport davlati | Kutiladigan mazmun |
|---|---|---|---|
| `Xitoy` | `O'zbekiston` | `Qozog'iston` | Uchinchi davlatdan tashuv, ruxsatnoma majburiy, yig'im undirilmaydi |
| `Afg'oniston` | `O'zbekiston` | `Afg'oniston` | Ikki tomonlama tashuv, ruxsatnoma talab etilmaydi, 50 USD yig'im |
| `Germaniya` | `Qozog'iston` | `Rossiya` | Tranzit tashuv, spravochnik qoidasiga ko'ra yig'im hisoblanadi |
| `O'zbekiston` | `Qozog'iston` | `Qozog'iston` | Ikki tomonlama tashuv, tashuv O'zbekistonda boshlanadi |
