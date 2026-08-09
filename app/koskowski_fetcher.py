"""
koskowski_fetcher.py — Human-fingerprinted Koskowski Shopify CDN image retriever.

Lookups:
1. First checks local DB (app_data.db / cached_images table or koskowskiautoparts_com.db).
2. If missing, performs a human-fingerprinted HTTP request to Koskowski Shopify API.
3. Caches retrieved image URLs into app_data.db for zero-latency future runs.
"""

import json
import logging
import random
import re
import sqlite3
import time
import urllib.parse
import urllib.request
from pathlib import Path

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
APP_DB_PATH = BASE_DIR / "app_data.db"
KOSKOWSKI_DB_PATH = BASE_DIR / "store_discovery" / "koskowskiautoparts_com.db"

# Human Windows 11 Chrome Fingerprint Headers
HUMAN_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Ch-Ua": '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Referer": "https://www.koskowskiautoparts.com/",
}

_CREATE_CACHE_TABLE = """
CREATE TABLE IF NOT EXISTS cached_images (
    mpn TEXT PRIMARY KEY,
    image_url TEXT,
    source TEXT,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

def init_image_cache_table():
    if APP_DB_PATH.exists():
        with sqlite3.connect(APP_DB_PATH) as conn:
            conn.execute(_CREATE_CACHE_TABLE)

def _get_from_local_cache(mpn: str) -> str:
    """Check local app_data.db cached_images table."""
    init_image_cache_table()
    if not APP_DB_PATH.exists():
        return ""
    try:
        with sqlite3.connect(APP_DB_PATH) as conn:
            cur = conn.cursor()
            res = cur.execute("SELECT image_url FROM cached_images WHERE mpn = ?", (mpn,)).fetchone()
            if res and res[0]:
                return res[0]
    except Exception as e:
        logger.warning(f"Error checking local cached_images: {e}")
    return ""

def _get_from_koskowski_db(mpn: str) -> str:
    """Check offline koskowskiautoparts_com.db sqlite DB if present."""
    if not KOSKOWSKI_DB_PATH.exists():
        return ""
    try:
        clean_mpn = mpn.replace("-", "").strip()
        with sqlite3.connect(KOSKOWSKI_DB_PATH) as conn:
            cur = conn.cursor()
            # 1. Exact 591| SKU prefix match (Koskowski Dorman SKU format)
            query_exact = (
                "SELECT images_json FROM shopify_products WHERE "
                "sku = ? OR sku = ? OR sku = ? OR sku = ? LIMIT 1"
            )
            res = cur.execute(query_exact, (f"591|{mpn}", f"591|{clean_mpn}", f"591{mpn}", f"591{clean_mpn}")).fetchone()
            
            # 2. Fallback to vendor / title matching Dorman
            if not res:
                query_fallback = (
                    "SELECT images_json FROM shopify_products WHERE "
                    "(sku LIKE ? OR title LIKE ?) AND "
                    "(vendor LIKE '%Dorman%' OR vendor LIKE '%Help%' OR title LIKE '%Dorman%' OR title LIKE '%Help%') "
                    "LIMIT 1"
                )
                res = cur.execute(query_fallback, (f"%{mpn}%", f"%{mpn}%")).fetchone()

            if res and res[0]:
                imgs = json.loads(res[0])
                if isinstance(imgs, list) and imgs:
                    first_img = imgs[0]
                    if isinstance(first_img, dict) and "src" in first_img:
                        return first_img["src"]
                    elif isinstance(first_img, str):
                        return first_img
    except Exception as e:
        logger.warning(f"Error checking koskowskiautoparts_com.db: {e}")
    return ""

def _save_to_local_cache(mpn: str, image_url: str, source: str = "koskowski_cdn"):
    """Persist fetched image URL into app_data.db."""
    init_image_cache_table()
    try:
        with sqlite3.connect(APP_DB_PATH) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO cached_images (mpn, image_url, source) VALUES (?, ?, ?)",
                (mpn, image_url, source)
            )
            conn.commit()
    except Exception as e:
        logger.warning(f"Failed to save cached image for {mpn}: {e}")

def _fetch_live_koskowski_cdn(mpn: str, log_callback=None) -> str:
    """Perform a human-fingerprinted HTTP search against Koskowski Shopify API."""
    def _log(msg: str):
        if log_callback:
            log_callback(msg)
        logger.info(msg)

    import requests

    # Try exact 591| prefix query first, then Dorman + MPN
    queries = [f"591|{mpn}", f"Dorman {mpn}", mpn]

    for q in queries:
        delay = random.uniform(1.0, 2.0)
        time.sleep(delay)

        encoded_q = urllib.parse.quote(q)
        suggest_url = f"https://www.koskowskiautoparts.com/search/suggest.json?q={encoded_q}&resources[type]=product"

        _log(f"[Koskowski CDN] Live searching for '{q}'...")

        try:
            resp = requests.get(suggest_url, headers=HUMAN_HEADERS, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                products = data.get("resources", {}).get("results", {}).get("products", [])

                for prod in products:
                    title = prod.get("title", "")
                    vendor = prod.get("vendor", "")
                    handle = prod.get("handle", "")
                    
                    # Strict Dorman / Help brand verification
                    title_lower = title.lower()
                    vendor_lower = vendor.lower()
                    handle_lower = handle.lower()

                    if not ("dorman" in title_lower or "dorman" in vendor_lower or "dorman" in handle_lower or "help" in title_lower or "help" in vendor_lower):
                        continue

                    image_url = prod.get("image", "")
                    if image_url:
                        if not image_url.startswith("http"):
                            image_url = "https:" + image_url
                        _log(f"[Koskowski CDN] [OK] Matched Dorman product: '{title}' -> {image_url}")
                        _save_to_local_cache(mpn, image_url, source="live_koskowski_cdn")
                        return image_url

        except Exception as exc:
            _log(f"[Koskowski CDN] [WARN] Live fetch failed for '{q}': {exc}")

    return ""

def get_koskowski_image_url(mpn: str, log_callback=None) -> str:
    """
    Public entrypoint for resolving Koskowski CDN image.
    Sequence:
    1. Check local app_data.db cached_images
    2. Check store_discovery/koskowskiautoparts_com.db
    3. Live human-fingerprinted fetch
    """
    def _log(msg: str):
        if log_callback:
            log_callback(msg)
        logger.info(msg)

    # 1. Local App Cache
    cached = _get_from_local_cache(mpn)
    if cached:
        _log(f"[Koskowski CDN] [OK] Using cached image URL for {mpn}")
        return cached

    # 2. Offline Scraped DB
    db_match = _get_from_koskowski_db(mpn)
    if db_match:
        _log(f"[Koskowski CDN] [OK] Found image in offline database for {mpn}")
        _save_to_local_cache(mpn, db_match, source="offline_koskowski_db")
        return db_match

    # 3. Live Fetch
    return _fetch_live_koskowski_cdn(mpn, log_callback=log_callback)
