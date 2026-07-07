import aiosqlite

from app.config import config

DATABASE_PATH = config.database_url.replace("sqlite+aiosqlite:///", "")


async def get_connection() -> aiosqlite.Connection:
    conn = await aiosqlite.connect(DATABASE_PATH)
    conn.row_factory = aiosqlite.Row
    return conn


async def init_db():
    conn = await get_connection()
    try:
        await conn.execute("PRAGMA journal_mode=WAL;")
        await conn.execute("PRAGMA foreign_keys=ON;")
        await conn.commit()
    finally:
        await conn.close()
