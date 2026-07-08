from aiogram import Router, F
from aiogram.filters import Command, Filter, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from datetime import datetime, timezone
import logging

from app.config import config
from app.database import (
    create_product,
    create_payment,
    exit_product,
    get_admin_stats,
    get_all_clients,
    get_payment_by_id,
    get_product_by_id,
    get_product_payment_summary,
    get_user_by_phone,
    mark_product_in_ombor_sheet,
    get_sheet_visible_active_products_by_client_id,
)
from app.services.calculation_service import (
    calculate_total_price,
    calculate_remaining_amount,
    validate_payment_amount,
)
from app.services.formatting_service import (
    format_active_products_for_exit,
    format_active_products_for_payment,
    format_admin_stats,
    format_client_list,
)
from app.keyboards import admin_panel_kb, cancel_kb, confirmation_kb
from app.services.sheets_service import sheets_service
from app.states import AdminAddProduct, AdminExitProduct, AdminAddPayment
from app.utils.validators import (
    normalize_phone,
    validate_phone_number,
    validate_positive_int,
    validate_quantity,
)

logger = logging.getLogger(__name__)

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
    await state.set_state(AdminAddProduct.waiting_for_box_count)
    await message.answer(
        "Qutilar sonini kiriting:\n\nMasalan: 5",
        reply_markup=cancel_kb(),
    )


@router.message(AdminAddProduct.waiting_for_box_count, F.text)
async def add_product_box_count(message: Message, state: FSMContext):
    text = message.text.strip()

    if text == "❌ Bekor qilish":
        await cancel_flow(message, state)
        return

    box_count = validate_positive_int(text)
    if box_count is None:
        await message.answer(
            "Noto'g'ri qiymat. Faqat musbat butun son kiriting.\n\nMasalan: 5",
            reply_markup=cancel_kb(),
        )
        return

    data = await state.update_data(box_count=box_count)

    kg_amount = data["kg_amount"]
    price_per_kg = data["price_per_kg"]
    total_price = calculate_total_price(kg_amount, price_per_kg)

    await state.update_data(total_price=total_price)

    summary = (
        f"📋 <b>Mahsulot ma'lumotlari</b>\n\n"
        f"<b>Mijoz:</b> {data['client_name'] or 'Ismsiz'}\n"
        f"<b>Telefon:</b> {data['phone']}\n"
        f"<b>Telegram ID:</b> {data['telegram_id']}\n"
        f"───────────────\n"
        f"<b>Mahsulot:</b> {data['product_name']}\n"
        f"<b>Kg:</b> {kg_amount}\n"
        f"<b>Qutilar soni:</b> {box_count}\n"
        f"<b>1 kg narxi:</b> {price_per_kg:,.0f} so'm\n"
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
        try:
            data = await state.get_data()
            product_id = await create_product(
                client_id=data["client_id"],
                telegram_id=data["telegram_id"],
                phone=data["phone"],
                client_name=data["client_name"],
                product_name=data["product_name"],
                kg_amount=data["kg_amount"],
                price_per_kg=data["price_per_kg"],
                box_count=data["box_count"],
                total_price=data["total_price"],
            )

            product_data = {
                **data,
                "id": product_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "active",
            }

            sheets_ok = False
            if sheets_service.is_configured():
                try:
                    sheets_ok = await sheets_service.append_product_row(product_data)
                except Exception:
                    logger.exception("Sheets append product crashed")
                    sheets_ok = False

            if sheets_ok:
                await mark_product_in_ombor_sheet(product_id, True)
                await message.answer(
                    "Mahsulot bazaga va Google Sheets'ga saqlandi ✅",
                    reply_markup=admin_panel_kb(),
                )
            else:
                await message.answer(
                    "Mahsulot SQLite bazaga saqlandi ✅, "
                    "lekin Google Sheets'ga yozishda xatolik bo'ldi ⚠️",
                    reply_markup=admin_panel_kb(),
                )
        except Exception:
            logger.exception("Product confirm failed")
            await message.answer(
                "Mahsulot saqlashda xatolik bo'ldi ❌",
                reply_markup=admin_panel_kb(),
            )
        finally:
            await state.clear()

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


@router.message(F.text == "❌ Bekor qilish",
                StateFilter(AdminAddProduct, AdminExitProduct, AdminAddPayment))
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


@router.message(F.text == "📤 Mahsulot chiqarish", IsAdmin())
async def exit_product_start(message: Message, state: FSMContext):
    await state.set_state(AdminExitProduct.waiting_for_client_phone)
    await message.answer(
        "Mijozning telefon raqamini kiriting:\n\n"
        "Masalan: +998901234567 yoki 901234567",
        reply_markup=cancel_kb(),
    )


@router.message(AdminExitProduct.waiting_for_client_phone, F.text)
async def exit_product_client_phone(message: Message, state: FSMContext):
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
            "Bu telefon raqam bilan ro'yxatdan o'tgan mijoz topilmadi.",
            reply_markup=cancel_kb(),
        )
        return

    products = await get_sheet_visible_active_products_by_client_id(user["id"])
    if not products:
        await message.answer(
            "Bu mijozda faol mahsulotlar mavjud emas.",
            reply_markup=admin_panel_kb(),
        )
        await state.clear()
        return

    await state.update_data(
        client_id=user["id"],
        client_telegram_id=user["telegram_id"],
        client_phone=user["phone"],
        client_name=user["full_name"],
        products=products,
    )

    await state.set_state(AdminExitProduct.waiting_for_product_id)
    await message.answer(
        format_active_products_for_exit(products),
        reply_markup=cancel_kb(),
    )


