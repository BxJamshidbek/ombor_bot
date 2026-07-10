from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from app.utils.validators import normalize_phone


def phone_number_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="📱 Telefon raqamni ulashish", request_contact=True)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def admin_main_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="📋 Mijozlarni ko'rish")
    builder.button(text="📊 Hisobot")
    builder.button(text="⚙️ Sozlash")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def main_menu_kb(role: str) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    if role == "admin":
        builder.button(text="📋 Mijozlarni ko'rish")
        builder.button(text="📊 Hisobot")
        builder.button(text="⚙️ Sozlash")
    else:
        builder.button(text="📦 Mening mahsulotlarim")
        builder.button(text="📍 Ombor lokatsiyasi")
        builder.button(text="❓ Yordam")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def admin_panel_kb() -> ReplyKeyboardMarkup:
    return admin_main_kb()


def clients_list_kb(clients: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for c in clients:
        name = c.get("full_name") or "Ism kiritilmagan"
        phone = normalize_phone(c["phone"])
        label = f"{name} — {phone}"
        builder.button(text=label, callback_data=f"client:{c['id']}")
    builder.adjust(2)
    return builder.as_markup()


def client_actions_kb(client_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="➕ Mahsulot kiritish",
        callback_data=f"client_add_product:{client_id}",
    )
    builder.button(
        text="📦 Mahsulotlar",
        callback_data=f"client_products:{client_id}",
    )
    builder.button(
        text="💳 To'lov kiritish",
        callback_data=f"client_add_payment:{client_id}",
    )
    builder.button(
        text="📤 Mahsulotni chiqarish",
        callback_data=f"client_exit_product:{client_id}",
    )
    builder.button(text="⬅️ Ortga", callback_data="clients_back")
    builder.adjust(1)
    return builder.as_markup()


def client_products_kb(client_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="⬅️ Mijozga qaytish",
        callback_data=f"client_back_detail:{client_id}",
    )
    builder.button(text="⬅️ Ortga", callback_data="clients_back")
    builder.adjust(1)
    return builder.as_markup()


def settings_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="📍 Ombor lokatsiyasini sozlash",
        callback_data="settings:warehouse_location",
    )
    builder.button(
        text="📦 Mahsulot turlari",
        callback_data="settings_product_types",
    )
    builder.button(
        text="➕ Mahsulot turi qo'shish",
        callback_data="settings_add_product_type",
    )
    builder.button(text="⬅️ Ortga", callback_data="settings_back")
    builder.adjust(1)
    return builder.as_markup()


def product_type_selection_kb(client_id: int, product_types: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for pt in product_types:
        emoji = pt.get("emoji", "📦")
        label = f"{emoji} {pt['name']}"
        builder.button(
            text=label,
            callback_data=f"pt_select:{client_id}:{pt['id']}",
        )
    builder.button(
        text="✍️ Boshqa mahsulot",
        callback_data=f"pt_custom:{client_id}",
    )
    builder.button(
        text="⬅️ Mijozga qaytish",
        callback_data=f"client_back_detail:{client_id}",
    )
    builder.adjust(2)
    return builder.as_markup()


def cancel_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="❌ Bekor qilish")
    return builder.as_markup(resize_keyboard=True)


def menu_only_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="☰ Menu")
    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def confirmation_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="Ha ✅")
    builder.button(text="Yo'q ❌")
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def product_input_cancel_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="⬅️ Mijozga qaytish")
    builder.button(text="❌ Bekor qilish")
    return builder.as_markup(resize_keyboard=True)


def warehouse_location_confirm_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Ha, saqlash", callback_data="warehouse_location:confirm")
    builder.button(text="Yo'q, bekor qilish", callback_data="warehouse_location:cancel")
    builder.adjust(2)
    return builder.as_markup()
