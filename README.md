# Ombor Bot

Muzlatgichli ombor uchun Telegram bot. Kirim/chiqim nazorati, mijozlar va mahsulotlarni boshqarish.

## Imkoniyatlar

- Admin va mijoz rollari
- Mijozlarni telefon raqam orqali ro'yxatga olish
- Mahsulot qo'shish va chiqarish
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

1. Admin `/admin` buyrug'ini yuboradi
2. Bot `ADMIN_IDS` ro'yxati orqali adminlikni tekshiradi
3. Admin panel menyusi ochiladi
4. "➕ Mahsulot qo'shish" tugmasi bosiladi
5. Bot mijozning telefon raqamini so'raydi
6. Admin raqamni kiritadi, bot normalize qiladi va `users` jadvalidan qidiradi
7. Agar mijoz topilmasa: "Avval mijoz botga /start bosib telefon raqamini ulashishi kerak"
8. Agar mijoz topilsa: mahsulot nomi → kg miqdori → 1 kg narxi → saqlash muddati (kun) so'raladi
9. Yakuniy hisobot ko'rsatiladi va tasdiqlash so'raladi
10. "Ha ✅" bossa `products` jadvaliga yoziladi
11. "Yo'q ❌" yoki "❌ Bekor qilish" bossa jarayon bekor qilinadi

## Client mahsulotlarni ko'rish

1. Foydalanuvchi "📦 Mening mahsulotlarim" tugmasini bosadi
2. Bot Telegram ID orqali foydalanuvchini topadi
3. Agar foydalanuvchi ro'yxatdan o'tmagan bo'lsa: "Avval /start orqali ro'yxatdan o'ting."
4. `get_products_by_client_id()` orqali mahsulotlar olinadi
5. Agar mahsulot yo'q bo'lsa: "Sizda hozircha mahsulot mavjud emas."
6. Mahsulotlar chiroyli formatda ko'rsatiladi (10 tadan ko'p bo'lsa, qolgani haqida xabar chiqadi)

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

### Google Cloud'da service account yaratish

1. [Google Cloud Console](https://console.cloud.google.com/) ga o'ting
2. Loyiha yarating yoki mavjud loyihani tanlang
3. "APIs & Services" → "Credentials" ga o'ting
4. "Create Credentials" → "Service Account" ni tanlang
5. Service account nomini kiriting va yarating
6. Yaratilgandan keyin "Keys" → "Add Key" → "JSON" ni tanlang
7. Yuklab olingan JSON faylni `credentials/service_account.json` ga nomlab saqlang
8. Google Sheets API ni yoqing: "APIs & Services" → "Library" → "Google Sheets API" → "Enable"
9. Google Drive API ni ham yoqing

### Google Sheets ID qayerdan olinadi

Google Sheet URL'ida:
```
https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit
```
`SPREADSHEET_ID` qismi — bu sizning Sheet ID'ingiz.

### Service account'ni Sheet'ga qo'shish

1. Service account JSON faylini oching va `client_email` qiymatini nusxalang
2. Google Sheet'ingizni oching
3. "Share" (Ulashish) tugmasini bosing
4. Service account email'ini qo'shing va "Editor" (Muharrir) rolini bering

### .env sozlamalari

```
GOOGLE_SHEETS_ID=your_google_sheet_id_here
GOOGLE_SERVICE_ACCOUNT_FILE=credentials/service_account.json
```

### Bot qanday ishlaydi

- Bot start bo'lganda `SheetsService.initialize()` chaqiriladi
- Agar credentials topilmasa, Sheets funksiyasi o'chiriladi (bot ishlashda davom etadi)
- Admin mahsulot qo'shganda avval SQLite, keyin Google Sheets'ga yoziladi
- Agar Sheets'ga yozishda xatolik bo'lsa, SQLite'dagi ma'lumot saqlanadi va adminga xabar chiqadi
- Sheet avtomatik tarzda "Kirim" varaqini yaratadi va headerlarni o'zi yozadi

**Muhim:** Service account JSON faylini **hech qachon** gitga push qilmang. U `.gitignore` orqali chiqarib tashlangan.

## DB ni tekshirish

### Foydalanuvchilar
```bash
sqlite3 data/ombor_bot.sqlite3 "SELECT telegram_id, phone, full_name, username, role, created_at FROM users;"
```

### Mahsulotlar
```bash
sqlite3 data/ombor_bot.sqlite3 "SELECT client_name, phone, product_name, kg_amount, price_per_kg, storage_days, total_price, status, created_at FROM products;"
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