@router.message(AdminExitProduct.waiting_for_product_id, F.text)
async def exit_product_select(message: Message, state: FSMContext):
    text = message.text.strip()

    if text == "❌ Bekor qilish":
        await cancel_flow(message, state)
        return

    data = await state.get_data()
    try:
        product_id = int(text)
    except ValueError:
        await message.answer(
            "Noto'g'ri ID. Mahsulot ID sini raqam ko'rinishida kiriting:",
            reply_markup=cancel_kb(),
        )
        return

    product = await get_product_by_id(product_id)
    if product is None:
        await message.answer(
            "Bu ID bilan mahsulot topilmadi. Qaytadan kiriting:",
            reply_markup=cancel_kb(),
        )
        return

    if product["status"] != "active":
        await message.answer(
            "Bu mahsulot allaqachon chiqim qilingan yoki faol emas. Boshqa ID kiriting:",
            reply_markup=cancel_kb(),
        )
        return

    if product["phone"] != data["client_phone"]:
        await message.answer(
            "Bu mahsulot ushbu mijozga tegishli emas. Boshqa ID kiriting:",
            reply_markup=cancel_kb(),
        )
        return

    summary = await get_product_payment_summary(product_id)
    paid = summary["paid_amount"]
    rem = summary["remaining_amount"]

    await state.update_data(
        selected_product_id=product["id"],
        selected_product_name=product["product_name"],
        selected_kg=product["kg_amount"],
        selected_box_count=product.get("box_count", 0),
        selected_price=product["price_per_kg"],
        selected_total=product["total_price"],
        selected_paid=paid,
        selected_remaining=rem,
    )

    debt_warning = ""
    if rem > 0:
        debt_warning = f"\n\n⚠️ <b>Diqqat:</b> bu mahsulot bo'yicha qolgan qarz bor: {rem:,.0f} so'm"

    summary_text = (
        f"📤 <b>Chiqim tasdiqlash</b>\n\n"
        f"<b>Mijoz:</b> {data['client_name'] or 'Ismsiz'}\n"
        f"<b>Telefon:</b> {data['client_phone']}\n"
        f"───────────────\n"
        f"<b>Product ID:</b> {product['id']}\n"
        f"<b>Mahsulot:</b> {product['product_name']}\n"
        f"<b>Kg:</b> {product['kg_amount']}\n"
        f"<b>Qutilar soni:</b> {product.get('box_count', 0)}\n"
        f"<b>Umumiy summa:</b> {product['total_price']:,.0f} so'm\n"
        f"<b>To'langan:</b> {paid:,.0f} so'm\n"
        f"<b>Qolgan:</b> {rem:,.0f} so'm"
        f"{debt_warning}\n\n"
        f"Chiqim qilinsinmi?"
    )

    await state.set_state(AdminExitProduct.waiting_for_confirmation)
    await message.answer(summary_text, reply_markup=confirmation_kb())


