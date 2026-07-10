from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from app.config import config
from app.database import create_user, get_user_by_telegram_id
from app.keyboards import admin_main_kb, main_menu_kb, phone_number_kb
from app.states import Registration
from app.utils.validators import (
    normalize_phone,
    validate_phone_number,
    validate_full_name,
)

import logging

logger = logging.getLogger(__name__)

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    logger.info("Start command received: telegram_id=%s username=%s", message.from_user.id, message.from_user.username)
    if message.from_user.id in config.admin_ids:
        await state.clear()
        await message.answer(
            "Admin panelga xush kelibsiz.",
            reply_markup=admin_main_kb(),
        )
        return

    user = await get_user_by_telegram_id(message.from_user.id)
    if user:
        role = user["role"]
        name = user.get("full_name") or "Ism kiritilmagan"
        phone = normalize_phone(user["phone"])
        await message.answer(
            f"Siz ro'yxatdan o'tgansiz: {name} — {phone}",
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
    try:
        logger.info(
            "registration contact received: telegram_id=%s contact_user_id=%s",
            message.from_user.id if message.from_user else None,
            message.contact.user_id if message.contact else None,
        )

        if message.contact is None:
            logger.warning("registration: contact is None")
            await message.answer(
                "Iltimos, telefon raqamingizni ulashish tugmasini bosing.",
                reply_markup=phone_number_kb(),
            )
            return

        if message.contact.user_id is not None and message.contact.user_id != message.from_user.id:
            await message.answer(
                "Iltimos, faqat o'zingizning Telegram telefon raqamingizni ulashing."
            )
            return

        phone = message.contact.phone_number
        if not phone:
            logger.warning("registration: phone_number is empty")
            await message.answer(
                "Telefon raqam o'qilmadi. Qaytadan urinib ko'ring.",
                reply_markup=phone_number_kb(),
            )
            return

        normalized = normalize_phone(phone)
        logger.info("registration: phone normalized")

        if not validate_phone_number(normalized):
            await message.answer(
                "Noto'g'ri telefon raqam formati. Iltimos, qaytadan urinib ko'ring.",
                reply_markup=phone_number_kb(),
            )
            return

        await state.update_data(phone=normalized)
        await state.set_state(Registration.waiting_for_name)
        logger.info("registration: waiting for name")

        await message.answer(
            "Ismingizni kiriting. Masalan: Ali Valiyev",
            reply_markup=ReplyKeyboardRemove(),
        )
        logger.info("registration: phone step completed successfully")
    except Exception:
        logger.exception("registration crashed in phone_contact_received")
        await state.clear()
        await message.answer(
            "Ro'yxatdan o'tishda xatolik yuz berdi. /start orqali qayta urinib ko'ring."
        )


@router.message(Registration.waiting_for_name, F.text)
async def name_received(message: Message, state: FSMContext):
    try:
        logger.info("registration: name received telegram_id=%s", message.from_user.id)

        name = validate_full_name(message.text)
        if name is None:
            await message.answer(
                "Ism noto'g'ri. Iltimos, ismingizni kiriting "
                "(kamida 2 ta belgi, maksimal 100 ta belgi). Masalan: Ali Valiyev"
            )
            return

        data = await state.get_data()
        phone = data.get("phone")
        if not phone:
            logger.warning("registration: phone missing from state")
            await state.clear()
            await message.answer(
                "Ma'lumotlar yo'qolgan. /start orqali qayta urinib ko'ring.",
                reply_markup=phone_number_kb(),
            )
            return

        username = message.from_user.username

        existing = await get_user_by_telegram_id(message.from_user.id)
        if existing:
            logger.warning("registration: duplicate telegram_id=%s", message.from_user.id)
            await state.clear()
            role = existing["role"]
            await message.answer(
                "Siz allaqachon ro'yxatdan o'tgansiz ✅",
                reply_markup=main_menu_kb(role),
            )
            return

        from app.config import config

        role = "admin" if message.from_user.id in config.admin_ids else "client"

        logger.info("registration: create_user start")
        user_id = await create_user(
            telegram_id=message.from_user.id,
            phone=phone,
            full_name=name,
            username=username,
            role=role,
        )
        logger.info("registration: create_user done user_id=%s", user_id)

        await state.clear()
        logger.info("registration: state cleared")

        await message.answer(
            "Ro'yxatdan o'tish yakunlandi. Endi ombor egasi sizni telefon "
            "raqamingiz orqali topa oladi.",
            reply_markup=main_menu_kb(role),
        )
        logger.info("registration: success response sent")
    except Exception:
        logger.exception("registration crashed in name_received")
        await state.clear()
        await message.answer(
            "Ro'yxatdan o'tishda xatolik yuz berdi. /start orqali qayta urinib ko'ring."
        )


@router.message(Registration.waiting_for_phone)
async def phone_contact_missing(message: Message):
    await message.answer(
        "Iltimos, quyidagi tugmani bosib telefon raqamingizni ulashing:",
        reply_markup=phone_number_kb(),
    )


@router.message(Registration.waiting_for_name)
async def name_non_text(message: Message):
    await message.answer(
        "Iltimos, ismingizni matn ko'rinishida yuboring. Masalan: Ali Valiyev"
    )
