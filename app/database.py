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
