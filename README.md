# Ombor Bot

Muzlatgichli ombor uchun Telegram bot. Kirim/chiqim nazorati, mijozlar va mahsulotlarni boshqarish, to'lov tizimi.

## Imkoniyatlar

- Admin va mijoz rollari
- Mijozlarni telefon raqam orqali ro'yxatga olish
- Mahsulot qo'shish va chiqarish
- To'lov kiritish va qarzdorlik hisobi
- Google Sheets orqali hisobot

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

### Telefon raqam qanday yuboriladi

Telegram'dagi `request_contact=True` tugmasi orqali. Foydalanuvchi faqat o'z raqamini yuborishi mumkin — boshqa odamning contacti qabul qilinmaydi.

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
11. "Yo'q ❌" yoki "❌ Bekor qilish" bossa jarayon bekor qilinadi

**Hisob-kitob:** Umumiy summa = kg × 1 kg narxi

## Client mahsulotlarni ko'rish

1. Foydalanuvchi "📦 Mening mahsulotlarim" tugmasini bosadi
2. Bot Telegram ID orqali foydalanuvchini topadi
3. Agar foydalanuvchi ro'yxatdan o'tmagan bo'lsa: "Avval /start orqali ro'yxatdan o'ting."
4. `get_products_by_client_id()` orqali mahsulotlar olinadi
5. `get_client_payment_summary()` orqali to'lov holati olinadi
6. Agar mahsulot yo'q bo'lsa: "Sizda hozircha mahsulot mavjud emas."
7. Mahsulotlar chiroyli formatda ko'rsatiladi
8. Pastida to'lov holati:
   - Jami to'lov
   - To'langan
   - Qolgan

### Admin /start ro'yxatdan o'tish

Agar foydalanuvchi `ADMIN_IDS` ro'yxatida bo'lsa, `/start` paytida uning roli `admin` qilib belgilanadi.

- `role = "admin"` → admin panel menyusi ko'rsatiladi
- `role = "client"` → client menyusi ko'rsatiladi

**Eski adminlar:** agar admin avval `client` role bilan ro'yxatdan o'tgan bo'lsa, DB'ni qo'lda tahrirlash kerak:
```sql
UPDATE users SET role='admin' WHERE telegram_id=123456789;
```

### Admin ID qanday beriladi

`.env` faylida:
```
ADMIN_IDS=123456789,987654321
```

Telegram ID'ni aniqlash uchun botga `/start` bosib, so'ngra https://t.me/userinfobot orqali tekshirish mumkin.

## Google Sheets

Ombor Bot Google Sheets'ga yozish uchun ikki xil usulni qo'llab-quvvatlaydi:

1. **Google Apps Script Web App** (tavsiya etiladi) — hech qanday API sozlamalari kerak emas
2. **Service Account** (murakkab) — Google Cloud Console talab qiladi

Ikkala usulda ham bot ishlaganda Sheets'ga yozishda xatolik bo'lsa, SQLite'dagi ma'lumot saqlanadi va adminga xabar chiqadi.

### Tavsiya: Google Apps Script Web App

1. Google Sheet'ingizni oching
2. **Extensions** → **Apps Script** ga o'ting
3. `docs/apps_script_webapp.gs` faylidagi kodni paste qiling
4. Kod ichidagi `SECRET` qiymatini o'zgartiring (masalan `const SECRET = "my_secret_key_123"`)
5. **Deploy** → **New deployment** → **Web app** ni tanlang
   - Execute as: **Me**
   - Who has access: **Anyone**
6. **Deploy** tugmasini bosing
7. Chiqgan Web App URL (`https://script.google.com/...`) ni nusxalang

### .env sozlamalari

Apps Script uchun:
```
GOOGLE_SCRIPT_WEBAPP_URL=https://script.google.com/macros/s/.../exec
GOOGLE_SCRIPT_SECRET=my_secret_key_123
```

Service Account uchun:
```
GOOGLE_SHEETS_ID=your_google_sheet_id_here
GOOGLE_SERVICE_ACCOUNT_FILE=credentials/service_account.json
```

### Bot qanday ishlaydi

- Bot start bo'lganda `SheetsService.initialize()` chaqiriladi
- Agar `GOOGLE_SCRIPT_WEBAPP_URL` va `GOOGLE_SCRIPT_SECRET` sozlangan bo'lsa → **Apps Script** mode
- Agar yuqoridagilar bo'lmasa va Service Account JSON fayli mavjud bo'lsa → **Service Account** mode
- Hech biri sozlanmagan bo'lsa, Sheets funksiyasi o'chiriladi (bot ishlashda davom etadi)
- Admin mahsulot qo'shganda avval SQLite, keyin Google Sheets'ga yoziladi
- Admin mahsulot chiqarganda avval SQLite (atomik transaction), keyin Google Sheets'ga yoziladi
- Admin to'lov kiritganda avval SQLite, keyin Google Sheets'ga yoziladi
- Agar Sheets'ga yozishda xatolik bo'lsa, SQLite'dagi ma'lumot saqlanadi va adminga xabar chiqadi
- Sheet avtomatik tarzda "Kirim", "Chiqim" va "To'lovlar" varaqlarini yaratadi va headerlarni o'zi yozadi

### Kirim sheet ustunlari

1. Telegram ID
2. Telefon raqam
3. Ism
4. Mahsulot nomi
5. Kg miqdori
6. Qutilar soni
7. 1 kg narxi
8. Umumiy summa
9. Status
10. Yaratilgan sana

### Chiqim sheet ustunlari

