from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def phone_number_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="📱 Telefon raqamni ulashish", request_contact=True)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def main_menu_kb(role: str) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    if role == "admin":
        builder.button(text="➕ Mahsulot qo'shish")
        builder.button(text="📋 Mijozlarni ko'rish")
        builder.button(text="📊 Hisobot")
    else:
        builder.button(text="📦 Mening mahsulotlarim")
    builder.button(text="❓ Yordam")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def admin_panel_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="➕ Mahsulot qo'shish")
    builder.button(text="📤 Mahsulot chiqarish")
    builder.button(text="📋 Mijozlarni ko'rish")
    builder.button(text="📊 Hisobot")
    builder.button(text="❓ Yordam")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def cancel_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="❌ Bekor qilish")
    return builder.as_markup(resize_keyboard=True)


def confirmation_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="Ha ✅")
    builder.button(text="Yo'q ❌")
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
