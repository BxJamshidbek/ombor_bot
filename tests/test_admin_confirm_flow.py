import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.handlers import admin
from app.keyboards import admin_panel_kb


def _run(coro):
    return asyncio.run(coro)


def _make_message(text="Ha ✅"):
    message = MagicMock()
    message.text = text
    message.chat = MagicMock()
    message.chat.id = 123
    message.answer = AsyncMock()
    return message


def _make_state():
    state = MagicMock()
    state.get_data = AsyncMock(return_value={
        "client_id": 1,
        "telegram_id": 999,
        "phone": "+998901234567",
        "client_name": "Ali",
        "product_name": "Olma",
        "kg_amount": 10.0,
        "price_per_kg": 2000.0,
        "box_count": 2,
        "total_price": 20000.0,
    })
    state.update_data = AsyncMock()
    state.clear = AsyncMock()
    return state


def test_add_product_confirm_sheets_timeout_continues():
    message = _make_message()
    state = _make_state()
    bot = MagicMock()

    with patch.object(admin, "create_product", AsyncMock(return_value=42)):
        with patch.object(admin.sheets_service, "is_configured", return_value=True):
            with patch.object(admin.sheets_service, "append_product_row", AsyncMock(side_effect=asyncio.TimeoutError())):
                with patch.object(admin, "mark_product_in_ombor_sheet", AsyncMock()) as mock_mark:
                    with patch.object(admin, "notify_product_assigned", AsyncMock(return_value=True)):
                        _run(admin.add_product_confirm(message, state, bot))

    state.update_data.assert_awaited_with(created_product_id=42)
    state.clear.assert_awaited_once()
    message.answer.assert_awaited()
    assert any("Google Sheets'ga yozishda xatolik" in str(call.args[0]) for call in message.answer.call_args_list)
    mock_mark.assert_not_called()


def test_add_product_confirm_notification_timeout_warns():
    message = _make_message()
    state = _make_state()
    bot = MagicMock()

    with patch.object(admin, "create_product", AsyncMock(return_value=43)):
        with patch.object(admin.sheets_service, "is_configured", return_value=False):
            with patch.object(admin, "notify_product_assigned", AsyncMock(side_effect=asyncio.TimeoutError())):
                _run(admin.add_product_confirm(message, state, bot))

    state.update_data.assert_awaited_with(created_product_id=43)
    state.clear.assert_awaited_once()
    message.answer.assert_awaited()
    assert any("Mijozga bildirishnoma yuborilmadi" in str(call.args[0]) for call in message.answer.call_args_list)


def test_add_product_confirm_sheets_exception_caught():
    message = _make_message()
    state = _make_state()
    bot = MagicMock()

    with patch.object(admin, "create_product", AsyncMock(return_value=44)):
        with patch.object(admin.sheets_service, "is_configured", return_value=True):
            with patch.object(admin.sheets_service, "append_product_row", AsyncMock(side_effect=RuntimeError("Sheets down"))):
                with patch.object(admin, "notify_product_assigned", AsyncMock(return_value=True)):
                    _run(admin.add_product_confirm(message, state, bot))

    state.clear.assert_awaited_once()
    message.answer.assert_awaited()
    assert any("xatolik" in str(call.args[0]).lower() for call in message.answer.call_args_list)


def test_add_product_confirm_notification_exception_caught():
    message = _make_message()
    state = _make_state()
    bot = MagicMock()

    with patch.object(admin, "create_product", AsyncMock(return_value=45)):
        with patch.object(admin.sheets_service, "is_configured", return_value=False):
            with patch.object(admin, "notify_product_assigned", AsyncMock(side_effect=RuntimeError("Notify down"))):
                _run(admin.add_product_confirm(message, state, bot))

    state.clear.assert_awaited_once()
    message.answer.assert_awaited()
    assert any("Mijozga bildirishnoma yuborilmadi" in str(call.args[0]) for call in message.answer.call_args_list)


def test_add_product_confirm_create_product_exception():
    message = _make_message()
    state = _make_state()
    bot = MagicMock()

    with patch.object(admin, "create_product", AsyncMock(side_effect=RuntimeError("DB down"))):
        _run(admin.add_product_confirm(message, state, bot))

    state.clear.assert_awaited_once()
    message.answer.assert_awaited()
    assert any("xatolik bo'ldi" in str(call.args[0]).lower() for call in message.answer.call_args_list)


