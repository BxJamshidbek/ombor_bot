from aiogram import Bot, Router, F
from aiogram.filters import Command, Filter, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

import asyncio
from datetime import datetime, timezone
import logging

from app.config import config
from app.database import (
    create_product,
    create_payment,
    create_product_type,
    exit_product,
    get_active_product_types,
    get_admin_stats,
    get_all_clients,
    get_payment_by_id,
    get_product_by_id,
    get_product_payment_summary,
    get_product_type_by_id,
    get_products_by_client_id,
    get_user_by_id,
    get_user_by_phone,
    mark_product_in_ombor_sheet,
    get_sheet_visible_active_products_by_client_id,
    get_warehouse_location,
    save_warehouse_location,
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
    format_client_products_message,
    format_product_types_list,
)
from app.services.notification_service import notify_product_assigned, notify_payment_received, notify_product_exited
from app.keyboards import (
    admin_panel_kb,
    admin_main_kb,
    confirmation_kb,
    clients_list_kb,
    client_actions_kb,
    client_products_kb,
    menu_only_kb,
    product_type_selection_kb,
    settings_kb,
    warehouse_location_confirm_kb,
)
from app.services.sheets_service import sheets_service
from app.states import AdminAddProduct, AdminExitProduct, AdminAddPayment, AdminSettings, AdminWarehouseLocation
from app.utils.validators import (
    normalize_phone,
    validate_phone_number,
    validate_positive_int,
    validate_quantity,
    validate_coordinates,
    build_google_maps_url,
)

logger = logging.getLogger(__name__)

router = Router()


class IsAdmin(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in config.admin_ids


class IsAdminCallback(Filter):
    async def __call__(self, callback: CallbackQuery) -> bool:
        return callback.from_user.id in config.admin_ids


def _parse_client_id(data: str) -> int | None:
    try:
        return int(data.split(":", 1)[1])
    except (ValueError, IndexError):
        return None


@router.message(F.text == "☰ Menu", IsAdmin())
async def back_to_admin_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Admin panelga qaytdingiz.",
        reply_markup=admin_main_kb(),
    )


@router.message(Command("admin"), IsAdmin())
async def admin_panel(message: Message):
    await message.answer(
        "👑 Admin panel. Kerakli bo‘limni tanlang:",
        reply_markup=admin_panel_kb(),
    )


@router.message(Command("admin"))
async def admin_panel_denied(message: Message):
    await message.answer("Sizda admin panelga kirish huquqi yo'q.")


@router.message(F.text == "➕ Mahsulot qo'shish", IsAdmin())
async def add_product_start(message: Message, state: FSMContext):
    await message.answer(
        "Avval 📋 Mijozlarni ko'rish orqali mijozni tanlang.",
        reply_markup=admin_main_kb(),
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
            reply_markup=menu_only_kb(),
        )
        return

    user = await get_user_by_phone(normalized)
    if user is None:
        await message.answer(
            "Bu telefon raqam bilan ro'yxatdan o'tgan mijoz topilmadi. "
            "Avval mijoz botga /start bosib telefon raqamini ulashishi kerak.",
            reply_markup=menu_only_kb(),
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
        reply_markup=menu_only_kb(),
    )


