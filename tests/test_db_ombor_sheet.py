import asyncio
import os
import pytest

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///test_ombor.sqlite3")
os.environ.setdefault("BOT_TOKEN", "test:token")
os.environ.setdefault("ADMIN_IDS", "123456")

from app.database import (
    init_db,
    create_user,
    create_product,
    mark_product_in_ombor_sheet,
    get_sheet_visible_active_products_by_client_id,
    get_active_products_for_client,
    get_admin_stats,
    get_product_by_id,
    exit_product,
    DATABASE_PATH,
)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


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


_counter = 90000

def _create_client():
    global _counter
    _counter += 1
    return _run(create_user(
        telegram_id=_counter,
        phone=f"+99890{str(_counter).zfill(7)}",
        full_name="Test Client",
        username="test_client",
        role="client",
    ))


def test_mark_product_in_ombor_sheet_true():
    client_id = _create_client()
    product_id = _run(create_product(
        client_id=client_id, telegram_id=99999, phone="+998901234567",
        client_name="Test Client", product_name="Test Product",
        kg_amount=10.0, price_per_kg=1000.0, box_count=2, total_price=10000.0,
    ))

    _run(mark_product_in_ombor_sheet(product_id, True))
    product = _run(get_product_by_id(product_id))
    assert product["is_in_ombor_sheet"] == 1


def test_mark_product_in_ombor_sheet_false():
    client_id = _create_client()
    product_id = _run(create_product(
        client_id=client_id, telegram_id=99999, phone="+998901234567",
        client_name="Test Client", product_name="Test Product",
        kg_amount=10.0, price_per_kg=1000.0, box_count=2, total_price=10000.0,
    ))

    _run(mark_product_in_ombor_sheet(product_id, True))
    _run(mark_product_in_ombor_sheet(product_id, False))
    product = _run(get_product_by_id(product_id))
    assert product["is_in_ombor_sheet"] == 0


def test_sheet_visible_filters_unsynced():
    client_id = _create_client()
    p1 = _run(create_product(
        client_id=client_id, telegram_id=99999, phone="+998901234567",
        client_name="Test Client", product_name="Synced",
        kg_amount=10.0, price_per_kg=1000.0, box_count=1, total_price=10000.0,
    ))
    p2 = _run(create_product(
        client_id=client_id, telegram_id=99999, phone="+998901234567",
        client_name="Test Client", product_name="Unsynced",
        kg_amount=5.0, price_per_kg=2000.0, box_count=1, total_price=10000.0,
    ))
    _run(mark_product_in_ombor_sheet(p1, True))

    visible = _run(get_sheet_visible_active_products_by_client_id(client_id))
    assert len(visible) == 1
    assert visible[0]["id"] == p1

    all_active = _run(get_active_products_for_client(client_id))
    assert len(all_active) == 2


def test_sheet_visible_excludes_exited():
    client_id = _create_client()
    p1 = _run(create_product(
        client_id=client_id, telegram_id=99999, phone="+998901234567",
        client_name="Test Client", product_name="Active",
        kg_amount=10.0, price_per_kg=1000.0, box_count=1, total_price=10000.0,
    ))
    p2 = _run(create_product(
        client_id=client_id, telegram_id=99999, phone="+998901234567",
        client_name="Test Client", product_name="Exited",
        kg_amount=5.0, price_per_kg=2000.0, box_count=1, total_price=10000.0,
    ))
    _run(mark_product_in_ombor_sheet(p1, True))
    _run(mark_product_in_ombor_sheet(p2, True))
    _run(exit_product(p2, admin_id=123456))

    visible = _run(get_sheet_visible_active_products_by_client_id(client_id))
    assert len(visible) == 1
    assert visible[0]["id"] == p1


def test_admin_stats_counts_only_in_sheet():
    client_id = _create_client()
    p1 = _run(create_product(
        client_id=client_id, telegram_id=99999, phone="+998901234567",
        client_name="Test Client", product_name="A",
        kg_amount=10.0, price_per_kg=1000.0, box_count=1, total_price=10000.0,
    ))
    _run(create_product(
        client_id=client_id, telegram_id=99999, phone="+998901234567",
        client_name="Test Client", product_name="B",
        kg_amount=5.0, price_per_kg=2000.0, box_count=1, total_price=10000.0,
    ))
    _run(mark_product_in_ombor_sheet(p1, True))

    stats = _run(get_admin_stats())
    assert stats["active_products"] == 1
    assert stats["total_products"] == 2
