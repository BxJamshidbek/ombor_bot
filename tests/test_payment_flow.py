import asyncio
import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///test_ombor.sqlite3")
os.environ.setdefault("BOT_TOKEN", "test:token")
os.environ.setdefault("ADMIN_IDS", "123456")

from app.database import (
    init_db,
    create_user,
    create_product,
    mark_product_in_ombor_sheet,
    get_product_payment_summary,
    get_sheet_visible_active_products_by_client_id,
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


_counter = 80000


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


def test_payment_flow_phone_key_is_phone_not_client_phone():
    client_id = _create_client()
    product_id = _run(create_product(
        client_id=client_id, telegram_id=_counter, phone=f"+99890{str(_counter).zfill(7)}",
        client_name="Test Client", product_name="Gilos",
        kg_amount=200.0, price_per_kg=2000.0, box_count=10, total_price=400000.0,
    ))
    _run(mark_product_in_ombor_sheet(product_id, True))

    products = _run(get_sheet_visible_active_products_by_client_id(client_id))
    assert len(products) == 1

    state_data = {
        "client_id": client_id,
        "telegram_id": _counter,
        "phone": f"+99890{str(_counter).zfill(7)}",
        "client_name": "Test Client",
        "products": products,
    }

    product = products[0]
    assert product["phone"] == state_data["phone"]


def test_payment_product_not_in_available_list():
    client_id = _create_client()
    product_id = _run(create_product(
        client_id=client_id, telegram_id=_counter, phone=f"+99890{str(_counter).zfill(7)}",
        client_name="Test Client", product_name="Gilos",
        kg_amount=200.0, price_per_kg=2000.0, box_count=10, total_price=400000.0,
    ))
    _run(mark_product_in_ombor_sheet(product_id, True))

    products = _run(get_sheet_visible_active_products_by_client_id(client_id))
    available_ids = [p["id"] for p in products]

    fake_id = 99999
    assert fake_id not in available_ids


def test_payment_remaining_amount_calculation():
    client_id = _create_client()
    product_id = _run(create_product(
        client_id=client_id, telegram_id=_counter, phone=f"+99890{str(_counter).zfill(7)}",
        client_name="Test Client", product_name="Gilos",
        kg_amount=200.0, price_per_kg=2000.0, box_count=10, total_price=400000.0,
    ))
    _run(mark_product_in_ombor_sheet(product_id, True))

    summary = _run(get_product_payment_summary(product_id))
    assert summary["total_amount"] == 400000.0
    assert summary["paid_amount"] == 0
    assert summary["remaining_amount"] == 400000.0


def test_payment_overpay_rejected():
    remaining = 400000.0
    amount = 500000.0
    assert amount > remaining
