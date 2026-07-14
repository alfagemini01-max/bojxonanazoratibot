# NazoratBot Telegram Python

Bu papka transport vositasi davlat raqami bo'yicha bojxona nazoratidagi hujjatlarni tekshiradigan Telegram bot uchun tayyorlandi.

Bot oqimi:

1. `/start` bosilganda foydalanuvchidan ism so'raladi.
2. Telefon raqamini Telegram kontakt tugmasi orqali yuborish so'raladi.
3. Foydalanish shartlari PDF ko'rinishida yuboriladi. PDF hali bo'lmasa, bot matnli ogohlantirish beradi.
4. Foydalanuvchi `Shartlarga roziman` tugmasini bosadi.
5. Rozilik vaqti SQLite bazasida saqlanadi.
6. Asosiy menyuda `Tekshirish` tugmasi orqali davlat raqami kiritiladi.
7. Bot nazoratdagi hujjatlar, bojxona yig'imlari, YHXB jarimasi va boshqa taqiqlar bo'yicha xabar qaytaradi.

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
DATA_SOURCE=demo
TZ=Asia/Tashkent
```

Polling bot uchun Render’da `Worker` servis tanlash maqsadga muvofiq. Webhook ishlatmoqchi bo'lsangiz `BOT_MODE=webhook` va `WEBHOOK_URL` qiymatlarini kiriting.

## Foydalanish shartlari PDF

PDF tayyor bo'lganda quyidagi manzilga joylashtiring:

```text
assets/foydalanish_shartlari.pdf
```

Kerak bo'lsa `.env` orqali boshqa fayl yo'lini ko'rsatish mumkin:

```text
TERMS_PDF_PATH=assets/foydalanish_shartlari.pdf
```

## Ma'lumot manbai

Hozir bot `DATA_SOURCE=demo` rejimida 31 ta test holat bilan ishlaydi.

SQL Serverga ulash uchun:

```text
DATA_SOURCE=sqlserver
SQL_CONNECTION_STRING=DRIVER={ODBC Driver 18 for SQL Server};SERVER=server_host,1433;DATABASE=db_name;UID=user;PWD=password;TrustServerCertificate=yes;
SQL_QUERY_PATH=sql/vehicle_check.sql
```

SQL Server rejimida `requirements-sql.txt` o'rnatiladi:

```bash
pip install -r requirements-sql.txt
```

`sql/vehicle_check.sql` faylida bot kutadigan ustunlar va moslashtiriladigan namunaviy T-SQL so'rov berilgan.

## Sinov raqamlari

| Raqam | Holat |
|---|---|
| `01A123BB` | Milliy yengil avtomobil, nazoratdagi yuk hujjati yo'q |
| `01B555CC` | Milliy yuk mashinasi, Eksport 3 qadam nazoratda |
| `01B556CC` | Milliy yuk mashinasi, Eksport 3 qadam topilmagan |
| `774ABC77` | Xorijiy yuk mashinasi, muddati o'tgan tranzit deklaratsiya va MB |
| `999KZ777` | Xorijiy yuk mashinasi, yuk nazorati yo'q, MB bor |
| `A123BC01` | Xorijiy yengil avtomobil, MB muddati o'tmagan |
| `B777DD09` | Xorijiy yengil avtomobil, MB muddati o'tgan |
| `270KZ777` | Xorijiy yuk mashinasi, YUBNK muddati o'tmagan |
| `888KZ777` | Xorijiy yuk mashinasi, YUBNK muddati o'tgan |
| `01C888EE` | Milliy yengil avtomobil, YHXB jarimasi bor |
| `01D444FF` | Milliy yengil avtomobil, MIB taqiqi bor |
| `T1234AB` | Xorijiy tirkama, MB muddati o'tmagan |
| `70ABC01` | Xorijiy yengil avtomobil, MB tugashiga 3 kun qolgan |
| `TR9999KZ` | Xorijiy tirkama, MB tugashiga 3 kun qolgan |
| `555TR555` | Xorijiy yuk mashinasi, tranzit deklaratsiya nazoratda |
| `03Z333ZZ` | Milliy yuk mashinasi, Eksport 3 qadam muddati o'tgan |
| `04Q444QQ` | Milliy yuk mashinasi, bojxona yig'imlari qarzdorligi bor |
| `05P555PP` | Milliy yengil avtomobil, bojxona yig'imlari qarzdorligi bor |
| `10H010HH` | Xorijiy yuk mashinasi, YUBNK va qarzdorlik bor |
| `60BUS60` | Xorijiy avtobus, MB muddati o'tmagan |
| `77L777LL` | Xorijiy yuk mashinasi, tranzit deklaratsiya nazoratda |
| `A000AA01` | Xorijiy transport, MB topilmagan |
| `22X222XX` | Milliy yuk mashinasi, Eksport 3 qadam nazoratda |
| `06M606MM` | Milliy yuk mashinasi, sud taqiqi va jarima bor |
| `30BUS01` | Milliy avtobus, nazorat hujjati yo'q |
| `KZ12345` | Xorijiy yuk mashinasi, TD va MB tugashiga 3 kun qolgan |
| `RU9090A` | Xorijiy yengil avtomobil, MB va YHXB jarimasi bor |
| `TJ7777T` | Xorijiy yuk mashinasi, yuk nazorati yo'q, MB bor |
| `TRK111RU` | Xorijiy tirkama, MB muddati o'tgan |
| `99A999AA` | Xorijiy yuk mashinasi, YUBNK muddati o'tgan va qarzdorlik bor |
| `NETERROR` | Tizimlardan biri javob bermagan test holati |

## Mantiqiy cheklov

Bot demo bazasida bitta transportga bir vaqtning o'zida faqat bitta yuk nazorat hujjati berilgan: `Tranzit deklaratsiya`, `Eksport 3 qadam` yoki `YUBNK`. Majburiyatnoma faqat xorijiy transport vositalarida ko'rsatiladi.
