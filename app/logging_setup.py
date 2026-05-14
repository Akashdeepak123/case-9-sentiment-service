# We hash text instead of storing it raw to avoid PII; hash lets us find a specific prediction
# by recomputing from user input.

import hashlib
import logging
import os
import sqlite3
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

LOG_DB_PATH = os.environ.get("LOG_DB_PATH", "./logs.db")


def init_db() -> None:
    db_path = os.environ.get("LOG_DB_PATH", "./logs.db")
    parent = os.path.dirname(os.path.abspath(db_path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                text_hash TEXT NOT NULL,
                text_length INTEGER NOT NULL,
                predicted_label TEXT NOT NULL,
                confidence REAL NOT NULL,
                latency_ms INTEGER NOT NULL,
                model_version TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def log_prediction(
    text: str,
    label: str,
    score: float,
    latency_ms: int,
    model_version: str,
) -> None:
    db_path = os.environ.get("LOG_DB_PATH", "./logs.db")
    text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    text_length = len(text)
    ts = datetime.now(timezone.utc).isoformat()
    try:
        conn = sqlite3.connect(db_path)
        try:
            conn.execute(
                """
                INSERT INTO predictions (
                    ts, text_hash, text_length, predicted_label,
                    confidence, latency_ms, model_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (ts, text_hash, text_length, label, score, latency_ms, model_version),
            )
            conn.commit()
        finally:
            conn.close()
    except sqlite3.Error:
        logger.exception("Failed to log prediction to SQLite")
