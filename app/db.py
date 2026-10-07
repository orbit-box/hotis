import os
import sqlite3
from contextlib import contextmanager

from app.config import settings


def _ensure_parent():
    parent = os.path.dirname(settings.db_path)
    if parent:
        os.makedirs(parent, exist_ok=True)


@contextmanager
def conn():
    _ensure_parent()
    c = sqlite3.connect(settings.db_path)
    try:
        yield c
        c.commit()
    finally:
        c.close()


def init_db():
    with conn() as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS sent_notifications (
            key TEXT PRIMARY KEY,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS market_snapshots (
            calendar_id TEXT PRIMARY KEY,
            symbol TEXT NOT NULL,
            price REAL NOT NULL,
            captured_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)


def was_sent(key: str) -> bool:
    with conn() as c:
        return c.execute("SELECT 1 FROM sent_notifications WHERE key = ?", (key,)).fetchone() is not None


def mark_sent(key: str):
    with conn() as c:
        c.execute("INSERT OR IGNORE INTO sent_notifications(key) VALUES(?)", (key,))


def save_snapshot(calendar_id: str, symbol: str, price: float):
    with conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO market_snapshots(calendar_id, symbol, price) VALUES(?,?,?)",
            (calendar_id, symbol, price),
        )


def get_snapshot(calendar_id: str):
    with conn() as c:
        row = c.execute(
            "SELECT symbol, price, captured_at FROM market_snapshots WHERE calendar_id = ?",
            (calendar_id,),
        ).fetchone()
        return row