def test_add_product_confirm_duplicate_blocked():
    message = _make_message()
    state = _make_state()
    state.get_data = AsyncMock(return_value={
        "client_id": 1,
        "telegram_id": 999,
        "phone": "+998901234567",
        "client_name": "Ali",
        "product_name": "Olma",
        "kg_amount": 10.0,
        "price_per_kg": 2000.0,
        "box_count": 2,
        "total_price": 20000.0,
        "created_product_id": 42,
    })
    bot = MagicMock()

    with patch.object(admin, "create_product", AsyncMock(return_value=99)) as mock_create:
        _run(admin.add_product_confirm(message, state, bot))

    mock_create.assert_not_called()
    state.clear.assert_awaited_once()
    message.answer.assert_awaited_once()
    assert "allaqachon" in str(message.answer.call_args[0][0]).lower()


def test_add_product_confirm_no_duplicate_on_first_call():
    message = _make_message()
    state = _make_state()
    state.get_data = AsyncMock(return_value={
        "client_id": 1,
        "telegram_id": 999,
        "phone": "+998901234567",
        "client_name": "Ali",
        "product_name": "Olma",
        "kg_amount": 10.0,
        "price_per_kg": 2000.0,
        "box_count": 2,
        "total_price": 20000.0,
    })
    bot = MagicMock()

    with patch.object(admin, "create_product", AsyncMock(return_value=100)):
        with patch.object(admin.sheets_service, "is_configured", return_value=False):
            with patch.object(admin, "notify_product_assigned", AsyncMock(return_value=True)):
                _run(admin.add_product_confirm(message, state, bot))

    state.update_data.assert_awaited_with(created_product_id=100)
    state.clear.assert_awaited_once()


def test_add_product_confirm_yok_rejected():
    message = _make_message(text="Yo'q ❌")
    state = _make_state()
    bot = MagicMock()

    with patch.object(admin, "create_product", AsyncMock()) as mock_create:
        _run(admin.add_product_confirm(message, state, bot))

    mock_create.assert_not_called()
    state.clear.assert_awaited_once()
    message.answer.assert_awaited_once()
    assert "bekor qilindi" in str(message.answer.call_args[0][0]).lower()


def test_add_product_confirm_bekor_qilish():
    message = _make_message(text="❌ Bekor qilish")
    state = _make_state()
    bot = MagicMock()

    with patch.object(admin, "create_product", AsyncMock()) as mock_create:
        _run(admin.add_product_confirm(message, state, bot))

    mock_create.assert_not_called()


def test_add_product_confirm_state_clear_always_called():
    message = _make_message()
    state = _make_state()
    bot = MagicMock()

    with patch.object(admin, "create_product", AsyncMock(side_effect=RuntimeError("DB crash"))):
        _run(admin.add_product_confirm(message, state, bot))

    state.clear.assert_awaited_once()


def test_global_error_handler_logs_traceback():
    from aiogram.types import ErrorEvent

    import app.main

    try:
        raise ValueError("test error")
    except ValueError:
        import sys
        exc_info = sys.exc_info()
        event = MagicMock(spec=ErrorEvent)
        event.exception = exc_info[1]
        event.exception.__traceback__ = exc_info[2]
        event.update = MagicMock()
        event.update.message = None
        event.update.callback_query = None

        with patch("app.main.logger") as mock_logger:
            _run(app.main.global_error_handler(event))

        mock_logger.error.assert_called_once()
        args, kwargs = mock_logger.error.call_args
        assert "ValueError" in str(args)


def test_global_error_handler_callback_query():
    from aiogram.types import ErrorEvent

    import app.main

    try:
        raise RuntimeError("callback error")
    except RuntimeError:
        import sys
        exc_info = sys.exc_info()
        event = MagicMock(spec=ErrorEvent)
        event.exception = exc_info[1]
        event.exception.__traceback__ = exc_info[2]
        event.update = MagicMock()
        event.update.message = MagicMock()
        event.update.message.answer = AsyncMock()
        event.update.callback_query = MagicMock()
        event.update.callback_query.message = MagicMock()
        event.update.callback_query.message.answer = AsyncMock()

        with patch("app.main.logger"):
            _run(app.main.global_error_handler(event))

        event.update.message.answer.assert_awaited_once()
