import os
import sqlite3
import sys

# Resolve the database path exactly as the application does (no .env editing).
try:
    from app.config import config

    DB_URL = config.database_url
except Exception:
    DB_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///data/ombor_bot.sqlite3")

DB_PATH = DB_URL.replace("sqlite+aiosqlite:///", "")


def main() -> None:
    if not os.path.exists(DB_PATH):
        print(f"ERROR: database file not found: {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON;")
    try:
        cur = conn.cursor()

        cur.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        all_tables = [r[0] for r in cur.fetchall()]

        # Build FK reference map: table -> list of referenced tables.
        fk_map: dict[str, list[str]] = {}
        for t in all_tables:
            cur.execute(f"PRAGMA foreign_key_list({t})")
            fk_map[t] = [row[2] for row in cur.fetchall()]

        # Tables to clear: users + every table that (transitively) references it.
        to_clear: set[str] = {"users"}
        changed = True
        while changed:
            changed = False
            for t in all_tables:
                if t in to_clear:
                    continue
                if any(ref in to_clear for ref in fk_map.get(t, [])):
                    to_clear.add(t)
                    changed = True

        # Topological deletion order: delete a table only after nothing
        # remaining still references it (children before parents).
        remaining = set(to_clear)
        order: list[str] = []
        while remaining:
            progress = False
            for t in list(remaining):
                refs_to_t = {
                    other for other in remaining if t in fk_map.get(other, [])
                }
                if not refs_to_t:
                    order.append(t)
                    remaining.discard(t)
                    progress = True
            if not progress:
                # Unexpected cycle guard: clear the rest (FK already enforced).
                order.extend(sorted(remaining))
                remaining.clear()

        print(f"Database: {DB_PATH}")
        print("Tables to clear (deletion order):", " -> ".join(order))

        print("\nBefore clearing:")
        before: dict[str, int] = {}
        for t in order:
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            before[t] = cur.fetchone()[0]
            print(f"  {t}: {before[t]}")

        for t in order:
            cur.execute(f"DELETE FROM {t}")

        if "sqlite_sequence" in all_tables:
            for t in order:
                cur.execute("DELETE FROM sqlite_sequence WHERE name = ?", (t,))

        conn.commit()

        print("\nAfter clearing:")
        for t in order:
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            print(f"  {t}: {cur.fetchone()[0]}")

        cur.execute("SELECT COUNT(*) FROM users")
        users_after = cur.fetchone()[0]
        print(f"\nusers count after: {users_after}")

        if users_after == 0:
            print("OK: all users cleared successfully.")
        else:
            print("WARNING: users table still has rows.")
            sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