@router.message(AdminExitProduct.waiting_for_confirmation, F.text)
async def exit_product_confirm(message: Message, state: FSMContext):
    text = message.text.strip()

    if text == "❌ Bekor qilish":
        await cancel_flow(message, state)
        return

    if text == "Ha ✅":
        try:
            data = await state.get_data()
            exit_data = await exit_product(
                product_id=data["selected_product_id"],
                admin_id=message.from_user.id,
            )

            if exit_data is None:
                await message.answer(
                    "Chiqim qilishda xatolik bo'ldi yoki mahsulot allaqachon chiqim qilingan.",
                    reply_markup=admin_panel_kb(),
                )
            else:
                sheets_ok = False
                if sheets_service.is_configured():
                    try:
                        sheets_ok = await sheets_service.move_product_to_exited(
                            exit_data,
                            paid_amount=data.get("selected_paid", 0),
                            remaining_amount=data.get("selected_remaining", 0),
                        )
                    except Exception:
                        logger.exception("Sheets move to exited crashed")
                        sheets_ok = False

                if sheets_ok:
                    await message.answer(
                        "Mahsulot SQLite va Google Sheets'da chiqim qilindi ✅",
                        reply_markup=admin_panel_kb(),
                    )
                else:
                    await message.answer(
                        "Mahsulot SQLite bazada chiqim qilindi ✅, "
                        "lekin Google Sheets'ga yozishda xatolik bo'ldi ⚠️",
                        reply_markup=admin_panel_kb(),
                    )
        except Exception:
            logger.exception("Exit confirm failed")
            await message.answer(
                "Chiqimda xatolik bo'ldi ❌",
                reply_markup=admin_panel_kb(),
            )
        finally:
            await state.clear()

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


@router.message(AdminExitProduct.waiting_for_confirmation)
async def exit_product_confirm_invalid(message: Message):
    await message.answer(
        "Iltimos, quyidagi tugmalardan birini tanlang:",
        reply_markup=confirmation_kb(),
    )


@router.message(F.text == "💳 To'lov kiritish", IsAdmin())
async def payment_start(message: Message, state: FSMContext):
    await state.set_state(AdminAddPayment.waiting_for_client_phone)
    await message.answer(
        "Mijozning telefon raqamini kiriting:\n\n"
        "Masalan: +998901234567 yoki 901234567",
        reply_markup=cancel_kb(),
    )


@router.message(AdminAddPayment.waiting_for_client_phone, F.text)
async def payment_client_phone(message: Message, state: FSMContext):
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
            "Bu telefon raqam bilan ro'yxatdan o'tgan mijoz topilmadi.",
            reply_markup=cancel_kb(),
        )
        return

    products = await get_sheet_visible_active_products_by_client_id(user["id"])
    if not products:
        await message.answer(
            "Bu mijozda omborda aktiv mahsulot yo'q.",
            reply_markup=admin_panel_kb(),
        )
        await state.clear()
        return

    payment_summaries = {}
    for p in products:
        payment_summaries[p["id"]] = await get_product_payment_summary(p["id"])

    await state.update_data(
        client_id=user["id"],
        telegram_id=user["telegram_id"],
        phone=user["phone"],
        client_name=user["full_name"],
        products=products,
        payment_summaries=payment_summaries,
    )

    await state.set_state(AdminAddPayment.waiting_for_product_id)
    await message.answer(
        format_active_products_for_payment(products, payment_summaries),
        reply_markup=cancel_kb(),
    )


@router.message(AdminAddPayment.waiting_for_product_id, F.text)
async def payment_product_select(message: Message, state: FSMContext):
    text = message.text.strip()

    if text == "❌ Bekor qilish":
        await cancel_flow(message, state)
        return

    data = await state.get_data()
    try:
        product_id = int(text)
    except ValueError:
        await message.answer(
            "Noto'g'ri ID. Mahsulot ID sini raqam ko'rinishida kiriting:",
            reply_markup=cancel_kb(),
        )
        return

    product = await get_product_by_id(product_id)
    if product is None:
        await message.answer(
            "Bu ID bilan mahsulot topilmadi. Qaytadan kiriting:",
            reply_markup=cancel_kb(),
        )
        return

    if product["status"] != "active":
        await message.answer(
            "Bu mahsulot allaqachon chiqim qilingan yoki faol emas. Boshqa ID kiriting:",
            reply_markup=cancel_kb(),
        )
        return

    if product["phone"] != data["client_phone"]:
        await message.answer(
            "Bu mahsulot ushbu mijozga tegishli emas. Boshqa ID kiriting:",
            reply_markup=cancel_kb(),
        )
        return

    summary = await get_product_payment_summary(product_id)
    paid = summary["paid_amount"]
    rem = summary["remaining_amount"]

    if rem <= 0:
        await message.answer(
            "Bu mahsulot uchun to'lov to'liq qilingan.",
            reply_markup=cancel_kb(),
        )
        return

    await state.update_data(
        selected_product_id=product["id"],
        selected_product_name=product["product_name"],
        selected_total=product["total_price"],
        selected_paid=paid,
        selected_remaining=rem,
    )

    await state.set_state(AdminAddPayment.waiting_for_amount)
    await message.answer(
        f"Bu mahsulot bo'yicha qolgan summa: <b>{rem:,.0f} so'm</b>\n\n"
        f"To'lov summasini kiriting:\n\n"
        f"Masalan: {rem:,.0f}",
        reply_markup=cancel_kb(),
    )


