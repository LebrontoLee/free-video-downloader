"""
SQLite database layer — connection management and schema initialization.
Uses WAL mode for concurrent reads and parameterized queries for safety.
"""
import sqlite3
import threading
from pathlib import Path

DB_PATH = Path(__file__).parent / "app.db"

_local = threading.local()


def get_db() -> sqlite3.Connection:
    """Get a thread-local database connection with WAL mode and foreign keys.

    Returns a sqlite3.Connection configured with:
      - WAL journal mode (concurrent reads + writes)
      - Foreign key enforcement
      - Row factory for dict-like access
    """
    conn = getattr(_local, "conn", None)
    if conn is None:
        conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        _local.conn = conn
    return conn


def close_db():
    """Close the thread-local connection if it exists."""
    conn = getattr(_local, "conn", None)
    if conn is not None:
        conn.close()
        _local.conn = None


def init_db():
    """Create all tables and indexes if they don't exist.

    Called once on application startup. Safe to call multiple times
    (uses IF NOT EXISTS for all DDL statements).
    """
    conn = get_db()

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            email           TEXT NOT NULL UNIQUE,
            password_hash   TEXT NOT NULL,
            salt            TEXT NOT NULL,
            is_pro          INTEGER NOT NULL DEFAULT 0,
            pro_expires_at  TEXT,
            created_at      TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS memberships (
            id                      INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id                 INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            stripe_customer_id      TEXT,
            stripe_subscription_id  TEXT,
            stripe_price_id         TEXT,
            status                  TEXT NOT NULL DEFAULT 'inactive',
            current_period_start    TEXT,
            current_period_end      TEXT,
            canceled_at             TEXT,
            created_at              TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at              TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS payments (
            id                          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id                     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            stripe_checkout_session_id  TEXT NOT NULL UNIQUE,
            stripe_payment_intent_id    TEXT,
            stripe_subscription_id      TEXT,
            amount                      INTEGER NOT NULL,
            currency                    TEXT NOT NULL DEFAULT 'usd',
            status                      TEXT NOT NULL DEFAULT 'pending',
            created_at                  TEXT NOT NULL DEFAULT (datetime('now'))
        );

        -- Usage tracking for free-tier AI limits (3/day)
        CREATE TABLE IF NOT EXISTS usage_logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER REFERENCES users(id) ON DELETE CASCADE,
            action_type TEXT NOT NULL,
            url         TEXT,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_usage_user_date
            ON usage_logs(user_id, action_type, created_at);

        CREATE INDEX IF NOT EXISTS idx_memberships_user
            ON memberships(user_id);

        CREATE INDEX IF NOT EXISTS idx_memberships_sub
            ON memberships(stripe_subscription_id);

        CREATE INDEX IF NOT EXISTS idx_payments_session
            ON payments(stripe_checkout_session_id);

        CREATE INDEX IF NOT EXISTS idx_users_email
            ON users(email);
    """)

    conn.commit()