@router.message(AdminAddProduct.waiting_for_product_name, F.text)
async def add_product_name(message: Message, state: FSMContext):
    text = message.text.strip()

    if text == "⬅️ Mijozga qaytish":
        data = await state.get_data()
        client_id = data.get("client_id")
        await state.clear()
        if client_id:
            user = await get_user_by_id(client_id)
            if user:
                detail_text = (
                    f"👤 <b>Mijoz:</b> {user['full_name'] or 'Ismsiz'}\n"
                    f"<b>Telefon:</b> {user['phone']}\n"
                    f"<b>Telegram ID:</b> {user['telegram_id']}"
                )
                await message.answer(
                    "Mahsulot kiritish bekor qilindi.",
                    reply_markup=menu_only_kb(),
                )
                await message.answer(
                    detail_text,
                    reply_markup=client_actions_kb(client_id),
                )
                return
        await message.answer(
            "Mahsulot kiritish bekor qilindi.",
            reply_markup=admin_main_kb(),
        )
        return

    if text == "❌ Bekor qilish":
        await cancel_flow(message, state)
        return

    if not text:
        await message.answer(
            "Mahsulot nomi bo'sh bo'lmasligi kerak. Qaytadan kiriting:",
            reply_markup=menu_only_kb(),
        )
        return

    await state.update_data(product_name=text)
    await state.set_state(AdminAddProduct.waiting_for_kg_amount)
    await message.answer(
        "Mahsulot miqdorini kg da kiriting:\n\nMasalan: 10.5",
        reply_markup=menu_only_kb(),
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
            reply_markup=menu_only_kb(),
        )
        return

    await state.update_data(kg_amount=kg)
    await state.set_state(AdminAddProduct.waiting_for_price_per_kg)
    await message.answer(
        "1 kg uchun narxni so'mda kiriting:\n\nMasalan: 2000",
        reply_markup=menu_only_kb(),
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
            reply_markup=menu_only_kb(),
        )
        return

    await state.update_data(price_per_kg=price)
    await state.set_state(AdminAddProduct.waiting_for_box_count)
    await message.answer(
        "Qutilar sonini kiriting:\n\nMasalan: 5",
        reply_markup=menu_only_kb(),
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
            reply_markup=menu_only_kb(),
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
async def add_product_confirm(message: Message, state: FSMContext, bot: Bot):
    text = message.text.strip()

    if text == "❌ Bekor qilish":
        await cancel_flow(message, state)
        return

    if text == "Ha ✅":
        logger.info("add_product_confirm: started chat_id=%s", message.chat.id)
        try:
            data = await state.get_data()
            logger.info("add_product_confirm: state loaded keys=%s", list(data.keys()))

            existing_product_id = data.get("created_product_id")
            if existing_product_id:
                logger.warning("add_product_confirm: duplicate confirmation blocked existing_product_id=%s", existing_product_id)
                await message.answer(
                    "Mahsulot allaqachon yaratilgan. Qayta urinish bloklandi.",
                    reply_markup=admin_panel_kb(),
                )
                return

            logger.info("add_product_confirm: create_product start")
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
            logger.info("add_product_confirm: product created product_id=%s", product_id)

            await state.update_data(created_product_id=product_id)
            logger.info("add_product_confirm: saved created_product_id in state")

            product_data = {
                **data,
                "id": product_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "active",
            }
            logger.info("add_product_confirm: product_data prepared")

            sheets_ok = False
            if sheets_service.is_configured():
                try:
                    logger.info("add_product_confirm: sheets start")
                    sheets_ok = await asyncio.wait_for(
                        sheets_service.append_product_row(product_data),
                        timeout=20,
                    )
                    logger.info("add_product_confirm: sheets append done result=%s", sheets_ok)
                except asyncio.TimeoutError:
                    logger.warning("add_product_confirm: Sheets append timed out")
                    sheets_ok = False
                except Exception:
                    logger.exception("add_product_confirm: Sheets append product crashed")
                    sheets_ok = False

            if sheets_ok:
                await mark_product_in_ombor_sheet(product_id, True)
                logger.info("add_product_confirm: marked product in ombor sheet")
            else:
                logger.info("add_product_confirm: sheets skipped or failed")

            notification_ok = False
            try:
                logger.info("add_product_confirm: notification start")
                notification_ok = await asyncio.wait_for(
                    notify_product_assigned(
                        bot=bot,
                        telegram_id=data["telegram_id"],
                        product=product_data,
                    ),
                    timeout=10,
                )
                logger.info("add_product_confirm: notification done result=%s", notification_ok)
            except asyncio.TimeoutError:
                logger.warning("add_product_confirm: Product notification timed out")
                notification_ok = False
            except Exception:
                logger.exception("add_product_confirm: Product notification failed")
                notification_ok = False

            if sheets_ok:
                msg = "Mahsulot bazaga va Google Sheets'ga saqlandi ✅"
            else:
                msg = "Mahsulot SQLite bazaga saqlandi ✅\nGoogle Sheets'ga yozishda xatolik bo'ldi ⚠️"

            if notification_ok:
                msg += "\nMijozga bildirishnoma yuborildi ✅"
            else:
                msg += "\nMijozga bildirishnoma yuborilmadi ⚠️"

            await message.answer(msg, reply_markup=admin_panel_kb())
            logger.info("add_product_confirm: admin response sent")
        except Exception:
            logger.exception("add_product_confirm: Product confirm failed")
            await message.answer(
                "Mahsulot saqlashda xatolik bo'ldi ❌",
                reply_markup=admin_panel_kb(),
            )
        finally:
            try:
                await state.clear()
                logger.info("add_product_confirm: state cleared")
            except Exception:
                logger.exception("add_product_confirm: state clear failed")

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
    if not clients:
        await message.answer("Hozircha mijozlar yo'q.", reply_markup=admin_main_kb())
        return
    menu_message = await message.answer(
        "Mijozlar bo'limi ochildi. Bosh menyuga qaytish uchun ☰ Menu tugmasini bosing.",
        reply_markup=menu_only_kb(),
    )
    logger.info(
        "Menu-only keyboard shown (permanent): chat_id=%s message_id=%s",
        menu_message.chat.id,
        menu_message.message_id,
    )
    clients_message = await message.answer(
        "Mijozni tanlang:", reply_markup=clients_list_kb(clients)
    )
    logger.info(
        "Client list message sent (permanent): chat_id=%s message_id=%s clients=%s",
        clients_message.chat.id,
        clients_message.message_id,
        len(clients),
    )


@router.message(F.text == "📊 Hisobot", IsAdmin())
async def admin_stats(message: Message):
    stats = await get_admin_stats()
    text = format_admin_stats(stats)
    await message.answer(text, reply_markup=admin_panel_kb())


@router.callback_query(IsAdminCallback(), F.data.startswith("client:"))
async def client_selected(callback: CallbackQuery, state: FSMContext):
    client_id = _parse_client_id(callback.data)
    if client_id is None:
        await callback.answer("Noto'g'ri mijoz.", show_alert=True)
        return

    user = await get_user_by_id(client_id)
    if user is None:
        await callback.answer("Mijoz topilmadi.", show_alert=True)
        return

    text = (
        f"👤 <b>Mijoz:</b> {user['full_name'] or 'Ismsiz'}\n"
        f"<b>Telefon:</b> {user['phone']}\n"
        f"<b>Telegram ID:</b> {user['telegram_id']}"
    )
    await callback.message.edit_text(text, reply_markup=client_actions_kb(client_id))
    await callback.answer()


@router.callback_query(IsAdminCallback(), F.data == "clients_back")
async def clients_back(callback: CallbackQuery, state: FSMContext):
    clients = await get_all_clients()
    if not clients:
        await callback.message.edit_text("Hozircha mijozlar yo'q.", reply_markup=None)
        await callback.answer()
        return
    await callback.message.edit_text(
        "Mijozni tanlang:", reply_markup=clients_list_kb(clients)
    )
    await callback.answer()


@router.callback_query(IsAdminCallback(), F.data.startswith("client_add_product:"))
async def client_add_product(callback: CallbackQuery, state: FSMContext):
    client_id = _parse_client_id(callback.data)
    if client_id is None:
        await callback.answer("Noto'g'ri mijoz.", show_alert=True)
        return

    user = await get_user_by_id(client_id)
    if user is None:
        await callback.answer("Mijoz topilmadi.", show_alert=True)
        return

    product_types = await get_active_product_types()
    await callback.message.edit_text(
        "Mahsulot turini tanlang:",
        reply_markup=product_type_selection_kb(client_id, product_types),
    )
    await callback.answer()


@router.callback_query(IsAdminCallback(), F.data.startswith("pt_select:"))
async def product_type_selected(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":", 2)
    try:
        client_id = int(parts[1])
        type_id = int(parts[2])
    except (ValueError, IndexError):
        await callback.answer("Noto'g'ri ma'lumot.", show_alert=True)
        return

    user = await get_user_by_id(client_id)
    if user is None:
        await callback.answer("Mijoz topilmadi.", show_alert=True)
        return

    pt = await get_product_type_by_id(type_id)
    if pt is None:
        await callback.answer("Mahsulot turi topilmadi.", show_alert=True)
        return

    await state.update_data(
        client_id=user["id"],
        telegram_id=user["telegram_id"],
        phone=user["phone"],
        client_name=user["full_name"],
        product_name=pt["name"],
    )
    await state.set_state(AdminAddProduct.waiting_for_kg_amount)
    await callback.message.edit_text(
        f"✅ Mahsulot: {pt['emoji']} {pt['name']}\n"
        f"👤 Mijoz: {user['full_name'] or 'Ismsiz'} ({user['phone']})\n\n"
        "Mahsulot miqdorini kg da kiriting:\n\nMasalan: 10.5",
    )
    await callback.answer()


@router.callback_query(IsAdminCallback(), F.data.startswith("pt_custom:"))
async def product_type_custom(callback: CallbackQuery, state: FSMContext):
    try:
        client_id = int(callback.data.split(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("Noto'g'ri mijoz.", show_alert=True)
        return

    user = await get_user_by_id(client_id)
    if user is None:
        await callback.answer("Mijoz topilmadi.", show_alert=True)
        return

    await state.update_data(
        client_id=user["id"],
        telegram_id=user["telegram_id"],
        phone=user["phone"],
        client_name=user["full_name"],
    )
    await state.set_state(AdminAddProduct.waiting_for_product_name)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        f"✅ Mijoz: {user['full_name'] or 'Ismsiz'} ({user['phone']})\n\n"
        "Mahsulot nomini kiriting:",
        reply_markup=menu_only_kb(),
    )
    await callback.answer()


@router.callback_query(IsAdminCallback(), F.data.startswith("client_add_payment:"))
async def client_add_payment(callback: CallbackQuery, state: FSMContext):
    client_id = _parse_client_id(callback.data)
    if client_id is None:
        await callback.answer("Noto'g'ri mijoz.", show_alert=True)
        return

    user = await get_user_by_id(client_id)
    if user is None:
        await callback.answer("Mijoz topilmadi.", show_alert=True)
        return

    products = await get_sheet_visible_active_products_by_client_id(user["id"])
    if not products:
        await callback.answer(
            "Bu mijozda omborda aktiv mahsulot yo'q.", show_alert=True
        )
        return

    payment_summaries = {
        p["id"]: await get_product_payment_summary(p["id"]) for p in products
    }
    await state.update_data(
        client_id=user["id"],
        telegram_id=user["telegram_id"],
        phone=user["phone"],
        client_name=user["full_name"],
        products=products,
        payment_summaries=payment_summaries,
    )
    await state.set_state(AdminAddPayment.waiting_for_product_id)
    await callback.message.edit_text(
        format_active_products_for_payment(products, payment_summaries)
    )
    await callback.answer()


@router.callback_query(IsAdminCallback(), F.data.startswith("client_exit_product:"))
async def client_exit_product(callback: CallbackQuery, state: FSMContext):
    client_id = _parse_client_id(callback.data)
    if client_id is None:
        await callback.answer("Noto'g'ri mijoz.", show_alert=True)
        return

    user = await get_user_by_id(client_id)
    if user is None:
        await callback.answer("Mijoz topilmadi.", show_alert=True)
        return

    products = await get_sheet_visible_active_products_by_client_id(user["id"])
    if not products:
        await callback.answer(
            "Bu mijozda faol mahsulotlar mavjud emas.", show_alert=True
        )
        return

    await state.update_data(
        client_id=user["id"],
        client_telegram_id=user["telegram_id"],
        client_phone=user["phone"],
        client_name=user["full_name"],
        products=products,
    )
    await state.set_state(AdminExitProduct.waiting_for_product_id)
    await callback.message.edit_text(format_active_products_for_exit(products))
    await callback.answer()


@router.callback_query(IsAdminCallback(), F.data.startswith("client_products:"))
async def client_products_handler(callback: CallbackQuery, state: FSMContext):
    client_id = _parse_client_id(callback.data)
    if client_id is None:
        await callback.answer("Noto'g'ri mijoz.", show_alert=True)
        return

    user = await get_user_by_id(client_id)
    if user is None:
        await callback.answer("Mijoz topilmadi.", show_alert=True)
        return

    products = await get_products_by_client_id(user["id"])
    text = format_client_products_message(user, products)
    await callback.message.edit_text(
        text, reply_markup=client_products_kb(client_id),
    )
    await callback.answer()


@router.callback_query(IsAdminCallback(), F.data.startswith("client_back_detail:"))
async def client_back_detail(callback: CallbackQuery, state: FSMContext):
    client_id = _parse_client_id(callback.data)
    if client_id is None:
        await callback.answer("Noto'g'ri mijoz.", show_alert=True)
        return

    user = await get_user_by_id(client_id)
    if user is None:
        await callback.answer("Mijoz topilmadi.", show_alert=True)
        return

    text = (
        f"👤 <b>Mijoz:</b> {user['full_name'] or 'Ismsiz'}\n"
        f"<b>Telefon:</b> {user['phone']}\n"
        f"<b>Telegram ID:</b> {user['telegram_id']}"
    )
    await callback.message.edit_text(text, reply_markup=client_actions_kb(client_id))
    await callback.answer()


@router.message(F.text == "⚙️ Sozlash", IsAdmin())
async def admin_settings(message: Message):
    await message.answer(
        "Sozlash bo'limi ochildi. Bosh menyuga qaytish uchun ☰ Menu tugmasini bosing.",
        reply_markup=menu_only_kb(),
    )
    await message.answer(
        "Kerakli bo'limni tanlang:",
        reply_markup=settings_kb(),
    )


@router.callback_query(IsAdminCallback(), F.data == "settings_product_types")
async def settings_show_product_types(callback: CallbackQuery):
    types = await get_active_product_types()
    text = format_product_types_list(types)
    await callback.message.edit_text(text, reply_markup=settings_kb())
    await callback.answer()


@router.callback_query(IsAdminCallback(), F.data == "settings_add_product_type")
async def settings_add_product_type_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminSettings.waiting_for_product_type_name)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        "Yangi mahsulot turi nomini kiriting. Masalan: Anor",
        reply_markup=menu_only_kb(),
    )
    await callback.answer()


