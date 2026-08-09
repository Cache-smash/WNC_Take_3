"""
db_manager.py — SQLite initialization and part lookup.

On first run, reads US_Parts_Catalog_Dorman_Help.tsv (8 columns) and
ingests every row into app_data.db with an index on ManufacturePartNumber.
All subsequent runs skip ingestion and go straight to fast SQL lookups.

Schema (mirrors TSV exactly):
    epid               — eBay Product ID
    title              — Full product title string
    brand              — e.g. "Dorman/Help"
    mpn                — ManufacturePartNumber (primary key / lookup key)
    subtype            — Product sub-type descriptor
    type               — Top-level category type
    category_id        — eBay category numeric ID
    category_breadcrumb — Full eBay breadcrumb string
"""

import csv
import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
DB_PATH  = BASE_DIR / "app_data.db"
TSV_PATH = BASE_DIR / "US_Parts_Catalog_Dorman_Help.tsv"

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS parts (
    epid                TEXT,
    title               TEXT,
    brand               TEXT,
    mpn                 TEXT PRIMARY KEY,
    subtype             TEXT,
    type                TEXT,
    category_id         TEXT,
    category_breadcrumb TEXT
);
"""

_CREATE_INDEX = "CREATE INDEX IF NOT EXISTS idx_mpn ON parts (mpn);"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def init_database(log_callback=None) -> None:
    """
    Check for app_data.db; if absent, parse the TSV and populate SQLite.
    Accepts an optional log_callback(str) to route progress messages to the UI.
    """
    def _log(msg: str) -> None:
        if log_callback:
            log_callback(msg)
        logger.info(msg)

    if DB_PATH.exists():
        _log(f"[DB] Database found at '{DB_PATH.name}'. Skipping ingestion.")
        return

    if not TSV_PATH.exists():
        raise FileNotFoundError(f"Catalog TSV not found: {TSV_PATH}")

    _log(f"[DB] Initializing database from '{TSV_PATH.name}' — this runs once...")

    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(_CREATE_TABLE)
        cur.execute(_CREATE_INDEX)

        row_count = 0
        with TSV_PATH.open(encoding="utf-8") as fh:
            reader = csv.DictReader(fh, delimiter="\t")
            batch = []
            for row in reader:
                batch.append((
                    row.get("ePID", "").strip(),
                    row.get("Title", "").strip(),
                    row.get("Brand", "").strip(),
                    row.get("ManufacturePartNumber", "").strip(),
                    row.get("SubType", "").strip(),
                    row.get("Type", "").strip(),
                    row.get("CategoryID", "").strip(),
                    row.get("Category Breadcrumb", "").strip(),
                ))
                row_count += 1
                if len(batch) >= 500:
                    cur.executemany(
                        "INSERT OR REPLACE INTO parts VALUES (?,?,?,?,?,?,?,?)", batch
                    )
                    batch.clear()
                if row_count % 2000 == 0:
                    _log(f"[DB] Ingested {row_count:,} rows...")

            if batch:
                cur.executemany(
                    "INSERT OR REPLACE INTO parts VALUES (?,?,?,?,?,?,?,?)", batch
                )

        conn.commit()
        _log(f"[DB] [OK] Ingestion complete -- {row_count:,} parts indexed in '{DB_PATH.name}'.")
    except Exception:
        conn.close()                       # Release file handle first
        DB_PATH.unlink(missing_ok=True)   # Then remove corrupt DB so next run retries
        raise
    else:
        conn.close()


def lookup_parts(mpn_list: list[str]) -> list[dict]:
    """
    Query the local database for a list of ManufacturePartNumbers.
    Returns a list of row dicts with all 8 columns preserved.
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
            f"SELECT epid, title, brand, mpn, subtype, type, category_id, category_breadcrumb "
            f"FROM parts WHERE mpn IN ({placeholders}) "
            f"ORDER BY CASE WHEN brand LIKE '%Dorman%' OR brand LIKE '%Help%' THEN 0 ELSE 1 END",
            mpn_list,
        ).fetchall()
        # Ensure only 1 row per MPN, taking the highest priority (Dorman) row
        seen = set()
        results = []
        for r in rows:
            dict_r = dict(r)
            mpn_key = dict_r.get("mpn", "").strip()
            if mpn_key not in seen:
                seen.add(mpn_key)
                results.append(dict_r)
        return results
    finally:
        conn.close()
