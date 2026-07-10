import asyncio
import os
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///test_registration.sqlite3")
os.environ.setdefault("BOT_TOKEN", "test:token")
os.environ.setdefault("ADMIN_IDS", "123456")

from app.config import config as app_config
from app.database import (
    init_db,
    create_user,
    get_user_by_telegram_id,
    DATABASE_PATH,
)


def _run(coro):
    return asyncio.run(coro)


def setup_module():
    _run(init_db())


def setup_function():
    import aiosqlite

    async def _clean():
        conn = await aiosqlite.connect(DATABASE_PATH)
        await conn.execute("DELETE FROM products")
        await conn.execute("DELETE FROM users")
        await conn.execute("DELETE FROM payments")
        await conn.execute("DELETE FROM exits")
        await conn.commit()
        await conn.close()

    _run(_clean())


def teardown_module():
    import time

    time.sleep(0.1)
    if os.path.exists(DATABASE_PATH):
        os.remove(DATABASE_PATH)


def _make_message(telegram_id=99999, text="/start", username="test_user", chat_id=99999):
    message = MagicMock()
    message.text = text
    message.chat = MagicMock()
    message.chat.id = chat_id
    message.chat.type = "private"
    message.from_user = MagicMock()
    message.from_user.id = telegram_id
    message.from_user.username = username
    message.from_user.full_name = "Test User"
    message.answer = AsyncMock()
    message.contact = None
    return message


def _make_contact_message(telegram_id=99999, phone="+998901234567", contact_user_id=None, username="test_user"):
    message = MagicMock()
    message.text = None
    message.chat = MagicMock()
    message.chat.id = telegram_id
    message.chat.type = "private"
    message.from_user = MagicMock()
    message.from_user.id = telegram_id
    message.from_user.username = username
    message.answer = AsyncMock()
    message.contact = MagicMock()
    message.contact.user_id = contact_user_id if contact_user_id is not None else telegram_id
    message.contact.phone_number = phone
    return message


def _make_state():
    state = MagicMock()
    state.get_data = AsyncMock(return_value={"phone": "+998901234567"})
    state.update_data = AsyncMock()
    state.set_state = AsyncMock()
    state.clear = AsyncMock()
    return state


class TestCmdStart:
    def test_new_user_gets_phone_keyboard(self):
        from app.handlers.start import cmd_start

        message = _make_message(telegram_id=99999)
        state = _make_state()

        with patch.object(app_config, "admin_ids", []):
            _run(cmd_start(message, state))

        state.set_state.assert_awaited_once()
        message.answer.assert_awaited_once()
        assert "telefon raqamingizni ulashing" in str(message.answer.call_args[0][0]).lower()

    def test_existing_user_gets_menu(self):
        from app.handlers.start import cmd_start

        user_id = _run(create_user(
            telegram_id=77777,
            phone="+998907777777",
            full_name="Old User",
            username="old_user",
            role="client",
        ))

        message = _make_message(telegram_id=77777)
        state = _make_state()

        with patch.object(app_config, "admin_ids", []):
            _run(cmd_start(message, state))

        assert message.answer.await_count >= 1
        text = str(message.answer.call_args[0][0])
        assert "ro'yxatdan o'tgansiz" in text.lower()

    def test_admin_gets_admin_menu(self):
        from app.handlers.start import cmd_start

        message = _make_message(telegram_id=123456)
        state = _make_state()

        with patch.object(app_config, "admin_ids", [123456]):
            _run(cmd_start(message, state))

        state.clear.assert_awaited_once()
        message.answer.assert_awaited_once()
        assert "admin" in str(message.answer.call_args[0][0]).lower()

    def test_new_user_after_previous_incomplete_state(self):
        from app.handlers.start import cmd_start

        state = MagicMock()
        state.update_data = AsyncMock()
        state.set_state = AsyncMock()
        state.clear = AsyncMock()

        message = _make_message(telegram_id=99998)

        with patch.object(app_config, "admin_ids", []):
            _run(cmd_start(message, state))

        state.set_state.assert_awaited_once()
        message.answer.assert_awaited_once()


