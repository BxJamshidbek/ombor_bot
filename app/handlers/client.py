from aiogram import Router, F
from aiogram.types import Message

router = Router()


@router.message(F.text == "📦 Mening mahsulotlarim")
async def my_products(message: Message):
    await message.answer("Sizning mahsulotlaringiz ro'yxati:")


@router.message(F.text == "❓ Yordam")
async def help_handler(message: Message):
    await message.answer(
        "🤖 Ombor boti yordam bo'limi\n\n"
        "Admin buyruqlari:\n"
        "/admin - Admin panel\n"
        "/add_client - Mijoz qo'shish\n\n"
        "Mijoz buyruqlari:\n"
        "📦 Mening mahsulotlarim - Mahsulotlarni ko'rish"
    )
