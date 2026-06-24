"""
database.py — Local SQLite storage for offline deployment.

Replaces MongoDB Atlas with SQLite (Python built-in, zero install).
All analyses are stored in a local file: jetson_analyses.db

Schema:
    analyses(id, founder_name, idea_summary, data JSON, saved_at)

Compatible with the original save_analysis() / get_all_analyses() API
so all callers work without any changes.
"""

import os
import json
import sqlite3
from datetime import datetime

# ─── DB path ─────────────────────────────────────────────────────────────────
# Stored next to the app files on the device. Override via env var if needed.
DB_PATH = os.environ.get("SQLITE_DB_PATH", "./jetson_analyses.db")


# ─── Schema init ──────────────────────────────────────────────────────────────

def _init_db(conn: sqlite3.Connection) -> None:
    """Creates the table if it does not already exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            founder_name  TEXT,
            idea_summary  TEXT,
            data          TEXT    NOT NULL,
            saved_at      TEXT    NOT NULL
        )
    """)
    conn.commit()


def _get_conn() -> sqlite3.Connection:
    """Opens and returns a new SQLite connection with init guarantee."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    _init_db(conn)
    return conn


# ─── Public API (identical signatures to original database.py) ───────────────

def save_analysis(analysis: dict) -> bool:
    """
    Saves one analysis result to SQLite.
    Returns True if saved successfully, False if failed.
    Also writes a timestamped JSON backup to outputs/ for easy retrieval.
    """
    try:
        conn = _get_conn()
        conn.execute(
            """
            INSERT INTO analyses (founder_name, idea_summary, data, saved_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                analysis.get("founder_name", "Unknown"),
                analysis.get("idea_summary", "")[:200],
                json.dumps(analysis, ensure_ascii=False),
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        conn.close()

        # Write a timestamped JSON backup alongside the main output
        _write_json_backup(analysis)

        print(f"✅ Analysis saved to SQLite: {DB_PATH}")
        return True

    except Exception as e:
        print(f"❌ SQLite save failed: {e}")
        return False


def get_all_analyses() -> list:
    """
    Returns all saved analyses from SQLite, newest first.
    Compatible with the original get_all_analyses() return type (list of dicts).
    """
    try:
        conn = _get_conn()
        rows = conn.execute(
            "SELECT data, saved_at FROM analyses ORDER BY id DESC"
        ).fetchall()
        conn.close()

        results = []
        for row in rows:
            try:
                entry = json.loads(row["data"])
                entry["_saved_at"] = row["saved_at"]   # attach timestamp
                results.append(entry)
            except json.JSONDecodeError:
                continue
        return results

    except Exception as e:
        print(f"❌ SQLite fetch failed: {e}")
        return []


def get_analysis_count() -> int:
    """Returns the total number of analyses stored."""
    try:
        conn = _get_conn()
        count = conn.execute("SELECT COUNT(*) FROM analyses").fetchone()[0]
        conn.close()
        return count
    except Exception:
        return 0


# ─── JSON backup writer ───────────────────────────────────────────────────────

def _write_json_backup(analysis: dict) -> None:
    """
    Writes a timestamped JSON backup to outputs/.
    e.g. outputs/analysis_2026-06-17T11-30-00.json
    Useful for sharing results without accessing the SQLite DB directly.
    """
    try:
        os.makedirs("outputs", exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        fname = f"outputs/analysis_{ts}.json"
        with open(fname, "w", encoding="utf-8") as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
    except Exception:
        pass  # non-critical, don't crash the app over a backup