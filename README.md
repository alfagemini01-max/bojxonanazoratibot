# NazoratBot Telegram Python

Bu papka xorijiy yuk avtotransport vositalarining O'zbekiston Respublikasiga kirishi yoki hududi orqali tranzit o'tishi bo'yicha ruxsatnoma va yig'im shartlarini tekshiradigan Telegram bot uchun tayyorlandi.

Bot oqimi:

1. `/start` bosilganda yangi foydalanuvchidan faqat bot tilini tanlash so'raladi.
2. Til avval tanlangan bo'lsa, asosiy menyu darhol ochiladi.
3. `Dazvol` tugmasi orqali tashuv boshlangan davlat, tashuv tugaydigan davlat va avtotransport ro'yxatdan o'tgan davlat ketma-ket kiritiladi.
4. `Chegaradagi yig'imlar` tugmasi orqali chegara bojxona postida undirilishi mumkin bo'lgan to'lovlar kalkulyatori ishga tushadi.
5. Har bir davlat nomi yozilganda bot mos kelgan davlatlarni kod va nomi bilan tugma ko'rinishida chiqaradi.
6. Davlatlar tanlangandan keyin bot tashuv turini avtomatik aniqlaydi va ruxsatnoma hamda yig'im bo'yicha javob qaytaradi.

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
BOT_MODE=webhook
WEBHOOK_URL=https://bojxonanazoratibot.onrender.com
WEBHOOK_PATH=/webhook
PERMISSION_RULES_PATH=data/permission_rules.json
TZ=Asia/Tashkent
FEES_RULES_PATH=data/fees_2026.json
BHM_VALUE=412000
USD_FALLBACK_RATE=12600
ADMIN_USERNAME=admin
ADMIN_PASSWORD=kuchli_parol_kiriting
ADMIN_SESSION_SECRET=uzun_tasodifiy_secret_kiriting
```

Tavsiya qilingan servis turi: `Web Service`.

Bot Renderda `webhook` rejimida ishlaydi. Bu rejim bitta bot token bo'yicha bir nechta `getUpdates` so'rovlari to'qnashuvini oldini oladi.

Render uchun kichik HTTP tekshiruv endpointlari ham ochiladi:

```text
/
/health
/admin
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

## Ma'lumot manbai

Bot `data/permission_rules.json` faylidagi spravochnik orqali ishlaydi. JSON fayl `Dazvollar davlatlar kesimida.xlsx` va `Dazvol istisnolar.xlsx` fayllari asosida tayyorlangan.

Kerak bo'lsa Render Environment Variables orqali boshqa JSON yo'lini ko'rsatish mumkin:

```text
PERMISSION_RULES_PATH=data/permission_rules.json
```

## Chegara to'lovlari kalkulyatori

Yangi `Chegaradagi yig'imlar` bo'limi quyidagi ma'lumotlar asosida taxminiy hisob-kitob beradi:

1. Transport turi.
2. Avtotransport ro'yxatdan o'tgan davlat.
3. Yo'nalish: O'zbekistonga kirish, tranzit o'tish yoki O'zbekistondan chiqish.
4. Yuk transporti bo'lsa, tashuv boshlangan va tugaydigan davlat.
5. Deklaratsiya, tranzit deklaratsiyasi, qoraytirilgan oyna, OSAGO, og'ir/yirik gabarit, gumanitar yuk, veterinariya nazorati, muddatdan o'tish va yukni kech yetkazish bo'yicha kerakli savollar.

Hisoblash qoidalari `data/fees_2026.json` faylida saqlanadi. BHM va USD zaxira kursi Render Environment Variables orqali yangilanishi mumkin:

```text
BHM_VALUE=412000
USD_FALLBACK_RATE=12600
FEES_RULES_PATH=data/fees_2026.json
```

Kalkulyator natijasi axborot-tavsiyaviy xususiyatga ega. Yakuniy summa chegara bojxona postida amaldagi Markaziy bank kursi va vakolatli tizimlardagi ma'lumotlar asosida aniqlanadi.

## Web admin panel

Admin panel Renderdagi shu Web Service ichida ishlaydi:

```text
https://SIZNING-RENDER-NOMINGIZ.onrender.com/admin
https://SIZNING-RENDER-NOMINGIZ.onrender.com/admin/dashboard
```

Panel orqali quyidagilar boshqariladi:

1. Davlat qo'shish, nomini o'zgartirish yoki o'chirish.
2. Har bir davlat bo'yicha 1-8 tashuv turi uchun Dazvol qoidasi.
3. Ruxsatnoma kerak/kerak emas/taqiqlangan holati.
4. Kirish yoki tranzit yig'imi undiriladi/undirilmaydi/ruxsat turiga qarab holati.
5. Dazvol qoidasi bo'yicha yig'im undirilsa, USD stavka va foydalanuvchiga chiqadigan UZ/RU/EN izoh kiritish.
6. Chegaradagi yig'imlar import, eksport va tranzit yo'nalishlari bo'yicha alohida boshqariladi.
7. Yig'im turi, miqdori, qo'llanish sharti va huquqiy asosi oddiy forma orqali qo'shiladi, o'zgartiriladi yoki o'chiriladi.
8. `Qoidalarni import qilish` bo'limida `Dazvollar davlatlar kesimida.xlsx` shaklidagi fayl yuklanadi.
9. Import jarayoni yuklash va tahlil foizini ko'rsatadi, so'ng mavjud va yangi qiymatlarni taqqoslaydi.
10. Har bir o'zgarish checkbox orqali alohida tanlanadi, tahrirlanadi yoki importdan chiqariladi.
11. `ISDELETED=1` yozuvlari xavfsizlik uchun dastlab tanlanmaydi; ularni o'chirish admin tomonidan alohida tasdiqlanadi.
12. Importdan avvalgi qoidalar `data/permission_rules.before-import.json` vaqtinchalik zaxira nusxasida saqlanadi.

Render Environment Variables ichida admin login va parolni albatta o'zgartiring:

```text
ADMIN_USERNAME=admin
ADMIN_PASSWORD=faqat_siz_biladigan_kuchli_parol
ADMIN_SESSION_SECRET=kamida_32_belgili_tasodifiy_secret
```

Muhim: Render Free Web Service local fayl tizimidagi admin o'zgarishlarini redeploy/restartdan keyin yo'qotishi mumkin. Doimiy saqlash uchun keyingi bosqichda qoidalarni Postgres jadvaliga ko'chirish tavsiya etiladi.

## Tekshiruv mantiqi

Bot foydalanuvchidan 3 ta davlatni so'raydi:

1. Tashuv boshlangan davlat.
2. Tashuv tugaydigan davlat.
3. Avtotransport ro'yxatdan o'tgan davlat.

Davlat nomi matn orqali yakuniy qabul qilinmaydi. Bot avval o'xshash davlatlar ro'yxatini chiqaradi, foydalanuvchi esa aniq davlatni tugma orqali tanlaydi.

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

Qo'shimcha izohlar quyidagicha qo'llanadi:

- Turkmaniston yuk avtotransport vositasi bilan uchinchi mamlakatlardan O'zbekistonga yuk olib kirish yoki O'zbekiston hududidan yuk olib chiqishda yig'imga 375 USD qo'shimcha qo'shiladi.
- Og'ir vaznli yoki yirik gabaritli transport vositalarida alohida qonunchilik to'lovlari bo'lishi mumkinligi ogohlantirish sifatida ko'rsatiladi.
- Gumanitar yuklar uchun kirish va tranzit yig'imlariga 0,5 kamaytiruvchi koeffitsiyent qo'llanishi mumkinligi ogohlantirish sifatida ko'rsatiladi.
- Eron Islom Respublikasi transport vositalari uchun kirish va tranzit yig'im stavkasi 0 USD sifatida belgilanadi.
- Xalqaro shartnomada boshqacha tartib belgilangan bo'lsa, xalqaro shartnoma qoidalari qo'llanishi ogohlantiriladi.

## Sinov uchun namunalar

| Boshlangan davlat | Tugaydigan davlat | Transport davlati | Kutiladigan mazmun |
|---|---|---|---|
| `Xitoy` | `O'zbekiston` | `Qozog'iston` | Uchinchi davlatdan tashuv, ruxsatnoma majburiy, yig'im undirilmaydi |
| `Afg'oniston` | `O'zbekiston` | `Afg'oniston` | Ikki tomonlama tashuv, ruxsatnoma talab etilmaydi, 50 USD yig'im |
| `Germaniya` | `Qozog'iston` | `Rossiya` | Tranzit tashuv, spravochnik qoidasiga ko'ra yig'im hisoblanadi |
| `O'zbekiston` | `Qozog'iston` | `Qozog'iston` | Ikki tomonlama tashuv, tashuv O'zbekistonda boshlanadi |
