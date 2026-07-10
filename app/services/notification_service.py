import asyncio
import html
import logging
from typing import Any

from aiogram import Bot
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramNetworkError,
    TelegramRetryAfter,
)

logger = logging.getLogger(__name__)


async def safe_send_message(
    bot: Bot,
    chat_id: int,
    text: str,
    reply_markup: Any = None,
) -> bool:
    try:
        await asyncio.wait_for(
            bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup,
            ),
            timeout=10,
        )
        return True
    except asyncio.TimeoutError:
        logger.warning(
            "Notification send timed out: chat_id=%s", chat_id
        )
        return False
    except TelegramForbiddenError:
        logger.warning(
            "Notification blocked by user: chat_id=%s", chat_id
        )
        return False
    except TelegramBadRequest as e:
        logger.warning(
            "Notification bad request: chat_id=%s error=%s", chat_id, e
        )
        return False
    except TelegramRetryAfter as e:
        logger.warning(
            "Notification rate limited: chat_id=%s retry_after=%s",
            chat_id,
            e.retry_after,
        )
        return False
    except TelegramNetworkError as e:
        logger.warning(
            "Notification network error: chat_id=%s error=%s", chat_id, e
        )
        return False
    except Exception as e:
        logger.exception(
            "Notification unexpected error: chat_id=%s", chat_id
        )
        return False


def _fmt_num(value: float) -> str:
    if value == int(value):
        return f"{int(value):,}".replace(",", " ")
    return f"{value:,.1f}".replace(",", " ")


def _escape(value: Any) -> str:
    return html.escape(str(value) if value is not None else "")


def format_product_assigned_notification(product: dict) -> str:
    name = _escape(product.get("product_name") or "Noma'lum")
    kg = _fmt_num(float(product.get("kg_amount", 0)))
    box = product.get("box_count", 0)
    price = _fmt_num(float(product.get("price_per_kg", 0)))
    total = _fmt_num(float(product.get("total_price", 0)))
    pid = product.get("id", "?")

    return (
        "📦 <b>Sizga yangi mahsulot biriktirildi</b>\n\n"
        f"<b>Mahsulot:</b> {name}\n"
        f"<b>Miqdor:</b> {kg} kg\n"
        f"<b>Qutilar soni:</b> {box}\n"
        f"<b>1 kg narxi:</b> {price} so'm\n"
        f"<b>Umumiy summa:</b> {total} so'm\n"
        f"<b>Product ID:</b> {pid}\n\n"
        "Mahsulotingiz omborga qabul qilindi ✅"
    )


def format_payment_received_notification(
    payment: dict,
    product: dict | None,
    payment_summary: dict | None,
) -> str:
    name = _escape((product or {}).get("product_name") or "Noma'lum")
    pid = (product or {}).get("id", "?")
    amount = _fmt_num(float(payment.get("amount", 0)))
    paid = _fmt_num(float((payment_summary or {}).get("paid_amount", 0)))
    remaining = _fmt_num(
        float((payment_summary or {}).get("remaining_amount", 0))
    )

    return (
        "💳 <b>To'lov qabul qilindi</b>\n\n"
        f"<b>Mahsulot:</b> {name}\n"
        f"<b>Product ID:</b> {pid}\n"
        f"<b>To'lov summasi:</b> {amount} so'm\n"
        f"<b>Jami to'langan:</b> {paid} so'm\n"
        f"<b>Qolgan summa:</b> {remaining} so'm\n\n"
        "To'lovingiz tizimga kiritildi ✅"
    )


def format_product_exited_notification(
    exit_data: dict,
    payment_summary: dict | None = None,
) -> str:
    name = _escape(exit_data.get("product_name") or "Noma'lum")
    pid = exit_data.get("product_id", "?")
    kg = _fmt_num(float(exit_data.get("kg_amount", 0)))
    box = exit_data.get("box_count", 0)
    total = _fmt_num(float(exit_data.get("total_price", 0)))
    paid = _fmt_num(
        float((payment_summary or {}).get("paid_amount", 0))
    )
    remaining = _fmt_num(
        float((payment_summary or {}).get("remaining_amount", 0))
    )
    exited_at = exit_data.get("exited_at") or ""
    date_str = ""
    if exited_at:
        try:
            date_str = exited_at[:10]
        except Exception:
            date_str = str(exited_at)

    lines = (
        "📤 <b>Mahsulotingiz ombordan chiqarildi</b>\n\n"
        f"<b>Mahsulot:</b> {name}\n"
        f"<b>Product ID:</b> {pid}\n"
        f"<b>Miqdor:</b> {kg} kg\n"
        f"<b>Qutilar soni:</b> {box}\n"
        f"<b>Umumiy summa:</b> {total} so'm\n"
        f"<b>To'langan:</b> {paid} so'm\n"
        f"<b>Qolgan:</b> {remaining} so'm\n"
    )
    if date_str:
        lines += f"<b>Chiqim sanasi:</b> {date_str}\n"

    lines += "\nMahsulot chiqim qilindi ✅"

    raw_remaining = float((payment_summary or {}).get("remaining_amount", 0))
    if raw_remaining > 0:
        lines += (
            f"\n\n⚠️ Ushbu mahsulot bo'yicha {_fmt_num(raw_remaining)} so'm qarzdorlik qolgan."
        )

    return lines


async def notify_product_assigned(
    bot: Bot,
    telegram_id: int,
    product: dict,
) -> bool:
    text = format_product_assigned_notification(product)
    return await safe_send_message(bot, telegram_id, text)


async def notify_payment_received(
    bot: Bot,
    telegram_id: int,
    payment: dict,
    product: dict | None,
    payment_summary: dict | None,
) -> bool:
    text = format_payment_received_notification(payment, product, payment_summary)
    return await safe_send_message(bot, telegram_id, text)


async def notify_product_exited(
    bot: Bot,
    telegram_id: int,
    exit_data: dict,
    payment_summary: dict | None = None,
) -> bool:
    text = format_product_exited_notification(exit_data, payment_summary)
    return await safe_send_message(bot, telegram_id, text)