1. Product ID
2. Telegram ID
3. Telefon raqam
4. Ism
5. Mahsulot nomi
6. Kg miqdori
7. Qutilar soni
8. 1 kg narxi
9. Umumiy summa
10. Chiqim sanasi
11. Admin Telegram ID
12. Izoh

### To'lovlar sheet ustunlari

1. Payment ID
2. Telegram ID
3. Telefon raqam
4. Ism
5. To'lov summasi
6. Izoh
7. Admin Telegram ID
8. Yaratilgan sana

## Admin: Mijozlar ro'yxati

1. Admin "📋 Mijozlarni ko'rish" tugmasini bosadi
2. Bot `get_all_clients()` orqali barcha `role='client'` foydalanuvchilarni oladi
3. Agar mijoz yo'q bo'lsa: "Hozircha mijozlar mavjud emas."
4. Format: ism, telefon, Telegram ID, sana (ko'pi bilan 20 ta, qolgani "Yana X ta mijoz bor")

## Admin: Mahsulot chiqarish

1. Admin "📤 Mahsulot chiqarish" tugmasini bosadi
2. Bot mijozning telefon raqamini so'raydi
3. Admin raqamni kiritadi, bot normalize qiladi va `users` jadvalidan qidiradi
4. Agar mijoz topilsa, bot uning faol mahsulotlarini real `ID` bilan ko'rsatadi
5. Admin chiqariladigan mahsulot ID sini kiritadi
6. Bot ID orqali mahsulotni tekshiradi (status `active`, telefon mosligi)
7. Admin izoh kiritadi yoki `-` yuborib izohsiz davom etadi
8. Yakuniy tasdiq so'raladi
9. "Ha ✅" bossa:
   - Bitta transaction ichida `exits` jadvaliga chiqim yozuvi qo'shiladi
   - `products` jadvalidagi mahsulot statusi `exited` ga o'zgaradi
   - Agar xatolik bo'lsa, to'liq rollback qilinadi
10. "Yo'q ❌" yoki "❌ Bekor qilish" bossa jarayon bekor qilinadi

**Muhim:**
- Mahsulot `products` jadvalidan **o'chirilmaydi**, faqat statusi `exited` ga o'zgaradi
- Chiqim tarixi `exits` jadvalida saqlanadi
- Chiqim va product status o'zgarishi **atomik transaction** bilan yoziladi
- `exits` jadvalida `created_by_admin_id` va `note` ustunlari mavjud

## Admin: To'lov kiritish

1. Admin "💳 To'lov kiritish" tugmasini bosadi
2. Bot mijozning telefon raqamini so'raydi
3. Admin raqamni kiritadi, bot normalize qiladi va `users` jadvalidan qidiradi
4. Agar mijoz topilsa, bot to'lov summasini so'raydi
5. Admin summani kiritadi, so'ng izoh kiritadi yoki `-` yuboradi
6. Yakuniy tasdiq so'raladi
7. "Ha ✅" bossa:
   - `payments` jadvaliga yoziladi
   - Google Sheets'ga yoziladi

## Admin: Hisobot

1. Admin "📊 Hisobot" tugmasini bosadi
2. Bot `get_admin_stats()` orqali quyidagilarni hisoblaydi:
   - Mijozlar soni (`role='client'` dagi userlar)
   - Jami mahsulot yozuvlari (barcha products)
   - Faol mahsulotlar (`status='active'`)
   - Faol kg jami (`active products` dagi `kg_amount` SUM)
   - Umumiy summa (barcha products total_price SUM)
   - To'langan (barcha payments amount SUM)
   - Qolgan (umumiy summa - to'langan)

3. Format:

```
📊 Ombor hisoboti

Mijozlar soni: 10
Jami mahsulot yozuvlari: 25
Faol mahsulotlar: 23
Faol kg jami: 530.5 kg
Umumiy summa: 4,500,000 so'm
To'langan: 2,000,000 so'm
Qolgan: 2,500,000 so'm
```

## Qarzdorlik hisobi

- **Jami qarz (mijoz bo'yicha):** mijozning active + exited barcha mahsulotlari `total_price` yig'indisi
- **To'langan summa:** mijoz bo'yicha barcha `payments` amount yig'indisi
- **Qolgan summa:** jami qarz - to'langan summa

## DB ni tekshirish

### Foydalanuvchilar
```bash
sqlite3 data/ombor_bot.sqlite3 "SELECT telegram_id, phone, full_name, username, role, created_at FROM users;"
```

### Mahsulotlar
```bash
sqlite3 data/ombor_bot.sqlite3 "SELECT client_name, phone, product_name, kg_amount, price_per_kg, box_count, total_price, status, created_at FROM products;"
```

### To'lovlar
```bash
sqlite3 data/ombor_bot.sqlite3 "SELECT id, client_id, amount, note, created_at FROM payments;"
```

## Xavfsizlik

- `.env` faylini **hech qachon** gitga push qilmang
- Google service account JSON faylini `credentials/` papkasiga qo'ying
- `credentials/` papkasi `.gitignore` orqali gitdan chiqarib tashlangan
- Maxfiy ma'lumotlarni faqat `.env` orqali yuklang
- Admin ID'lar faqat `.env` orqali sozlanadi, kodda hardcode qilinmaydi

## Loyiha tuzilishi

```
ombor_bot/
├── app/
│   ├── main.py              # Botni ishga tushirish
│   ├── config.py            # Konfiguratsiya (.env)
│   ├── database.py          # SQLite baza
│   ├── models.py            # Ma'lumot modellari
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
