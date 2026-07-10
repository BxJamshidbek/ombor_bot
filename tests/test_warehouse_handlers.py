import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from aiogram.types import CallbackQuery, Message

from app.handlers import admin, client
from app.keyboards import settings_kb, menu_only_kb, warehouse_location_confirm_kb


def _make_message():
    message = MagicMock()
    message.answer = AsyncMock()
    message.answer_location = AsyncMock()
    return message


def _make_state():
    state = MagicMock()
    state.set_state = AsyncMock()
    state.get_data = AsyncMock(return_value={})
    state.clear = AsyncMock()
    return state


def test_settings_warehouse_location_starts_fsm():
    callback = MagicMock(spec=CallbackQuery)
    callback.data = "settings:warehouse_location"
    callback.message = MagicMock()
    callback.message.edit_reply_markup = AsyncMock()
    callback.message.answer = AsyncMock()
    callback.answer = AsyncMock()

    state = _make_state()

    with patch.object(admin, "get_warehouse_location", AsyncMock(return_value=None)):
        with patch.object(admin, "save_warehouse_location", AsyncMock()):
            asyncio.run(admin.settings_warehouse_location_start(callback, state))

    state.set_state.assert_awaited_once()
    callback.message.edit_reply_markup.assert_awaited_once()
    callback.answer.assert_awaited_once()
    callback.message.answer.assert_awaited_once()


def test_warehouse_location_confirm_saves():
    callback = MagicMock(spec=CallbackQuery)
    callback.data = "warehouse_location:confirm"
    callback.message = MagicMock()
    callback.message.edit_text = AsyncMock()
    callback.message.answer = AsyncMock()
    callback.answer = AsyncMock()

    state = _make_state()
    state.get_data = AsyncMock(return_value={"latitude": 41.0, "longitude": 69.0})

    with patch.object(admin, "save_warehouse_location", AsyncMock()) as mock_save:
        asyncio.run(admin.warehouse_location_confirm(callback, state))

    mock_save.assert_awaited_once_with(41.0, 69.0)
    callback.message.edit_text.assert_awaited_once()
    callback.answer.assert_awaited_once()


def test_warehouse_location_cancel_does_not_save():
    callback = MagicMock(spec=CallbackQuery)
    callback.data = "warehouse_location:cancel"
    callback.message = MagicMock()
    callback.message.edit_text = AsyncMock()
    callback.message.answer = AsyncMock()
    callback.answer = AsyncMock()

    state = _make_state()

    with patch.object(admin, "save_warehouse_location", AsyncMock()) as mock_save:
        asyncio.run(admin.warehouse_location_cancel(callback, state))

    mock_save.assert_not_called()
    callback.message.edit_text.assert_awaited_once()
    callback.message.answer.assert_awaited_once()


def test_client_location_not_set():
    message = _make_message()
    with patch.object(client, "get_warehouse_location", return_value=None):
        with patch.object(client, "get_user_by_telegram_id", return_value={"role": "client"}):
            asyncio.run(client.warehouse_location(message))

    assert message.answer.await_count >= 1
    texts = [str(c.args[0]) for c in message.answer.call_args_list]
    assert any("admin tomonidan sozlanmagan" in t for t in texts)


def test_client_location_set_sends_map():
    message = _make_message()
    location = {
        "warehouse_latitude": 41.0,
        "warehouse_longitude": 69.0,
        "warehouse_location_name": "Asosiy ombor",
    }
    with patch.object(client, "get_warehouse_location", return_value=location):
        with patch.object(client, "get_user_by_telegram_id", return_value={"role": "client"}):
            asyncio.run(client.warehouse_location(message))

    assert message.answer_location.await_count == 1
    assert message.answer.await_count == 1
    call_args = message.answer.call_args_list
    second_text = str(call_args[0].args[0])
    assert "Asosiy ombor" in second_text
    second_kb = call_args[0].kwargs.get("reply_markup")
    assert second_kb is not None
