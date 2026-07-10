import os
import asyncio

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///test_warehouse.sqlite3")
os.environ.setdefault("BOT_TOKEN", "test:token")
os.environ.setdefault("ADMIN_IDS", "123456")

from app.database import (
    init_db,
    get_warehouse_location,
    save_warehouse_location,
    set_setting,
    get_setting,
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
        await conn.execute("DELETE FROM settings")
        await conn.commit()
        await conn.close()

    _run(_clean())


def teardown_module():
    import time

    time.sleep(0.1)
    if os.path.exists(DATABASE_PATH):
        os.remove(DATABASE_PATH)


def test_get_warehouse_location_returns_none_when_empty():
    assert _run(get_warehouse_location()) is None


def test_save_and_get_warehouse_location():
    _run(save_warehouse_location(41.0, 69.0, "Asosiy ombor"))
    result = _run(get_warehouse_location())
    assert result is not None
    assert result["warehouse_latitude"] == 41.0
    assert result["warehouse_longitude"] == 69.0
    assert result.get("warehouse_location_name") == "Asosiy ombor"


def test_save_without_name():
    _run(save_warehouse_location(-33.8688, 151.2093))
    result = _run(get_warehouse_location())
    assert result is not None
    assert result["warehouse_latitude"] == -33.8688
    assert result["warehouse_longitude"] == 151.2093
    assert result.get("warehouse_location_name") is None


def test_save_overwrites_existing():
    _run(save_warehouse_location(1.0, 2.0, "Eski"))
    _run(save_warehouse_location(3.0, 4.0, "Yangi"))
    result = _run(get_warehouse_location())
    assert result["warehouse_latitude"] == 3.0
    assert result["warehouse_longitude"] == 4.0
    assert result.get("warehouse_location_name") == "Yangi"


def test_get_setting_and_set_setting():
    _run(set_setting("test_key", "test_value"))
    assert _run(get_setting("test_key")) == "test_value"
    assert _run(get_setting("missing_key")) is None


def test_incomplete_coordinates_returns_none():
    _run(set_setting("warehouse_latitude", "41.0"))
    assert _run(get_warehouse_location()) is None
