import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramNetworkError,
    TelegramRetryAfter,
)

from app.services.notification_service import (
    safe_send_message,
    format_product_assigned_notification,
    format_payment_received_notification,
    format_product_exited_notification,
    notify_product_assigned,
    notify_payment_received,
    notify_product_exited,
)


def _run(coro):
    return asyncio.run(coro)


class TestFormatProductAssignedNotification:
    def test_contains_all_fields(self):
        product = {
            "product_name": "Olma",
            "kg_amount": 300,
            "box_count": 40,
            "price_per_kg": 2000,
            "total_price": 600000,
            "id": 123,
        }
        text = format_product_assigned_notification(product)
        assert "Sizga yangi mahsulot biriktirildi" in text
        assert "Olma" in text
        assert "300 kg" in text
        assert "40" in text
        assert "2 000 so'm" in text
        assert "600 000 so'm" in text
        assert "Product ID:</b> 123" in text
        assert "qabul qilindi ✅" in text

    def test_decimal_kg_preserved(self):
        product = {
            "product_name": "Olma",
            "kg_amount": 300.5,
            "box_count": 10,
            "price_per_kg": 1000,
            "total_price": 300500,
            "id": 1,
        }
        text = format_product_assigned_notification(product)
        assert "300.5 kg" in text

    def test_html_escaped(self):
        product = {
            "product_name": "<script>alert('x')</script>",
            "kg_amount": 10,
            "box_count": 1,
            "price_per_kg": 1000,
            "total_price": 10000,
            "id": 1,
        }
        text = format_product_assigned_notification(product)
        assert "<script>" not in text
        assert "&lt;script&gt;" in text


class TestFormatPaymentReceivedNotification:
    def test_amounts_displayed(self):
        payment = {"amount": 100000}
        product = {"product_name": "Olma", "id": 123}
        summary = {"paid_amount": 300000, "remaining_amount": 300000}
        text = format_payment_received_notification(payment, product, summary)
        assert "100 000 so'm" in text
        assert "300 000 so'm" in text
        assert "Product ID:</b> 123" in text

    def test_missing_product(self):
        payment = {"amount": 50000}
        text = format_payment_received_notification(payment, None, None)
        assert "Noma&#x27;lum" in text
        assert "50 000 so'm" in text

    def test_missing_summary(self):
        payment = {"amount": 100}
        product = {"product_name": "X", "id": 1}
        text = format_payment_received_notification(payment, product, None)
        assert "0 so'm" in text


class TestFormatProductExitedNotification:
    def test_full_exit(self):
        exit_data = {
            "product_name": "Olma",
            "product_id": 123,
            "kg_amount": 300,
            "box_count": 40,
            "total_price": 600000,
            "exited_at": "2026-07-10T12:00:00+05:00",
        }
        text = format_product_exited_notification(exit_data, {
            "paid_amount": 600000,
            "remaining_amount": 0,
        })
        assert "ombordan chiqarildi" in text
        assert "Product ID:</b> 123" in text
        assert "chiqim qilindi ✅" in text
        assert "Chiqim sanasi:</b> 2026-07-10" in text
        assert "qarzdorlik" not in text

    def test_debt_warning(self):
        exit_data = {
            "product_name": "Olma",
            "product_id": 123,
            "kg_amount": 300,
            "box_count": 40,
            "total_price": 600000,
            "exited_at": "2026-07-10T12:00:00Z",
        }
        text = format_product_exited_notification(exit_data, {
            "paid_amount": 500000,
            "remaining_amount": 100000,
        })
        assert "100 000 so'm qarzdorlik qolgan" in text

    def test_no_date_when_missing(self):
        exit_data = {
            "product_name": "Olma",
            "product_id": 123,
            "kg_amount": 300,
            "box_count": 40,
            "total_price": 600000,
            "exited_at": None,
        }
        text = format_product_exited_notification(exit_data)
        assert "Chiqim sanasi" not in text


