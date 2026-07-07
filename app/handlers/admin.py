from aiogram import Router, F
from aiogram.filters import Command, Filter, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from datetime import datetime, timezone

from app.config import config
from app.database import (
    create_product,
    get_admin_stats,
    get_all_clients,
    get_user_by_phone,
)
from app.services.formatting_service import format_admin_stats, format_client_list
from app.keyboards import admin_panel_kb, cancel_kb, confirmation_kb
from app.services.calculation_service import calculate_total_price
from app.services.sheets_service import sheets_service
from app.states import AdminAddProduct
from app.utils.validators import (
    normalize_phone,
    validate_phone_number,
    validate_positive_int,
    validate_quantity,
)

router = Router()


class IsAdmin(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in config.admin_ids


@router.message(Command("admin"), IsAdmin())
async def admin_panel(message: Message):
    await message.answer(
        "👑 Admin panel\n\nQuyidagi tugmalardan birini tanlang:",
        reply_markup=admin_panel_kb(),
    )


@router.message(Command("admin"))
async def admin_panel_denied(message: Message):
    await message.answer("Sizda admin panelga kirish huquqi yo'q.")


@router.message(F.text == "➕ Mahsulot qo'shish", IsAdmin())
async def add_product_start(message: Message, state: FSMContext):
    await state.set_state(AdminAddProduct.waiting_for_client_phone)
    await message.answer(
        "Mijozning telefon raqamini kiriting:\n\n"
        "Masalan: +998901234567 yoki 901234567",
        reply_markup=cancel_kb(),
    )


@router.message(AdminAddProduct.waiting_for_client_phone, F.text)
async def add_product_client_phone(message: Message, state: FSMContext):
    text = message.text.strip()

    if text == "❌ Bekor qilish":
        await cancel_flow(message, state)
        return

    normalized = normalize_phone(text)
    if not validate_phone_number(normalized):
        await message.answer(
            "Noto'g'ri telefon raqam formati. Qaytadan urinib ko'ring.\n\n"
            "Masalan: +998901234567",
            reply_markup=cancel_kb(),
        )
        return

    user = await get_user_by_phone(normalized)
    if user is None:
        await message.answer(
            "Bu telefon raqam bilan ro'yxatdan o'tgan mijoz topilmadi. "
            "Avval mijoz botga /start bosib telefon raqamini ulashishi kerak.",
            reply_markup=cancel_kb(),
        )
        return

    await state.update_data(
        client_id=user["id"],
        telegram_id=user["telegram_id"],
        phone=user["phone"],
        client_name=user["full_name"],
    )
    await state.set_state(AdminAddProduct.waiting_for_product_name)
    await message.answer(
        f"✅ Mijoz topildi: {user['full_name'] or 'Ismsiz'} "
        f"({user['phone']})\n\n"
        "Mahsulot nomini kiriting:",
        reply_markup=cancel_kb(),
    )


@router.message(AdminAddProduct.waiting_for_product_name, F.text)
async def add_product_name(message: Message, state: FSMContext):
    text = message.text.strip()

    if text == "❌ Bekor qilish":
        await cancel_flow(message, state)
        return

    if not text:
        await message.answer(
            "Mahsulot nomi bo'sh bo'lmasligi kerak. Qaytadan kiriting:",
            reply_markup=cancel_kb(),
        )
        return

    await state.update_data(product_name=text)
    await state.set_state(AdminAddProduct.waiting_for_kg_amount)
    await message.answer(
        "Mahsulot miqdorini kg da kiriting:\n\nMasalan: 10.5",
        reply_markup=cancel_kb(),
    )


@router.message(AdminAddProduct.waiting_for_kg_amount, F.text)
async def add_product_kg(message: Message, state: FSMContext):
    text = message.text.strip()

    if text == "❌ Bekor qilish":
        await cancel_flow(message, state)
        return

    kg = validate_quantity(text)
    if kg is None:
        await message.answer(
            "Noto'g'ri miqdor. Faqat musbat son kiriting.\n\nMasalan: 10.5",
            reply_markup=cancel_kb(),
        )
        return

    await state.update_data(kg_amount=kg)
    await state.set_state(AdminAddProduct.waiting_for_price_per_kg)
    await message.answer(
        "1 kg uchun narxni so'mda kiriting:\n\nMasalan: 2000",
        reply_markup=cancel_kb(),
    )


@router.message(AdminAddProduct.waiting_for_price_per_kg, F.text)
async def add_product_price(message: Message, state: FSMContext):
    text = message.text.strip()

    if text == "❌ Bekor qilish":
        await cancel_flow(message, state)
        return

    price = validate_quantity(text)
    if price is None:
        await message.answer(
            "Noto'g'ri narx. Faqat musbat son kiriting.\n\nMasalan: 2000",
            reply_markup=cancel_kb(),
        )
        return

    await state.update_data(price_per_kg=price)
    await state.set_state(AdminAddProduct.waiting_for_storage_days)
    await message.answer(
        "Saqlash muddatini kunlarda kiriting:\n\nMasalan: 30",
        reply_markup=cancel_kb(),
    )


@router.message(AdminAddProduct.waiting_for_storage_days, F.text)
async def add_product_storage_days(message: Message, state: FSMContext):
    text = message.text.strip()

    if text == "❌ Bekor qilish":
        await cancel_flow(message, state)
        return

    days = validate_positive_int(text)
    if days is None:
        await message.answer(
            "Noto'g'ri muddat. Faqat musbat butun son kiriting.\n\nMasalan: 30",
            reply_markup=cancel_kb(),
        )
        return

    data = await state.update_data(storage_days=days)

    kg_amount = data["kg_amount"]
    price_per_kg = data["price_per_kg"]
    total_price = calculate_total_price(kg_amount, price_per_kg, days)

    await state.update_data(total_price=total_price)

    summary = (
        f"📋 <b>Mahsulot ma'lumotlari</b>\n\n"
        f"<b>Mijoz:</b> {data['client_name'] or 'Ismsiz'}\n"
        f"<b>Telefon:</b> {data['phone']}\n"
        f"<b>Telegram ID:</b> {data['telegram_id']}\n"
        f"───────────────\n"
        f"<b>Mahsulot:</b> {data['product_name']}\n"
        f"<b>Kg:</b> {kg_amount}\n"
        f"<b>1 kg narxi:</b> {price_per_kg:,.0f} so'm\n"
        f"<b>Saqlash muddati:</b> {days} kun\n"
        f"───────────────\n"
        f"<b>Umumiy summa:</b> {total_price:,.0f} so'm\n\n"
        f"Bazaga saqlansinmi?"
    )

    await state.set_state(AdminAddProduct.waiting_for_confirmation)
    await message.answer(summary, reply_markup=confirmation_kb())


@router.message(AdminAddProduct.waiting_for_confirmation, F.text)
async def add_product_confirm(message: Message, state: FSMContext):
    text = message.text.strip()

    if text == "❌ Bekor qilish":
        await cancel_flow(message, state)
        return

    if text == "Ha ✅":
        data = await state.get_data()
        await create_product(
            client_id=data["client_id"],
            telegram_id=data["telegram_id"],
            phone=data["phone"],
            client_name=data["client_name"],
            product_name=data["product_name"],
            kg_amount=data["kg_amount"],
            price_per_kg=data["price_per_kg"],
            storage_days=data["storage_days"],
            total_price=data["total_price"],
        )

        product = {
            **data,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "active",
        }
        await state.clear()

        if not sheets_service.is_configured():
            await message.answer(
                "Mahsulot SQLite bazaga saqlandi ✅. "
                "Google Sheets sozlanmagan, shuning uchun Sheets'ga yozilmadi.",
                reply_markup=admin_panel_kb(),
            )
        elif await sheets_service.append_product_row(product):
            await message.answer(
                "Mahsulot bazaga saqlandi ✅",
                reply_markup=admin_panel_kb(),
            )
        else:
            await message.answer(
                "Mahsulot SQLite bazaga saqlandi ✅, "
                "lekin Google Sheets'ga yozishda xatolik bo'ldi ⚠️",
                reply_markup=admin_panel_kb(),
            )

    elif text == "Yo'q ❌":
        await state.clear()
        await message.answer(
            "Jarayon bekor qilindi.",
            reply_markup=admin_panel_kb(),
        )

    else:
        await message.answer(
            "Iltimos, quyidagi tugmalardan birini tanlang:",
            reply_markup=confirmation_kb(),
        )


@router.message(AdminAddProduct.waiting_for_confirmation)
async def add_product_confirm_invalid(message: Message):
    await message.answer(
        "Iltimos, quyidagi tugmalardan birini tanlang:",
        reply_markup=confirmation_kb(),
    )


async def cancel_flow(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Jarayon bekor qilindi.",
        reply_markup=admin_panel_kb(),
    )


@router.message(F.text == "❌ Bekor qilish", StateFilter(AdminAddProduct))
async def cancel_product_flow(message: Message, state: FSMContext):
    await cancel_flow(message, state)


@router.message(F.text == "📋 Mijozlarni ko'rish", IsAdmin())
async def list_clients(message: Message):
    clients = await get_all_clients()
    text = format_client_list(clients)
    await message.answer(text, reply_markup=admin_panel_kb())


@router.message(F.text == "📊 Hisobot", IsAdmin())
async def admin_stats(message: Message):
    stats = await get_admin_stats()
    text = format_admin_stats(stats)
    await message.answer(text, reply_markup=admin_panel_kb())