class TestPhoneContactReceived:
    def test_valid_contact_sets_name_state(self):
        from app.handlers.start import phone_contact_received

        message = _make_contact_message(telegram_id=10001)
        state = _make_state()

        _run(phone_contact_received(message, state))

        state.update_data.assert_awaited_once()
        state.set_state.assert_awaited_once()
        message.answer.assert_awaited_once()
        assert "Ismingizni kiriting" in str(message.answer.call_args[0][0])

    def test_wrong_contact_user_id_rejected(self):
        from app.handlers.start import phone_contact_received

        message = _make_contact_message(telegram_id=10002, contact_user_id=88888)
        state = _make_state()

        _run(phone_contact_received(message, state))

        message.answer.assert_awaited_once()
        assert "faqat o'zingizning" in str(message.answer.call_args[0][0]).lower()
        state.update_data.assert_not_called()

    def test_invalid_phone_format_shows_error(self):
        from app.handlers.start import phone_contact_received

        message = _make_contact_message(telegram_id=10003, phone="123")
        state = _make_state()

        _run(phone_contact_received(message, state))

        message.answer.assert_awaited_once()
        assert "noto'g'ri" in str(message.answer.call_args[0][0]).lower()
        state.update_data.assert_not_called()

    def test_contact_user_id_none_does_not_crash(self):
        from app.handlers.start import phone_contact_received

        message = _make_contact_message(telegram_id=10004, contact_user_id=None)
        state = _make_state()

        _run(phone_contact_received(message, state))

        state.update_data.assert_awaited_once()
        message.answer.assert_awaited_once()

    def test_contact_is_none_does_not_crash(self):
        from app.handlers.start import phone_contact_received

        message = _make_message(telegram_id=10005, text="not a contact")
        state = _make_state()

        _run(phone_contact_received(message, state))

    def test_exception_fallback_message_sent(self):
        from app.handlers.start import phone_contact_received

        message = _make_contact_message(telegram_id=10006, phone="+998901234567")
        state = MagicMock()
        state.update_data = AsyncMock(side_effect=Exception("DB error"))
        state.set_state = AsyncMock()
        state.clear = AsyncMock()

        _run(phone_contact_received(message, state))

        state.clear.assert_awaited_once()
        message.answer.assert_awaited_once()
        assert "xatolik" in str(message.answer.call_args[0][0]).lower()


class TestNameReceived:
    def test_valid_name_creates_user(self):
        from app.handlers.start import name_received

        message = _make_message(telegram_id=20001, text="Ali Valiyev")
        state = _make_state()

        _run(name_received(message, state))

        state.clear.assert_awaited_once()
        message.answer.assert_awaited_once()
        assert "yakunlandi" in str(message.answer.call_args[0][0]).lower()

        user = _run(get_user_by_telegram_id(20001))
        assert user is not None
        assert user["full_name"] == "Ali Valiyev"
        assert user["phone"] == "+998901234567"
        assert user["role"] == "client"

    def test_duplicate_telegram_id_handled_gracefully(self):
        from app.handlers.start import name_received

        _run(create_user(
            telegram_id=30001,
            phone="+998903000001",
            full_name="First User",
            username="first",
            role="client",
        ))

        message = _make_message(telegram_id=30001, text="Second User")
        state = MagicMock()
        state.get_data = AsyncMock(return_value={"phone": "+998901234567"})
        state.clear = AsyncMock()
        state.update_data = AsyncMock()

        with patch.object(app_config, "admin_ids", []):
            _run(name_received(message, state))

        state.clear.assert_awaited_once()
        message.answer.assert_awaited_once()

        async def _check():
            u = await get_user_by_telegram_id(30001)
            return u
        user = _run(_check())
        assert user is not None
        assert user["full_name"] == "First User"

    def test_invalid_name_returns_error(self):
        from app.handlers.start import name_received

        message = _make_message(telegram_id=20002, text="A")
        state = _make_state()

        _run(name_received(message, state))

        state.clear.assert_not_called()
        message.answer.assert_awaited_once()
        assert "noto'g'ri" in str(message.answer.call_args[0][0]).lower()

    def test_phone_missing_from_state(self):
        from app.handlers.start import name_received

        message = _make_message(telegram_id=20003, text="Ali Valiyev")
        state = MagicMock()
        state.get_data = AsyncMock(return_value={})
        state.update_data = AsyncMock()
        state.clear = AsyncMock()
        state.set_state = AsyncMock()

        _run(name_received(message, state))

        state.clear.assert_awaited_once()
        message.answer.assert_awaited_once()

    def test_create_user_exception_fallback(self):
        from app.handlers.start import name_received

        message = _make_message(telegram_id=20004, text="Ali Valiyev")
        state = MagicMock()
        state.get_data = AsyncMock(return_value={"phone": "+998901234567"})
        state.clear = AsyncMock()
        state.update_data = AsyncMock()
        state.set_state = AsyncMock()

        with patch("app.handlers.start.create_user", AsyncMock(side_effect=Exception("DB error"))):
            _run(name_received(message, state))

        state.clear.assert_awaited_once()
        message.answer.assert_awaited_once()
        assert "xatolik" in str(message.answer.call_args[0][0]).lower()

    def test_admin_name_creates_admin_role(self):
        from app.handlers.start import name_received

        message = _make_message(telegram_id=123456, text="Admin User")
        state = _make_state()

        with patch.object(app_config, "admin_ids", [123456]):
            _run(name_received(message, state))

        state.clear.assert_awaited_once()
        user = _run(get_user_by_telegram_id(123456))
        assert user is not None
        assert user["role"] == "admin"


class TestNameNonText:
    def test_non_text_prompts_name_input(self):
        from app.handlers.start import name_non_text

        message = _make_message(telegram_id=30001, text=None)
        _run(name_non_text(message))

        message.answer.assert_awaited_once()
        assert "ismingizni" in str(message.answer.call_args[0][0]).lower()


class TestPhoneContactMissing:
    def test_phone_missing_reminds_button(self):
        from app.handlers.start import phone_contact_missing

        message = _make_message(telegram_id=40001, text="hello")
        _run(phone_contact_missing(message))

        message.answer.assert_awaited_once()
        assert "telefon raqamingizni ulashing" in str(message.answer.call_args[0][0]).lower()
