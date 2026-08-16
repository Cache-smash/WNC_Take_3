"""
db_manager.py — SQLite part lookup and inventory database management.

Provides fast SQL lookups against local app_data.db which mirrors WNC_Archive inventory schema.

Schema:
    mpn, brand, title, description, category_id, price, quantity,
    custom_label, item_specifics, pic_urls, local_photo_paths, created_at, updated_at
"""

import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
DB_PATH  = BASE_DIR / "app_data_(catalog-lookup).db"

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS parts (
    mpn                TEXT PRIMARY KEY,
    brand              TEXT NOT NULL,
    title              TEXT NOT NULL,
    description        TEXT,
    category_id        TEXT,
    price              REAL,
    quantity           INTEGER,
    custom_label       TEXT,
    item_specifics     JSON,
    pic_urls           TEXT,
    local_photo_paths  TEXT,
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

_CREATE_INDEX = "CREATE INDEX IF NOT EXISTS idx_mpn ON parts (mpn);"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def init_database(log_callback=None) -> None:
    """
    Ensure app_data.db table structure exists.
    Accepts an optional log_callback(str) to route progress messages to the UI.
    """
    def _log(msg: str) -> None:
        if log_callback:
            log_callback(msg)
        logger.info(msg)

    if not DB_PATH.exists():
        _log(f"[DB] Initializing database table structure at '{DB_PATH.name}'...")
        conn = sqlite3.connect(DB_PATH)
        try:
            cur = conn.cursor()
            cur.execute(_CREATE_TABLE)
            cur.execute(_CREATE_INDEX)
            conn.commit()
            _log(f"[DB] [OK] Table created in '{DB_PATH.name}'.")
        finally:
            conn.close()
    else:
        _log(f"[DB] Database found at '{DB_PATH.name}'. Ready for lookups.")


def lookup_parts(mpn_list: list[str]) -> list[dict]:
    """
    Query the local database for a list of ManufacturePartNumbers.
    Returns a list of row dicts with all inventory columns preserved.
    Raises FileNotFoundError if the DB has not been initialized.
    """
    if not DB_PATH.exists():
        raise FileNotFoundError(
            "Database not found. Call init_database() before lookup_parts()."
        )
    if not mpn_list:
        return []

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        placeholders = ",".join("?" * len(mpn_list))
        rows = conn.execute(
            f"SELECT * FROM parts WHERE mpn IN ({placeholders}) "
            f"ORDER BY CASE WHEN brand LIKE '%Dorman%' OR brand LIKE '%Help%' THEN 0 ELSE 1 END",
            mpn_list,
        ).fetchall()
        
        seen = set()
        results = []
        for r in rows:
            dict_r = dict(r)
            mpn_key = str(dict_r.get("mpn", "")).strip()
            if mpn_key not in seen:
                seen.add(mpn_key)
                results.append(dict_r)
        return results
    finally:
        conn.close()

