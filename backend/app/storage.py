"""Small SQLite persistence; random IDs are possession-based result access tokens."""
import json
import os
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

DB_PATH = Path(os.getenv("RENEWCALC_DB_PATH", str(Path(__file__).resolve().parents[1] / ".local" / "renewcalc.db")))


def connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS assessments (
        id TEXT PRIMARY KEY, created_at TEXT NOT NULL, result_json TEXT NOT NULL
    )""")
    return conn


def save_result(result: dict) -> str:
    result_id = str(uuid.uuid4())
    with connection() as conn:
        conn.execute("DELETE FROM assessments WHERE created_at < ?", ((datetime.now(timezone.utc) - timedelta(days=7)).isoformat(),))
        conn.execute("INSERT INTO assessments VALUES (?, ?, ?)",
                     (result_id, datetime.now(timezone.utc).isoformat(), json.dumps(result, allow_nan=False)))
    return result_id


def find_result(result_id: str) -> dict | None:
    try:
        uuid.UUID(result_id)
    except (ValueError, AttributeError):
        return None
    with connection() as conn:
        match = conn.execute("SELECT result_json FROM assessments WHERE id=? AND created_at >= ?",
                             (result_id, (datetime.now(timezone.utc) - timedelta(days=7)).isoformat())).fetchone()
    return json.loads(match[0]) if match else None