@router.message(AdminAddPayment.waiting_for_amount, F.text)
async def payment_amount(message: Message, state: FSMContext):
    text = message.text.strip()

    if text == "❌ Bekor qilish":
        await cancel_flow(message, state)
        return

    amount = validate_quantity(text)
    if amount is None:
        await message.answer(
            "Noto'g'ri summa. Faqat musbat son kiriting.",
            reply_markup=cancel_kb(),
        )
        return

    data = await state.get_data()
    remaining = data.get("selected_remaining", 0)

    valid, error_msg = validate_payment_amount(amount, remaining)
    if not valid:
        await message.answer(error_msg, reply_markup=cancel_kb())
        return

    new_remaining = calculate_remaining_amount(data["selected_total"], data["selected_paid"] + amount)

    await state.update_data(amount=amount, new_remaining=new_remaining)

    summary_text = (
        f"💳 <b>To'lov tasdiqlash</b>\n\n"
        f"<b>Mijoz:</b> {data['client_name'] or 'Ismsiz'}\n"
        f"<b>Telefon:</b> {data['phone']}\n"
        f"───────────────\n"
        f"<b>Product ID:</b> {data['selected_product_id']}\n"
        f"<b>Mahsulot:</b> {data['selected_product_name']}\n"
        f"<b>Umumiy summa:</b> {data['selected_total']:,.0f} so'm\n"
        f"<b>Oldin to'langan:</b> {data['selected_paid']:,.0f} so'm\n"
        f"<b>Qolgan:</b> {data['selected_remaining']:,.0f} so'm\n"
        f"───────────────\n"
        f"<b>To'lov summasi:</b> {amount:,.0f} so'm\n"
        f"<b>To'lovdan keyin qolgan:</b> {new_remaining:,.0f} so'm\n\n"
        f"To'lov bazaga saqlansinmi?"
    )

    await state.set_state(AdminAddPayment.waiting_for_confirmation)
    await message.answer(summary_text, reply_markup=confirmation_kb())


@router.message(AdminAddPayment.waiting_for_confirmation, F.text)
async def payment_confirm(message: Message, state: FSMContext):
    text = message.text.strip()

    if text == "❌ Bekor qilish":
        await cancel_flow(message, state)
        return

    if text == "Ha ✅":
        try:
            data = await state.get_data()
            payment = await create_payment(
                client_id=data["client_id"],
                product_id=data["selected_product_id"],
                telegram_id=data["telegram_id"],
                phone=data["phone"],
                client_name=data["client_name"],
                amount=data["amount"],
                created_by_admin_id=message.from_user.id,
            )

            if payment is None:
                await message.answer(
                    "To'lovni saqlashda xatolik bo'ldi.",
                    reply_markup=admin_panel_kb(),
                )
            else:
                summary = await get_product_payment_summary(data["selected_product_id"])

                sheets_ok = False
                if sheets_service.is_configured():
                    try:
                        sheets_ok = await sheets_service.append_payment_history(payment)
                        if sheets_ok:
                            await sheets_service.update_product_payment(
                                data["selected_product_id"],
                                summary["paid_amount"],
                                summary["remaining_amount"],
                            )
                    except Exception:
                        logger.exception("Sheets payment crashed")
                        sheets_ok = False

                if sheets_ok:
                    await message.answer(
                        "To'lov bazaga va Google Sheets'ga saqlandi ✅",
                        reply_markup=admin_panel_kb(),
                    )
                else:
                    await message.answer(
                        "To'lov SQLite bazaga saqlandi ✅, "
                        "lekin Google Sheets'ga yozishda xatolik bo'ldi ⚠️",
                        reply_markup=admin_panel_kb(),
                    )
        except Exception:
            logger.exception("Payment confirm failed")
            await message.answer(
                "To'lov saqlashda xatolik bo'ldi ❌",
                reply_markup=admin_panel_kb(),
            )
        finally:
            await state.clear()

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


@router.message(AdminAddPayment.waiting_for_confirmation)
async def payment_confirm_invalid(message: Message):
    await message.answer(
        "Iltimos, quyidagi tugmalardan birini tanlang:",
        reply_markup=confirmation_kb(),
    )
