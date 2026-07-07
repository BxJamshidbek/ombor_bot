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
| `ADMIN_IDS` | Admin Telegram ID lari (vergul bilan ajratib) |
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

Telegram dagi `request_contact=True` tugmasi orqali. Foydalanuvchi faqat o'z raqamini yuborishi mumkin — boshqa odamning contacti qabul qilinmaydi.

### DB qayerda yaratiladi

SQLite fayli `data/ombor_bot.sqlite3` da yaratiladi. Ushbu papka `.gitignore` orqali gitdan chiqarib tashlangan.

### DB'ni tekshirish

```bash
sqlite3 data/ombor_bot.sqlite3 "SELECT telegram_id, phone, full_name, username, role, created_at FROM users;"
```

## Xavfsizlik

- `.env` faylini **hech qachon** gitga push qilmang
- Google service account JSON faylini `credentials/` papkasiga qo'ying
- `credentials/` papkasi `.gitignore` orqali gitdan chiqarib tashlangan
- Maxfiy ma'lumotlarni faqat `.env` orqali yuklang

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
