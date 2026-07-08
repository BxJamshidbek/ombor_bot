# Ombor Bot

Muzlatgichli ombor uchun Telegram bot. Kirim/chiqim nazorati, mijozlar va mahsulotlarni boshqarish, to'lov tizimi.

## Imkoniyatlar

- Admin va mijoz rollari
- Mijozlarni telefon raqam orqali ro'yxatga olish
- Mahsulot qo'shish va chiqarish
- Product-based to'lov kiritish va qarzdorlik hisobi
- Google Sheets orqali hisobot (3 ta sheet: Ombor, Chiqarilganlar, To'lovlar tarixi)

## Local o'rnatish

### 1. Repository ni clone qiling

```bash
git clone https://github.com/BxJamshidbek/ombor_bot.git
cd ombor_bot
```

### 2. Virtual muhit yaratish

```bash
python3 -m venv .venv
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate    # Windows
```

### 3. Dependency larni o'rnatish

```bash
pip install -r requirements.txt
```

### 4. .env faylini yaratish

```bash
cp .env.example .env
```

So'ng `.env` faylini ochib, quyidagilarni to'ldiring:

| O'zgaruvchi | Tavsif |
|---|---|
| `BOT_TOKEN` | Telegram bot token (https://t.me/BotFather) |
| `ADMIN_IDS` | Admin Telegram ID lari (vergul bilan ajratib, masalan: `123456789,987654321`) |
| `GOOGLE_SHEETS_ID` | Google Sheets ID si |
| `GOOGLE_SERVICE_ACCOUNT_FILE` | Service account JSON fayl yo'li |

### 5. Botni ishga tushirish

```bash
python -m app.main
```

## /start orqali ro'yxatdan o'tish

1. Foydalanuvchi `/start` bosadi
2. Bot Telegram ID orqali foydalanuvchini tekshiradi
3. Agar foydalanuvchi avval ro'yxatdan o'tgan bo'lsa: "Siz allaqachon ro'yxatdan o'tgansiz ✅"
4. Agar ro'yxatdan o'tmagan bo'lsa: telefon raqam so'raladi
5. Foydalanuvchi "📱 Telefon raqamni ulashish" tugmasini bosadi
6. Telefon raqam validator orqali tekshiriladi va normalizatsiya qilinadi
7. Ma'lumotlar SQLite bazaga yoziladi
8. Foydalanuvchi asosiy menyuga o'tadi

## Admin panel / admin mahsulot qo'shish

**Muhim:** Admin mijozni qo'lda yaratmaydi. Mijoz avval `/start` bosib telefon raqamini ulashishi va o'zi ro'yxatdan o'tishi shart. Admin faqat mavjud mijozga mahsulot qo'shadi.

1. Admin `/admin` buyrug'ini yuboradi
2. Bot `ADMIN_IDS` ro'yxati orqali adminlikni tekshiradi
3. Admin panel menyusi ochiladi
4. "➕ Mahsulot qo'shish" tugmasi bosiladi
5. Bot mijozning telefon raqamini so'raydi
6. Admin raqamni kiritadi, bot normalize qiladi va `users` jadvalidan qidiradi
7. Agar mijoz topilmasa: "Avval mijoz botga /start bosib telefon raqamini ulashishi kerak"
8. Agar mijoz topilsa: mahsulot nomi → kg miqdori → 1 kg narxi → qutilar soni so'raladi
9. Yakuniy hisobot ko'rsatiladi va tasdiqlash so'raladi
10. "Ha ✅" bossa `products` jadvaliga yoziladi

**Hisob-kitob:** Umumiy summa = kg × 1 kg narxi

## Client mahsulotlarni ko'rish

1. Foydalanuvchi "📦 Mening mahsulotlarim" tugmasini bosadi
2. Bot Telegram ID orqali foydalanuvchini topadi
3. Faqat `active` statusdagi mahsulotlar ko'rsatiladi
4. Har bir mahsulot uchun: Product ID, nom, kg, quti, narx, umumiy, to'langan, qolgan
5. Pastida jami holat: umumiy summa, to'langan, qolgan

## Admin: Mahsulot chiqarish

1. Admin "📤 Mahsulot chiqarish" tugmasini bosadi
2. Bot mijozning telefon raqamini so'raydi
3. Faqat `active` mahsulotlar ko'rsatiladi
4. Admin Product ID kiritadi
5. Bot mahsulot ma'lumotlari va to'lov holatini ko'rsatadi
6. Agar qarz bo'lsa, ogohlantirish chiqadi
7. "Ha ✅" bossa:
   - SQLite'da status `exited` ga o'zgaradi
   - Google Sheets'da `Ombor` tabdan row o'chiriladi
   - `Chiqarilganlar` tabga snapshot qo'shiladi

## Admin: To'lov kiritish (product-based)

1. Admin "💳 To'lov kiritish" tugmasini bosadi
2. Bot mijozning telefon raqamini so'raydi
3. Faqat `active` mahsulotlar ko'rsatiladi (har biri uchun to'langan/qolgan bilan)
4. Admin Product ID kiritadi
5. Bot qolgan summani ko'rsatadi
6. Admin to'lov summasini kiritsa:
   - Summa qolgan summadan katta bo'lsa rad etiladi
   - "Ortiqcha to'lov mumkin emas" xabari chiqadi
7. Tasdiqlash: mijoz, mahsulot, eski to'lov, yangi to'lov, to'lovdan keyingi qolgan
8. "Ha ✅" bossa:
   - `payments` jadvaliga `product_id` bilan yoziladi
   - `To'lovlar tarixi` tabga transaction qo'shiladi
   - `Ombor` tabdagi to'langan/qolgan update qilinadi

## Google Sheets

3 ta sheet ishlatiladi:

### Ombor (faqat active mahsulotlar)

1. Product ID
2. Telegram ID
3. Telefon raqam
4. Ism
5. Mahsulot nomi
6. Kg miqdori
7. Qutilar soni
8. 1 kg narxi
9. Umumiy summa
10. To'langan summa
11. Qolgan summa
12. Status
13. Yaratilgan sana
14. Yangilangan sana

### Chiqarilganlar (exited mahsulotlar tarixi)

1. Product ID
2. Telegram ID
3. Telefon raqam
4. Ism
5. Mahsulot nomi
6. Kg miqdori
7. Qutilar soni
8. 1 kg narxi
9. Umumiy summa
10. To'langan summa
11. Qolgan summa
12. Status
13. Yaratilgan sana
14. Chiqim sanasi
15. Yangilangan sana

### To'lovlar tarixi (transaction log)

1. Payment ID
2. Product ID
3. Telegram ID
4. Telefon raqam
5. Ism
6. To'lov summasi
7. Admin Telegram ID
8. Yaratilgan sana

### Apps Script Web App

1. Google Sheet'ingizni oching
2. **Extensions** → **Apps Script** ga o'ting
3. `docs/apps_script_webapp.gs` faylidagi kodni paste qiling
4. Kod ichidagi `SECRET` qiymatini o'zgartiring
5. **Deploy** → **New deployment** → **Web app** ni tanlang
6. Deploy URL ni `.env` ga qo'shing

### .env sozlamalari

```
GOOGLE_SCRIPT_WEBAPP_URL=https://script.google.com/macros/s/.../exec
GOOGLE_SCRIPT_SECRET=my_secret_key_123
```

## Xavfsizlik

- `.env` faylini **hech qachon** gitga push qilmang
- Google service account JSON faylini `credentials/` papkasiga qo'ying
- Admin ID'lar faqat `.env` orqali sozlanadi, kodda hardcode qilinmaydi

## Loyiha tuzilishi

```
ombor_bot/
├── app/
│   ├── main.py              # Botni ishga tushirish
│   ├── config.py            # Konfiguratsiya (.env)
│   ├── database.py          # SQLite baza
│   ├── states.py            # FSM holatlari
│   ├── keyboards.py         # Klaviatura yaratish
│   ├── handlers/            # Telegram handlerlar
│   ├── services/            # Google Sheets va hisob
│   └── utils/               # Yordamchi funksiyalar
├── data/                    # SQLite fayllari (gitga tushmaydi)
├── credentials/             # Service account (gitga tushmaydi)
├── tests/                   # Testlar
├── .env.example             # O'zgaruvchilar namunasi
├── .gitignore
├── requirements.txt
└── README.md
```

## Developer

**BxJamshidbek**
