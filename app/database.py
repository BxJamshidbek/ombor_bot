import aiosqlite
from datetime import datetime, timezone

from app.config import config

DATABASE_PATH = config.database_url.replace("sqlite+aiosqlite:///", "")


async def get_connection() -> aiosqlite.Connection:
    conn = await aiosqlite.connect(DATABASE_PATH)
    conn.row_factory = aiosqlite.Row
    return conn


async def init_db() -> None:
    conn = await get_connection()
    try:
        await conn.execute("PRAGMA journal_mode=WAL;")
        await conn.execute("PRAGMA foreign_keys=ON;")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL UNIQUE,
                phone TEXT NOT NULL,
                full_name TEXT,
                username TEXT,
                role TEXT NOT NULL DEFAULT 'client',
                created_at TEXT NOT NULL,
                updated_at TEXT
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS exits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                client_id INTEGER NOT NULL,
                telegram_id INTEGER NOT NULL,
                phone TEXT NOT NULL,
                client_name TEXT,
                product_name TEXT NOT NULL,
                kg_amount REAL NOT NULL,
                price_per_kg REAL NOT NULL,
                storage_days INTEGER NOT NULL,
                total_price REAL NOT NULL,
                box_count INTEGER NOT NULL DEFAULT 0,
                exited_at TEXT NOT NULL,
                created_by_admin_id INTEGER NOT NULL DEFAULT 0,
                note TEXT,
                FOREIGN KEY (product_id) REFERENCES products(id),
                FOREIGN KEY (client_id) REFERENCES users(id)
            )
        """)

        cursor = await conn.execute("PRAGMA table_info(exits)")
        existing_cols = {row["name"] for row in await cursor.fetchall()}
        if "created_by_admin_id" not in existing_cols:
            await conn.execute(
                "ALTER TABLE exits ADD COLUMN created_by_admin_id INTEGER NOT NULL DEFAULT 0"
            )
        if "note" not in existing_cols:
            await conn.execute(
                "ALTER TABLE exits ADD COLUMN note TEXT"
            )
        if "box_count" not in existing_cols:
            await conn.execute(
                "ALTER TABLE exits ADD COLUMN box_count INTEGER NOT NULL DEFAULT 0"
            )

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                telegram_id INTEGER NOT NULL,
                phone TEXT NOT NULL,
                client_name TEXT,
                product_name TEXT NOT NULL,
                kg_amount REAL NOT NULL,
                price_per_kg REAL NOT NULL,
                storage_days INTEGER NOT NULL DEFAULT 0,
                total_price REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL,
                updated_at TEXT,
                box_count INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (client_id) REFERENCES users(id)
            )
        """)

        cursor = await conn.execute("PRAGMA table_info(products)")
        existing_prod_cols = {row["name"] for row in await cursor.fetchall()}
        if "box_count" not in existing_prod_cols:
            await conn.execute(
                "ALTER TABLE products ADD COLUMN box_count INTEGER NOT NULL DEFAULT 0"
            )

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                telegram_id INTEGER NOT NULL,
                phone TEXT NOT NULL,
                client_name TEXT,
                amount REAL NOT NULL,
                note TEXT,
                created_by_admin_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (client_id) REFERENCES users(id)
            )
        """)
        await conn.commit()
    finally:
        await conn.close()


async def get_user_by_telegram_id(telegram_id: int) -> dict | None:
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            "SELECT * FROM users WHERE telegram_id = ?",
            (telegram_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await conn.close()


async def get_user_by_phone(phone: str) -> dict | None:
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            "SELECT * FROM users WHERE phone = ?",
            (phone,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await conn.close()


async def create_user(
    telegram_id: int,
    phone: str,
    full_name: str | None,
    username: str | None,
    role: str = "client",
) -> int:
    conn = await get_connection()
    now = datetime.now(timezone.utc).isoformat()
    try:
        cursor = await conn.execute(
            """
            INSERT INTO users (telegram_id, phone, full_name, username, role, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (telegram_id, phone, full_name, username, role, now),
        )
        await conn.commit()
        return cursor.lastrowid
    finally:
        await conn.close()


