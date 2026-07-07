import aiosqlite
from datetime import datetime

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
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                telegram_id INTEGER NOT NULL,
                phone TEXT NOT NULL,
                client_name TEXT,
                product_name TEXT NOT NULL,
                kg_amount REAL NOT NULL,
                price_per_kg REAL NOT NULL,
                storage_days INTEGER NOT NULL,
                total_price REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL,
                updated_at TEXT,
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
    now = datetime.utcnow().isoformat()
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
    storage_days: int,
    total_price: float,
) -> int:
    conn = await get_connection()
    now = datetime.utcnow().isoformat()
    try:
        cursor = await conn.execute(
            """
            INSERT INTO products
                (client_id, telegram_id, phone, client_name, product_name,
                 kg_amount, price_per_kg, storage_days, total_price, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (client_id, telegram_id, phone, client_name, product_name,
             kg_amount, price_per_kg, storage_days, total_price, now),
        )
        await conn.commit()
        return cursor.lastrowid
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