@router.message(AdminSettings.waiting_for_product_type_name, F.text == "❌ Bekor qilish")
async def settings_add_product_type_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Amal bekor qilindi.",
        reply_markup=menu_only_kb(),
    )
    await message.answer(
        "Kerakli bo'limni tanlang:",
        reply_markup=settings_kb(),
    )


@router.message(AdminSettings.waiting_for_product_type_name, F.text)
async def settings_add_product_type_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2 or len(name) > 50:
        await message.answer(
            "Mahsulot turi nomi kamida 2 ta va ko'pi bilan 50 ta belgidan iborat bo'lishi kerak.\n"
            "Qaytadan kiriting:",
            reply_markup=menu_only_kb(),
        )
        return

    pt_id = await create_product_type(name)
    if pt_id is None:
        await message.answer(
            f"Bu mahsulot turi allaqachon mavjud.",
            reply_markup=settings_kb(),
        )
        await state.clear()
        return

    await message.answer(
        f"✅ Mahsulot turi qo'shildi: 📦 {name}",
        reply_markup=settings_kb(),
    )
    await state.clear()


@router.callback_query(IsAdminCallback(), F.data == "settings:warehouse_location")
async def settings_warehouse_location_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminWarehouseLocation.waiting_for_location)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        "Telegram pastki qismidagi 📎 tugmasini bosing, Location tanlang va omborning aniq nuqtasini yuboring.",
        reply_markup=menu_only_kb(),
    )
    await callback.answer()


