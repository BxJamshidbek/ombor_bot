from aiogram import Router, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.database import create_user, get_user_by_telegram_id
from app.keyboards import main_menu_kb, phone_number_kb
from app.states import Registration
from app.utils.validators import normalize_phone, validate_phone_number

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    if user:
        role = user["role"]
        await message.answer(
            "Siz allaqachon ro'yxatdan o'tgansiz ✅",
            reply_markup=main_menu_kb(role),
        )
        return

    await state.set_state(Registration.waiting_for_phone)
    await message.answer(
        "👋 Ombor botiga xush kelibsiz!\n\n"
        "Iltimos, telefon raqamingizni ulashing:",
        reply_markup=phone_number_kb(),
    )


@router.message(Registration.waiting_for_phone, F.contact)
async def phone_contact_received(message: Message, state: FSMContext):
    if message.contact.user_id != message.from_user.id:
        await message.answer(
            "Iltimos, faqat o'zingizning Telegram telefon raqamingizni ulashing."
        )
        return

    phone = message.contact.phone_number
    normalized = normalize_phone(phone)

    if not validate_phone_number(normalized):
        await message.answer(
            "Noto'g'ri telefon raqam formati. Iltimos, qaytadan urinib ko'ring.",
            reply_markup=phone_number_kb(),
        )
        return

    full_name = message.from_user.full_name
    username = message.from_user.username

    await create_user(
        telegram_id=message.from_user.id,
        phone=normalized,
        full_name=full_name,
        username=username,
    )

    await state.clear()
    await message.answer(
        "Ro'yxatdan o'tish yakunlandi ✅",
        reply_markup=main_menu_kb("client"),
    )


@router.message(Registration.waiting_for_phone)
async def phone_contact_missing(message: Message):
    await message.answer(
        "Iltimos, quyidagi tugmani bosib telefon raqamingizni ulashing:",
        reply_markup=phone_number_kb(),
    )
