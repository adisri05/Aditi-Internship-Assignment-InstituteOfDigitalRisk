from __future__ import annotations

import sqlite3
from pathlib import Path


DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "app.db"


def connect(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path, timeout=30, isolation_level=None, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def initialize_database(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT NOT NULL UNIQUE,
            user_id TEXT NOT NULL,
            amount REAL NOT NULL,
            transaction_type TEXT NOT NULL,
            points_delta INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS user_summaries (
            user_id TEXT PRIMARY KEY,
            total_points INTEGER NOT NULL DEFAULT 0,
            transaction_count INTEGER NOT NULL DEFAULT 0,
            purchase_count INTEGER NOT NULL DEFAULT 0,
            refund_count INTEGER NOT NULL DEFAULT 0,
            bonus_count INTEGER NOT NULL DEFAULT 0,
            last_transaction_at TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
        CREATE INDEX IF NOT EXISTS idx_summaries_points ON user_summaries(total_points DESC);
        """
    )
