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

def save_analysis(analysis: dict) -> int:
    """
    Saves one analysis result to SQLite.
    Returns the new row ID on success, or -1 on failure.
    Also writes a timestamped JSON backup to outputs/ for easy retrieval.
    """
    try:
        conn = _get_conn()
        cursor = conn.execute(
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
        row_id = cursor.lastrowid
        conn.commit()
        conn.close()

        _write_json_backup(analysis)
        print(f"✅ Analysis saved to SQLite id={row_id}: {DB_PATH}")
        return row_id

    except Exception as e:
        print(f"❌ SQLite save failed: {e}")
        return -1


def update_analysis_tips(analysis_id: int, tip_type: str, tips: dict) -> bool:
    """
    Saves generated readiness tips back into an existing analysis row.
    tip_type must be 'mvp' or 'investment'.
    Stores under keys 'mvp_tips' / 'investment_tips' inside the data JSON.
    """
    field = f"{tip_type}_tips"
    try:
        conn = _get_conn()
        row = conn.execute(
            "SELECT data FROM analyses WHERE id = ?", (analysis_id,)
        ).fetchone()
        if not row:
            conn.close()
            return False
        data = json.loads(row["data"])
        data[field] = tips
        conn.execute(
            "UPDATE analyses SET data = ? WHERE id = ?",
            (json.dumps(data, ensure_ascii=False), analysis_id),
        )
        conn.commit()
        conn.close()
        print(f"✅ Tips ({field}) saved to analysis id={analysis_id}")
        return True
    except Exception as e:
        print(f"❌ update_analysis_tips failed: {e}")
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