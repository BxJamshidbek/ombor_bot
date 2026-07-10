from aiogram import Router, F
from aiogram.types import Message

from app.database import (
    get_client_active_payment_summary,
    get_products_by_client_id_asc,
    get_sheet_visible_active_products_by_client_id,
    get_user_by_telegram_id,
    get_warehouse_location,
)
from app.services.calculation_service import allocate_payments_to_products
from app.keyboards import main_menu_kb
from app.services.formatting_service import format_product_list
from app.utils.validators import build_google_maps_url

router = Router()


@router.message(F.text == "📦 Mening mahsulotlarim")
async def my_products(message: Message):
    user = await get_user_by_telegram_id(message.from_user.id)
    if user is None:
        await message.answer("Avval /start orqali ro'yxatdan o'ting.")
        return

    products = await get_sheet_visible_active_products_by_client_id(user["id"])
    summary = await get_client_active_payment_summary(user["id"])

    allocation = {}
    for p in products:
        pid = p["id"]
        paid = summary.get("paid_amount", 0)
        total = summary.get("total_amount", 0)
        allocation[pid] = {
            "paid_amount": 0,
            "remaining_amount": p["total_price"],
        }

    text = format_product_list(products, payment_summary=summary, allocation=allocation)
    await message.answer(text, reply_markup=main_menu_kb(user["role"]))


@router.message(F.text == "❓ Yordam")
async def help_handler(message: Message):
    user = await get_user_by_telegram_id(message.from_user.id)
    role = user["role"] if user else "client"

    if role == "admin":
        text = (
            "🤖 <b>Ombor boti — Admin yordam</b>\n\n"
            "/admin - Admin panel\n"
            "📋 Mijozlarni ko'rish - Ro'yxatdan o'tgan mijozlar ro'yxati\n"
            "📊 Hisobot - Ombor hisoboti\n\n"
            "Mahsulot qo'shish, to'lov kiritish va chiqarish faqat "
            "📋 Mijozlarni ko'rish orqali tanlangan mijoz ichidan amalga oshiriladi.\n\n"
            "Mijozlarga /start bosib ro'yxatdan o'tishni tavsiya eting."
        )
    else:
        text = (
            "🤖 <b>Ombor boti — Yordam</b>\n\n"
            "/start - Botga kirish va ro'yxatdan o'tish\n"
            "📦 Mening mahsulotlarim - O'z mahsulotlaringizni ko'rish\n\n"
            "Savol va muammolar bo'lsa, ombor admini bilan bog'laning."
        )

    await message.answer(text, reply_markup=main_menu_kb(role))


@router.message(F.text == "📍 Ombor lokatsiyasi")
async def warehouse_location(message: Message):
    user = await get_user_by_telegram_id(message.from_user.id)
    if user is None:
        await message.answer("Avval /start orqali ro'yxatdan o'ting.")
        return

    location = await get_warehouse_location()
    if location is None:
        await message.answer(
            "Ombor lokatsiyasi hali admin tomonidan sozlanmagan.",
            reply_markup=main_menu_kb(user["role"]),
        )
        return

    latitude = location["warehouse_latitude"]
    longitude = location["warehouse_longitude"]
    name = location.get("warehouse_location_name")
    maps_url = build_google_maps_url(latitude, longitude)

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗺 Google Maps'da ochish", url=maps_url)]
    ])

    await message.answer_location(latitude=latitude, longitude=longitude)
    display_name = name if name else "Ombor lokatsiyasi"
    await message.answer(
        f"📍 <b>{display_name}</b>\n\nQuyidagi tugmani bosib Google Maps'da ochishingiz mumkin.",
        reply_markup=kb,
    )
