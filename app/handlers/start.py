from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.keyboards import phone_number_kb

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "👋 Ombor botiga xush kelibsiz!\n\n"
        "Iltimos, telefon raqamingizni ulashing:",
        reply_markup=phone_number_kb(),
    )


@router.message(F.contact)
async def phone_number_received(message: Message):
    phone = message.contact.phone_number
    await message.answer(
        f"✅ Telefon raqamingiz qabul qilindi: {phone}\n\n"
        "Admin tomonidan tasdiqlanishini kuting.",
        reply_markup=await _get_main_menu(message),
    )


async def _get_main_menu(message: Message):
    from app.keyboards import main_menu_kb
    role = "client"
    return main_menu_kb(role)