class TestSafeSendMessage:
    def test_success(self):
        bot = MagicMock()
        bot.send_message = AsyncMock()
        result = _run(safe_send_message(bot, 123, "test"))
        assert result is True
        bot.send_message.assert_awaited_once_with(chat_id=123, text="test", reply_markup=None)

    def test_forbidden(self):
        bot = MagicMock()
        bot.send_message = AsyncMock(side_effect=TelegramForbiddenError(
            method=None, message="Forbidden: bot was blocked by the user"
        ))
        result = _run(safe_send_message(bot, 123, "test"))
        assert result is False

    def test_bad_request(self):
        bot = MagicMock()
        bot.send_message = AsyncMock(side_effect=TelegramBadRequest(
            method=None, message="Bad Request: chat not found"
        ))
        result = _run(safe_send_message(bot, 123, "test"))
        assert result is False

    def test_network_error(self):
        bot = MagicMock()
        bot.send_message = AsyncMock(side_effect=TelegramNetworkError(
            method=None, message="Network down"
        ))
        result = _run(safe_send_message(bot, 123, "test"))
        assert result is False

    def test_retry_after(self):
        bot = MagicMock()
        bot.send_message = AsyncMock(side_effect=TelegramRetryAfter(
            method=None, message="Too Many Requests", retry_after=30
        ))
        result = _run(safe_send_message(bot, 123, "test"))
        assert result is False

    def test_unexpected_exception(self):
        bot = MagicMock()
        bot.send_message = AsyncMock(side_effect=RuntimeError("boom"))
        result = _run(safe_send_message(bot, 123, "test"))
        assert result is False

    def test_with_reply_markup(self):
        bot = MagicMock()
        bot.send_message = AsyncMock()
        kb = MagicMock()
        result = _run(safe_send_message(bot, 123, "test", reply_markup=kb))
        assert result is True
        bot.send_message.assert_awaited_once_with(chat_id=123, text="test", reply_markup=kb)


class TestNotifyProductAssigned:
    def test_calls_safe_send(self):
        bot = MagicMock()
        bot.send_message = AsyncMock()
        product = {
            "product_name": "Olma",
            "kg_amount": 300,
            "box_count": 40,
            "price_per_kg": 2000,
            "total_price": 600000,
            "id": 123,
            "telegram_id": 999,
        }
        result = _run(notify_product_assigned(bot, 999, product))
        assert result is True
        bot.send_message.assert_awaited_once()
        call = bot.send_message.call_args
        assert call.kwargs["chat_id"] == 999
        assert "Olma" in call.kwargs["text"]
        assert "300 kg" in call.kwargs["text"]

    def test_timeout_returns_false(self):
        async def long_send(*args, **kwargs):
            await asyncio.sleep(60)

        bot = MagicMock()
        bot.send_message = AsyncMock(side_effect=long_send)
        result = _run(safe_send_message(bot, 123, "test"))
        assert result is False
        bot.send_message.assert_awaited_once()


class TestNotifyPaymentReceived:
    def test_sends_notification(self):
        bot = MagicMock()
        bot.send_message = AsyncMock()
        payment = {"amount": 100000}
        product = {"product_name": "Olma", "id": 123}
        summary = {"paid_amount": 300000, "remaining_amount": 300000}
        result = _run(notify_payment_received(bot, 999, payment, product, summary))
        assert result is True
        bot.send_message.assert_awaited_once()
        text = bot.send_message.call_args.kwargs["text"]
        assert "100 000 so'm" in text
        assert "300 000 so'm" in text


class TestNotifyProductExited:
    def test_sends_notification_with_debt(self):
        bot = MagicMock()
        bot.send_message = AsyncMock()
        exit_data = {
            "product_name": "Olma",
            "product_id": 123,
            "kg_amount": 300,
            "box_count": 40,
            "total_price": 600000,
            "exited_at": "2026-07-10T12:00:00Z",
        }
        result = _run(notify_product_exited(bot, 999, exit_data, {
            "paid_amount": 500000,
            "remaining_amount": 100000,
        }))
        assert result is True
        bot.send_message.assert_awaited_once()
        text = bot.send_message.call_args.kwargs["text"]
        assert "100 000 so'm qarzdorlik" in text
        assert "chiqim qilindi ✅" in text