async def create_product(
    client_id: int,
    telegram_id: int,
    phone: str,
    client_name: str | None,
    product_name: str,
    kg_amount: float,
    price_per_kg: float,
    box_count: int,
    total_price: float,
) -> int:
    conn = await get_connection()
    now = datetime.now(timezone.utc).isoformat()
    try:
        cursor = await conn.execute(
            """
            INSERT INTO products
                (client_id, telegram_id, phone, client_name, product_name,
                 kg_amount, price_per_kg, total_price, box_count, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (client_id, telegram_id, phone, client_name, product_name,
             kg_amount, price_per_kg, total_price, box_count, now),
        )
        await conn.commit()
        return cursor.lastrowid
    finally:
        await conn.close()


async def create_payment(
    client_id: int,
    telegram_id: int,
    phone: str,
    client_name: str | None,
    amount: float,
    created_by_admin_id: int,
    note: str | None = None,
) -> dict:
    conn = await get_connection()
    now = datetime.now(timezone.utc).isoformat()
    try:
        cursor = await conn.execute(
            """
            INSERT INTO payments
                (client_id, telegram_id, phone, client_name, amount, note,
                 created_by_admin_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (client_id, telegram_id, phone, client_name, amount, note,
             created_by_admin_id, now),
        )
        await conn.commit()
        return {
            "id": cursor.lastrowid,
            "client_id": client_id,
            "telegram_id": telegram_id,
            "phone": phone,
            "client_name": client_name,
            "amount": amount,
            "note": note,
            "created_by_admin_id": created_by_admin_id,
            "created_at": now,
        }
    except Exception:
        await conn.rollback()
        return None
    finally:
        await conn.close()


async def get_client_payment_summary(client_id: int) -> dict:
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            "SELECT COALESCE(SUM(total_price), 0) as s FROM products WHERE client_id = ?",
            (client_id,),
        )
        total_amount = (await cursor.fetchone())["s"]

        cursor = await conn.execute(
            "SELECT COALESCE(SUM(amount), 0) as s FROM payments WHERE client_id = ?",
            (client_id,),
        )
        paid_amount = (await cursor.fetchone())["s"]

        return {
            "total_amount": total_amount,
            "paid_amount": paid_amount,
            "remaining_amount": total_amount - paid_amount,
        }
    finally:
        await conn.close()


async def get_products_by_client_id(client_id: int) -> list[dict]:
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            "SELECT * FROM products WHERE client_id = ? ORDER BY created_at DESC",
            (client_id,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await conn.close()


async def get_all_clients() -> list[dict]:
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            "SELECT * FROM users WHERE role = 'client' ORDER BY created_at DESC"
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await conn.close()


async def get_admin_stats() -> dict:
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            "SELECT COUNT(*) as cnt FROM users WHERE role = 'client'"
        )
        total_clients = (await cursor.fetchone())["cnt"]

        cursor = await conn.execute("SELECT COUNT(*) as cnt FROM products")
        total_products = (await cursor.fetchone())["cnt"]

        cursor = await conn.execute(
            "SELECT COUNT(*) as cnt FROM products WHERE status = 'active'"
        )
        active_products = (await cursor.fetchone())["cnt"]

        cursor = await conn.execute(
            "SELECT COALESCE(SUM(kg_amount), 0) as s FROM products WHERE status = 'active'"
        )
        total_kg = (await cursor.fetchone())["s"]

        cursor = await conn.execute(
            "SELECT COALESCE(SUM(total_price), 0) as s FROM products"
        )
        total_amount = (await cursor.fetchone())["s"]

        cursor = await conn.execute(
            "SELECT COALESCE(SUM(amount), 0) as s FROM payments"
        )
        paid_amount = (await cursor.fetchone())["s"]

        return {
            "total_clients": total_clients,
            "total_products": total_products,
            "active_products": active_products,
            "total_kg": total_kg,
            "total_amount": total_amount,
            "paid_amount": paid_amount,
            "remaining_amount": total_amount - paid_amount,
        }
    finally:
        await conn.close()


async def get_active_products_for_client(client_id: int) -> list[dict]:
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            "SELECT * FROM products WHERE client_id = ? AND status = 'active' ORDER BY created_at ASC",
            (client_id,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await conn.close()


async def get_product_by_id(product_id: int) -> dict | None:
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            "SELECT * FROM products WHERE id = ?",
            (product_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await conn.close()


async def exit_product(product_id: int, admin_id: int, note: str | None = None) -> dict | None:
    conn = await get_connection()
    now = datetime.now(timezone.utc).isoformat()
    try:
        await conn.execute("PRAGMA foreign_keys=ON;")
        cursor = await conn.execute(
            "SELECT * FROM products WHERE id = ?",
            (product_id,),
        )
        product = await cursor.fetchone()
        if product is None or product["status"] != "active":
            return None

        await conn.execute(
            """
            INSERT INTO exits
                (product_id, client_id, telegram_id, phone, client_name,
                 product_name, kg_amount, price_per_kg, storage_days,
                 total_price, box_count, exited_at, created_by_admin_id, note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                product["id"], product["client_id"], product["telegram_id"],
                product["phone"], product["client_name"], product["product_name"],
                product["kg_amount"], product["price_per_kg"],
                product["storage_days"], product["total_price"],
                product["box_count"], now,
                admin_id, note,
            ),
        )
        await conn.execute(
            "UPDATE products SET status = 'exited', updated_at = ? WHERE id = ?",
            (now, product_id),
        )
        await conn.commit()

        return {
            "product_id": product["id"],
            "client_id": product["client_id"],
            "telegram_id": product["telegram_id"],
            "phone": product["phone"],
            "client_name": product["client_name"],
            "product_name": product["product_name"],
            "kg_amount": product["kg_amount"],
            "price_per_kg": product["price_per_kg"],
            "storage_days": product["storage_days"],
            "total_price": product["total_price"],
            "box_count": product["box_count"],
            "exited_at": now,
            "created_by_admin_id": admin_id,
            "note": note,
        }
    except Exception:
        await conn.rollback()
        return None
    finally:
        await conn.close()


async def get_payment_by_id(payment_id: int) -> dict | None:
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            "SELECT * FROM payments WHERE id = ?",
            (payment_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await conn.close()