@router.message(AdminWarehouseLocation.waiting_for_location, F.location)
async def warehouse_location_received(message: Message, state: FSMContext):
    latitude = message.location.latitude
    longitude = message.location.longitude

    if not validate_coordinates(latitude, longitude):
        await message.answer(
            "Noto'g'ri lokatsiya. Iltimos, aniq lokatsiyani yuboring.",
            reply_markup=menu_only_kb(),
        )
        return

    await state.update_data(latitude=latitude, longitude=longitude)
    maps_url = build_google_maps_url(latitude, longitude)

    await message.answer_location(latitude=latitude, longitude=longitude)
    await message.answer(
        f"📍 <b>Ombor lokatsiyasi</b>\n\n"
        f"Latitude: {latitude:.7f}\n"
        f"Longitude: {longitude:.7f}\n\n"
        f"Shu lokatsiyani saqlaysizmi?",
        reply_markup=warehouse_location_confirm_kb(),
    )
    await state.set_state(AdminWarehouseLocation.waiting_for_confirmation)


@router.message(AdminWarehouseLocation.waiting_for_location, F.text == "❌ Bekor qilish")
async def warehouse_location_cancel_text(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Amal bekor qilindi.",
        reply_markup=menu_only_kb(),
    )
    await message.answer(
        "Kerakli bo'limni tanlang:",
        reply_markup=settings_kb(),
    )


