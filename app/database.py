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
        if "is_in_ombor_sheet" not in existing_prod_cols:
            await conn.execute(
                "ALTER TABLE products ADD COLUMN is_in_ombor_sheet INTEGER NOT NULL DEFAULT 0"
            )

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                product_id INTEGER,
                telegram_id INTEGER NOT NULL,
                phone TEXT NOT NULL,
                client_name TEXT,
                amount REAL NOT NULL,
                created_by_admin_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (client_id) REFERENCES users(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)

        cursor = await conn.execute("PRAGMA table_info(payments)")
        existing_pay_cols = {row["name"] for row in await cursor.fetchall()}
        if "product_id" not in existing_pay_cols:
            await conn.execute(
                "ALTER TABLE payments ADD COLUMN product_id INTEGER"
            )

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS product_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                emoji TEXT NOT NULL DEFAULT '📦',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT
            )
        """)

        await seed_default_product_types(conn)

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


async def get_user_by_id(user_id: int) -> dict | None:
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,),
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
    except Exception:
        await conn.rollback()
        raise
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
                 kg_amount, price_per_kg, storage_days, total_price, box_count, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
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
    product_id: int,
    telegram_id: int,
    phone: str,
    client_name: str | None,
    amount: float,
    created_by_admin_id: int,
) -> dict | None:
    conn = await get_connection()
    now = datetime.now(timezone.utc).isoformat()
    try:
        cursor = await conn.execute(
            """
            INSERT INTO payments
                (client_id, product_id, telegram_id, phone, client_name,
                 amount, created_by_admin_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (client_id, product_id, telegram_id, phone, client_name,
             amount, created_by_admin_id, now),
        )
        await conn.commit()
        return {
            "id": cursor.lastrowid,
            "client_id": client_id,
            "product_id": product_id,
            "telegram_id": telegram_id,
            "phone": phone,
            "client_name": client_name,
            "amount": amount,
            "created_by_admin_id": created_by_admin_id,
            "created_at": now,
        }
    except Exception:
        await conn.rollback()
        return None
    finally:
        await conn.close()


async def get_product_payment_summary(product_id: int) -> dict:
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            "SELECT total_price FROM products WHERE id = ?",
            (product_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return {"total_amount": 0, "paid_amount": 0, "remaining_amount": 0}

        total_amount = row["total_price"]

        cursor = await conn.execute(
            "SELECT COALESCE(SUM(amount), 0) as s FROM payments WHERE product_id = ?",
            (product_id,),
        )
        paid_amount = (await cursor.fetchone())["s"]

        return {
            "total_amount": total_amount,
            "paid_amount": paid_amount,
            "remaining_amount": max(total_amount - paid_amount, 0),
        }
    finally:
        await conn.close()


async def get_client_active_payment_summary(client_id: int) -> dict:
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            "SELECT COALESCE(SUM(total_price), 0) as s FROM products WHERE client_id = ? AND status = 'active'",
            (client_id,),
        )
        total_amount = (await cursor.fetchone())["s"]

        cursor = await conn.execute(
            """
            SELECT COALESCE(SUM(p.amount), 0) as s FROM payments p
            INNER JOIN products pr ON p.product_id = pr.id
            WHERE pr.client_id = ? AND pr.status = 'active'
            """,
            (client_id,),
        )
        paid_amount = (await cursor.fetchone())["s"]

        return {
            "total_amount": total_amount,
            "paid_amount": paid_amount,
            "remaining_amount": max(total_amount - paid_amount, 0),
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
            "SELECT COUNT(*) as cnt FROM products WHERE status = 'active' AND is_in_ombor_sheet = 1"
        )
        active_products = (await cursor.fetchone())["cnt"]

        cursor = await conn.execute(
            "SELECT COALESCE(SUM(kg_amount), 0) as s FROM products WHERE status = 'active' AND is_in_ombor_sheet = 1"
        )
        active_kg = (await cursor.fetchone())["s"]

        cursor = await conn.execute(
            "SELECT COALESCE(SUM(total_price), 0) as s FROM products WHERE status = 'active' AND is_in_ombor_sheet = 1"
        )
        active_total_amount = (await cursor.fetchone())["s"]

        cursor = await conn.execute(
            """
            SELECT COALESCE(SUM(p.amount), 0) as s FROM payments p
            INNER JOIN products pr ON p.product_id = pr.id
            WHERE pr.status = 'active' AND pr.is_in_ombor_sheet = 1
            """
        )
        active_paid_amount = (await cursor.fetchone())["s"]

        cursor = await conn.execute(
            "SELECT COUNT(*) as cnt FROM products WHERE status = 'exited'"
        )
        exited_products = (await cursor.fetchone())["cnt"]

        cursor = await conn.execute(
            "SELECT COALESCE(SUM(kg_amount), 0) as s FROM products WHERE status = 'exited'"
        )
        exited_kg = (await cursor.fetchone())["s"]

        cursor = await conn.execute(
            "SELECT COALESCE(SUM(total_price), 0) as s FROM products WHERE status = 'exited'"
        )
        exited_total_amount = (await cursor.fetchone())["s"]

        return {
            "total_clients": total_clients,
            "total_products": total_products,
            "active_products": active_products,
            "active_kg": active_kg,
            "active_total_amount": active_total_amount,
            "active_paid_amount": active_paid_amount,
            "active_remaining_amount": max(active_total_amount - active_paid_amount, 0),
            "exited_products": exited_products,
            "exited_kg": exited_kg,
            "exited_total_amount": exited_total_amount,
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


async def mark_product_in_ombor_sheet(product_id: int, value: bool = True) -> None:
    conn = await get_connection()
    try:
        await conn.execute(
            "UPDATE products SET is_in_ombor_sheet = ? WHERE id = ?",
            (1 if value else 0, product_id),
        )
        await conn.commit()
    finally:
        await conn.close()


async def get_sheet_visible_active_products_by_client_id(client_id: int) -> list[dict]:
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            "SELECT * FROM products WHERE client_id = ? AND status = 'active' AND is_in_ombor_sheet = 1 ORDER BY created_at ASC",
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


async def exit_product(product_id: int, admin_id: int) -> dict | None:
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
                 total_price, box_count, exited_at, created_by_admin_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                product["id"], product["client_id"], product["telegram_id"],
                product["phone"], product["client_name"], product["product_name"],
                product["kg_amount"], product["price_per_kg"],
                product["storage_days"], product["total_price"],
                product["box_count"], now, admin_id,
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
        }
    except Exception:
        await conn.rollback()
        return None
    finally:
        await conn.close()


