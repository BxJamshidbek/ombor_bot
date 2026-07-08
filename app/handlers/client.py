from aiogram import Router, F
from aiogram.types import Message

from app.database import (
    get_client_active_payment_summary,
    get_products_by_client_id_asc,
    get_sheet_visible_active_products_by_client_id,
    get_user_by_telegram_id,
)
from app.services.calculation_service import allocate_payments_to_products
from app.keyboards import main_menu_kb
from app.services.formatting_service import format_product_list

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
            "➕ Mahsulot qo'shish - Mijozga mahsulot qo'shish\n"
            "💳 To'lov kiritish - Mijoz to'lovini kiritish\n"
            "📋 Mijozlarni ko'rish - Mijozlar ro'yxati\n"
            "📊 Hisobot - Hisobot\n\n"
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