@router.message(AdminWarehouseLocation.waiting_for_location, F.text)
async def warehouse_location_invalid(message: Message):
    await message.answer(
        "Iltimos, matn yoki link emas, Telegram'ning Location funksiyasi orqali lokatsiya yuboring.",
        reply_markup=menu_only_kb(),
    )


@router.callback_query(IsAdminCallback(), F.data == "warehouse_location:confirm")
async def warehouse_location_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    if latitude is None or longitude is None:
        await callback.answer("Lokatsiya ma'lumotlari topilmadi.", show_alert=True)
        await state.clear()
        return

    await save_warehouse_location(latitude, longitude)
    await state.clear()

    await callback.message.edit_text("Ombor lokatsiyasi saqlandi ✅")
    await callback.message.answer(
        "Kerakli bo'limni tanlang:",
        reply_markup=settings_kb(),
    )
    await callback.answer()


@router.callback_query(IsAdminCallback(), F.data == "warehouse_location:cancel")
async def warehouse_location_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Lokatsiya saqlanmadi.")
    await callback.message.answer(
        "Kerakli bo'limni tanlang:",
        reply_markup=settings_kb(),
    )
    await callback.answer()


@router.callback_query(IsAdminCallback(), F.data == "settings_back")
async def settings_back(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        "👑 Admin panel. Kerakli bo'limni tanlang:",
        reply_markup=admin_main_kb(),
    )
    await callback.answer()