async def get_products_by_client_id_asc(client_id: int) -> list[dict]:
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


async def get_payments_by_client_id(client_id: int) -> list[dict]:
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            "SELECT * FROM payments WHERE client_id = ? ORDER BY created_at ASC",
            (client_id,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await conn.close()


async def get_payments_by_product_id(product_id: int) -> list[dict]:
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            "SELECT * FROM payments WHERE product_id = ? ORDER BY created_at ASC",
            (product_id,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
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


async def seed_default_product_types(conn: aiosqlite.Connection | None = None) -> None:
    own_conn = False
    if conn is None:
        conn = await get_connection()
        own_conn = True
    try:
        cur = await conn.execute("SELECT COUNT(*) as c FROM product_types")
        row = await cur.fetchone()
        if row["c"] == 0:
            now = datetime.now(timezone.utc).isoformat()
            defaults = [
                ("Olma", "🍎", now),
                ("Nok", "🍐", now),
            ]
            for name, emoji, t in defaults:
                try:
                    await conn.execute(
                        "INSERT INTO product_types (name, emoji, created_at) VALUES (?, ?, ?)",
                        (name, emoji, t),
                    )
                except Exception:
                    pass
            await conn.commit()
    finally:
        if own_conn:
            await conn.close()


async def get_active_product_types() -> list[dict]:
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            "SELECT * FROM product_types WHERE is_active = 1 ORDER BY created_at ASC"
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await conn.close()


async def get_product_type_by_name(name: str) -> dict | None:
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            "SELECT * FROM product_types WHERE name = ?", (name.strip(),)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await conn.close()


async def create_product_type(name: str) -> int | None:
    cleaned = name.strip()
    existing = await get_product_type_by_name(cleaned)
    if existing is not None:
        return None
    conn = await get_connection()
    now = datetime.now(timezone.utc).isoformat()
    try:
        cursor = await conn.execute(
            "INSERT INTO product_types (name, emoji, created_at) VALUES (?, '📦', ?)",
            (cleaned, now),
        )
        await conn.commit()
        return cursor.lastrowid
    except Exception:
        await conn.rollback()
        return None
    finally:
        await conn.close()


async def get_product_type_by_id(type_id: int) -> dict | None:
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            "SELECT * FROM product_types WHERE id = ?", (type_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await conn.close()


async def set_setting(key: str, value: str) -> None:
    conn = await get_connection()
    now = datetime.now(timezone.utc).isoformat()
    try:
        await conn.execute(
            "INSERT INTO settings (key, value, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at",
            (key, value, now),
        )
        await conn.commit()
    finally:
        await conn.close()


async def get_setting(key: str) -> str | None:
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            "SELECT value FROM settings WHERE key = ?",
            (key,),
        )
        row = await cursor.fetchone()
        return row["value"] if row else None
    finally:
        await conn.close()


async def get_warehouse_location() -> dict | None:
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            "SELECT key, value, updated_at FROM settings WHERE key IN (?, ?, ?)",
            ("warehouse_latitude", "warehouse_longitude", "warehouse_location_name"),
        )
        rows = await cursor.fetchall()
        if not rows:
            return None
        result = {row["key"]: row["value"] for row in rows}
        try:
            result["warehouse_latitude"] = float(result["warehouse_latitude"])
            result["warehouse_longitude"] = float(result["warehouse_longitude"])
        except (KeyError, ValueError, TypeError):
            return None
        return result
    finally:
        await conn.close()


async def save_warehouse_location(
    latitude: float,
    longitude: float,
    location_name: str | None = None,
) -> None:
    conn = await get_connection()
    now = datetime.now(timezone.utc).isoformat()
    try:
        await conn.execute(
            "INSERT INTO settings (key, value, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at",
            ("warehouse_latitude", str(latitude), now),
        )
        await conn.execute(
            "INSERT INTO settings (key, value, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at",
            ("warehouse_longitude", str(longitude), now),
        )
        if location_name is not None:
            await conn.execute(
                "INSERT INTO settings (key, value, updated_at) VALUES (?, ?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at",
                ("warehouse_location_name", location_name, now),
            )
        await conn.commit()
    finally:
        await conn.close()
