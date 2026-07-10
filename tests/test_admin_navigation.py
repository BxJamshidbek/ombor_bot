import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.handlers import admin


def _make_message():
    message = MagicMock()
    message.answer = AsyncMock()
    return message


def test_list_clients_sends_permanent_menu_then_clients_and_no_delete():
    message = _make_message()
    clients = [{"id": 1, "full_name": "Ali", "phone": "+998901234567"}]

    with patch.object(admin, "get_all_clients", AsyncMock(return_value=clients)):
        asyncio.run(admin.list_clients(message))

    assert message.answer.await_count == 2

    menu_call = None
    clients_call = None
    for call in message.answer.call_args_list:
        rm = call.kwargs.get("reply_markup")
        if rm is None:
            continue
        if getattr(rm, "keyboard", None):
            texts = [b.text for row in rm.keyboard for b in row]
            if "☰ Menu" in texts:
                menu_call = call
        if getattr(rm, "inline_keyboard", None):
            datas = [b.callback_data for row in rm.inline_keyboard for b in row]
            if "client:1" in datas:
                clients_call = call

    assert menu_call is not None, "Permanent menu-only keyboard message was not sent"
    assert clients_call is not None, "Client list inline message was not sent"

    # No message sent by list_clients may be deleted (no temporary/auto-delete).
    message.answer.return_value.delete.assert_not_called()


def test_list_clients_empty_sends_admin_menu_no_delete():
    message = _make_message()
    with patch.object(admin, "get_all_clients", AsyncMock(return_value=[])):
        asyncio.run(admin.list_clients(message))

    assert message.answer.await_count == 1
    message.answer.return_value.delete.assert_not_called()


def test_client_selected_uses_edit_text_and_answer_no_delete():
    callback = MagicMock()
    callback.data = "client:1"
    callback.message = MagicMock()
    callback.message.edit_text = AsyncMock()
    callback.message.delete = AsyncMock()
    callback.answer = AsyncMock()

    user = {
        "id": 1,
        "full_name": "Ali",
        "phone": "+998901234567",
        "telegram_id": 123,
    }

    with patch.object(admin, "get_user_by_id", AsyncMock(return_value=user)):
        asyncio.run(admin.client_selected(callback, MagicMock()))

    callback.message.edit_text.assert_awaited_once()
    callback.answer.assert_awaited_once()
    callback.message.delete.assert_not_called()


def test_admin_settings_sends_permanent_menu_message():
    message = _make_message()
    asyncio.run(admin.admin_settings(message))

    assert message.answer.await_count == 2
    menu_call = None
    for call in message.answer.call_args_list:
        rm = call.kwargs.get("reply_markup")
        if getattr(rm, "keyboard", None):
            texts = [b.text for row in rm.keyboard for b in row]
            if "☰ Menu" in texts:
                menu_call = call
    assert menu_call is not None, "Settings flow must send a permanent menu-only keyboard message"
    message.answer.return_value.delete.assert_not_called()