@router.message(F.text == "📤 Mahsulot chiqarish", IsAdmin())
async def exit_product_start(message: Message, state: FSMContext):
    await message.answer(
        "Avval 📋 Mijozlarni ko'rish orqali mijozni tanlang.",
        reply_markup=admin_main_kb(),
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
            reply_markup=menu_only_kb(),
        )
        return

    user = await get_user_by_phone(normalized)
    if user is None:
        await message.answer(
            "Bu telefon raqam bilan ro'yxatdan o'tgan mijoz topilmadi.",
            reply_markup=menu_only_kb(),
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
        reply_markup=menu_only_kb(),
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
            reply_markup=menu_only_kb(),
        )
        return

    product = await get_product_by_id(product_id)
    if product is None:
        await message.answer(
            "Bu ID bilan mahsulot topilmadi. Qaytadan kiriting:",
            reply_markup=menu_only_kb(),
        )
        return

    if product["status"] != "active":
        await message.answer(
            "Bu mahsulot allaqachon chiqim qilingan yoki faol emas. Boshqa ID kiriting:",
            reply_markup=menu_only_kb(),
        )
        return

    if product["phone"] != data["client_phone"]:
        await message.answer(
            "Bu mahsulot ushbu mijozga tegishli emas. Boshqa ID kiriting:",
            reply_markup=menu_only_kb(),
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
async def exit_product_confirm(message: Message, state: FSMContext, bot: Bot):
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
                        sheets_ok = await asyncio.wait_for(
                            sheets_service.move_product_to_exited(
                                exit_data,
                                paid_amount=data.get("selected_paid", 0),
                                remaining_amount=data.get("selected_remaining", 0),
                            ),
                            timeout=20,
                        )
                    except asyncio.TimeoutError:
                        logger.warning("exit_product_confirm: Sheets move to exited timed out")
                        sheets_ok = False
                    except Exception:
                        logger.exception("Sheets move to exited crashed")
                        sheets_ok = False

                notification_ok = False
                try:
                    notify_data = {
                        "paid_amount": data.get("selected_paid", 0),
                        "remaining_amount": data.get("selected_remaining", 0),
                    }
                    notification_ok = await asyncio.wait_for(
                        notify_product_exited(
                            bot=bot,
                            telegram_id=exit_data["telegram_id"],
                            exit_data=exit_data,
                            payment_summary=notify_data,
                        ),
                        timeout=10,
                    )
                except asyncio.TimeoutError:
                    logger.warning("exit_product_confirm: Exit notification timed out")
                    notification_ok = False
                except Exception:
                    logger.exception("Exit notification failed")
                    notification_ok = False

                if sheets_ok:
                    msg = "Mahsulot SQLite va Google Sheets'da chiqim qilindi ✅"
                else:
                    msg = "Mahsulot SQLite bazada chiqim qilindi ✅, lekin Google Sheets'ga yozishda xatolik bo'ldi ⚠️"

                if notification_ok:
                    msg += "\nMijozga bildirishnoma yuborildi ✅"
                else:
                    msg += "\nMijozga bildirishnoma yuborilmadi ⚠️"

                await message.answer(msg, reply_markup=admin_panel_kb())
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
    await message.answer(
        "Avval 📋 Mijozlarni ko'rish orqali mijozni tanlang.",
        reply_markup=admin_main_kb(),
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
            reply_markup=menu_only_kb(),
        )
        return

    user = await get_user_by_phone(normalized)
    if user is None:
        await message.answer(
            "Bu telefon raqam bilan ro'yxatdan o'tgan mijoz topilmadi.",
            reply_markup=menu_only_kb(),
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
        reply_markup=menu_only_kb(),
    )


@router.message(AdminAddPayment.waiting_for_product_id, F.text)
async def payment_product_select(message: Message, state: FSMContext):
    text = message.text.strip()

    if text == "❌ Bekor qilish":
        await cancel_flow(message, state)
        return

    try:
        data = await state.get_data()
        logger.info(
            "Payment product id received: user_id=%s text=%s state=%s",
            message.from_user.id, text, data,
        )

        try:
            product_id = int(text)
        except ValueError:
            await message.answer(
                "Mahsulot ID raqam bo'lishi kerak.",
                reply_markup=menu_only_kb(),
            )
            return

        available_ids = [p["id"] for p in data.get("products", [])]
        if product_id not in available_ids:
            await message.answer(
                "Bu mahsulot ro'yxatda yo'q yoki Ombor sheetda mavjud emas.",
                reply_markup=menu_only_kb(),
            )
            return

        product = await get_product_by_id(product_id)
        if product is None:
            await message.answer(
                "Bu ID bilan mahsulot topilmadi. Qaytadan kiriting:",
                reply_markup=menu_only_kb(),
            )
            return

        if product["status"] != "active":
            await message.answer(
                "Bu mahsulot allaqachon chiqim qilingan yoki faol emas. Boshqa ID kiriting:",
                reply_markup=menu_only_kb(),
            )
            return

        summary = await get_product_payment_summary(product_id)
        paid = summary["paid_amount"]
        rem = summary["remaining_amount"]

        logger.info(
            "Payment product selected: product_id=%s client_id=%s remaining=%s",
            product_id, data.get("client_id"), rem,
        )

        if rem <= 0:
            await message.answer(
                "Bu mahsulot uchun to'lov to'liq qilingan. Boshqa mahsulot tanlang.",
                reply_markup=menu_only_kb(),
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
            f"✅ Tanlangan mahsulot:\n\n"
            f"<b>ID:</b> {product['id']}\n"
            f"<b>Mahsulot:</b> {product['product_name']}\n"
            f"<b>Umumiy summa:</b> {product['total_price']:,.0f} so'm\n"
            f"<b>To'langan:</b> {paid:,.0f} so'm\n"
            f"<b>Qolgan:</b> {rem:,.0f} so'm\n\n"
            f"To'lov summasini kiriting:",
            reply_markup=menu_only_kb(),
        )
    except Exception:
        logger.exception("Payment product id handler failed")
        await message.answer(
            "Xatolik yuz berdi. Qayta urinib ko'ring.",
            reply_markup=admin_panel_kb(),
        )
        await state.clear()


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
            reply_markup=menu_only_kb(),
        )
        return

    data = await state.get_data()
    remaining = data.get("selected_remaining", 0)

    valid, error_msg = validate_payment_amount(amount, remaining)
    if not valid:
        await message.answer(error_msg, reply_markup=menu_only_kb())
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
async def payment_confirm(message: Message, state: FSMContext, bot: Bot):
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
                        sheets_ok = await asyncio.wait_for(
                            sheets_service.append_payment_history(payment),
                            timeout=20,
                        )
                        if sheets_ok:
                            await asyncio.wait_for(
                                sheets_service.update_product_payment(
                                    data["selected_product_id"],
                                    summary["paid_amount"],
                                    summary["remaining_amount"],
                                ),
                                timeout=20,
                            )
                    except asyncio.TimeoutError:
                        logger.warning("payment_confirm: Sheets operation timed out")
                        sheets_ok = False
                    except Exception:
                        logger.exception("Sheets payment crashed")
                        sheets_ok = False

                notification_ok = False
                try:
                    product = await get_product_by_id(data["selected_product_id"])
                    notification_ok = await asyncio.wait_for(
                        notify_payment_received(
                            bot=bot,
                            telegram_id=data["telegram_id"],
                            payment=payment,
                            product=product,
                            payment_summary=summary,
                        ),
                        timeout=10,
                    )
                except asyncio.TimeoutError:
                    logger.warning("payment_confirm: Payment notification timed out")
                    notification_ok = False
                except Exception:
                    logger.exception("Payment notification failed")
                    notification_ok = False

                if sheets_ok:
                    msg = "To'lov bazaga va Google Sheets'ga saqlandi ✅"
                else:
                    msg = "To'lov SQLite bazaga saqlandi ✅, lekin Google Sheets'ga yozishda xatolik bo'ldi ⚠️"

                if notification_ok:
                    msg += "\nMijozga bildirishnoma yuborildi ✅"
                else:
                    msg += "\nMijozga bildirishnoma yuborilmadi ⚠️"

                await message.answer(msg, reply_markup=admin_panel_kb())
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
