"""
dorman_provider.py — Dual-Source Dorman Data & Image Provider.

Combines product data from both Koskowski Auto Parts (primary high-res photos,
591| SKU catalog data, full body_html fitment tables) and PartCatalog (supplemental
specifications and fitment data) into a single, rich, deduplicated dataset for eBay CSV creation.
"""

import json
import logging
import random
import re
import sqlite3
import time
import urllib.parse
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from .cloudinary_uploader import upload_images_for_part

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
APP_DB_PATH = BASE_DIR / "app_data.db"
KOSKOWSKI_DB_PATH = BASE_DIR / "store_discovery" / "koskowskiautoparts_com.db"

_RATE_LIMIT_SECS = 1.5
_TIMEOUT = 12

HUMAN_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.koskowskiautoparts.com/",
}

_PARTCATALOG_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
}


def _get_from_local_cache(mpn: str) -> str:
    """Check local app_data.db cached_images table."""
    if not APP_DB_PATH.exists():
        return ""
    try:
        with sqlite3.connect(APP_DB_PATH) as conn:
            cur = conn.cursor()
            row = cur.execute(
                "SELECT image_url FROM cached_images WHERE mpn = ?", (mpn,)
            ).fetchone()
            if row and row[0]:
                return row[0]
    except Exception:
        pass
    return ""


def _save_to_local_cache(mpn: str, image_url: str, source: str = "koskowski"):
    """Persist fetched image URLs into app_data.db cached_images table."""
    if not APP_DB_PATH.exists() or not image_url:
        return
    try:
        with sqlite3.connect(APP_DB_PATH) as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS cached_images (mpn TEXT PRIMARY KEY, image_url TEXT, source TEXT, fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
            )
            conn.execute(
                "INSERT OR REPLACE INTO cached_images (mpn, image_url, source) VALUES (?, ?, ?)",
                (mpn, image_url, source)
            )
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Koskowski Fetcher & Parser
# ---------------------------------------------------------------------------

def parse_koskowski_body_html(body_html: str) -> tuple[list[dict], dict[str, str], list[str]]:
    """Parse Koskowski body_html into (compatibility, specs_dict, interchange_numbers)."""
    if not body_html:
        return [], {}, []

    soup = BeautifulSoup(body_html, "html.parser")
    
    # 1. Compatibility / Fitment Table
    compatibility = []
    fit_table = None
    for tbl in soup.find_all("table"):
        if "detail-app-row" in str(tbl):
            fit_table = tbl
            break
            
    if fit_table:
        for tr in fit_table.find_all("tr", class_="detail-app-row"):
            tds = [td.get_text(strip=True) for td in tr.find_all("td")]
            if len(tds) >= 3:
                year, make, model = tds[0], tds[1], tds[2]
                engine = tds[3] if len(tds) > 3 else ""
                pos = tds[4] if len(tds) > 4 else ""
                notes = tds[5] if len(tds) > 5 and tds[5] else ("Engine: " + engine if engine else "Direct Replacement")
                compatibility.append({
                    "Year": year,
                    "Make": make,
                    "Model": model,
                    "Position": pos if pos else "N/A",
                    "Notes": notes
                })

    # 2. Specs Table
    specs_dict = {}
    for tbl in soup.find_all("table"):
        if "table-dorman" in str(tbl) and "OE Numbers" not in str(tbl):
            for tr in tbl.find_all("tr"):
                ths = tr.find_all("th")
                tds = tr.find_all("td")
                if ths and tds:
                    key = ths[0].get_text(strip=True).rstrip(":")
                    val = tds[0].get_text(strip=True)
                    if key and val:
                        specs_dict[key] = val

    # 3. OE / Interchange Numbers
    interchange_numbers = []
    for tbl in soup.find_all("table"):
        if "DIRECT OE CROSS" in str(tbl) or "OE Numbers" in str(tbl):
            for tr in tbl.find_all("tr"):
                th = tr.find("th")
                td = tr.find("td")
                if th and td:
                    num = th.get_text(strip=True)
                    mfr = td.get_text(strip=True)
                    if num and num != "DIRECT OE CROSS":
                        interchange_numbers.append(f"{num} ({mfr})" if mfr else num)

    return compatibility, specs_dict, interchange_numbers


def fetch_koskowski_data(mpn: str, log_callback=None) -> dict:
    """Fetch Koskowski product details and CDN image URLs using 591| prefix matching."""
    def _log(msg: str):
        if log_callback:
            log_callback(msg)
        logger.info(msg)

    clean_mpn = mpn.replace("-", "").strip()
    result = {
        "title": "",
        "body_html": "",
        "images": [],
        "compatibility": [],
        "specs_dict": {},
        "interchange_numbers": []
    }

    # 0. Check Local App Cache (app_data.db cached_images table)
    cached_url = _get_from_local_cache(mpn)
    if cached_url:
        result["images"] = cached_url.split("|")
        _log(f"[Koskowski Provider] [OK] Loaded cached image URL for {mpn} from local database.")

    # 1. Query Offline Database
    if KOSKOWSKI_DB_PATH.exists():
        try:
            with sqlite3.connect(KOSKOWSKI_DB_PATH) as conn:
                cur = conn.cursor()
                query = (
                    "SELECT title, body_html, images_json FROM shopify_products WHERE "
                    "sku = ? OR sku = ? OR sku = ? OR sku = ? LIMIT 1"
                )
                row = cur.execute(query, (f"591|{mpn}", f"591|{clean_mpn}", f"591{mpn}", f"591{clean_mpn}")).fetchone()
                if not row:
                    query_fallback = (
                        "SELECT title, body_html, images_json FROM shopify_products WHERE "
                        "(sku LIKE ? OR title LIKE ?) AND "
                        "(vendor LIKE '%Dorman%' OR vendor LIKE '%Help%' OR title LIKE '%Dorman%' OR title LIKE '%Help%') "
                        "LIMIT 1"
                    )
                    row = cur.execute(query_fallback, (f"%{mpn}%", f"%{mpn}%")).fetchone()

                if row:
                    result["title"] = row[0] or ""
                    result["body_html"] = row[1] or ""
                    if not result["images"] and row[2]:
                        try:
                            imgs = json.loads(row[2])
                            result["images"] = [img.get("src", "") for img in imgs if isinstance(img, dict) and img.get("src")]
                        except Exception:
                            pass
                    
                    comp, specs, interchange = parse_koskowski_body_html(result["body_html"])
                    result["compatibility"] = comp
                    result["specs_dict"] = specs
                    result["interchange_numbers"] = interchange
                    
                    _log(f"[Koskowski Provider] [OK] Loaded offline catalog data for {mpn} ({len(comp)} fitment rows, {len(result['images'])} images)")
                    return result
        except Exception as exc:
            _log(f"[Koskowski Provider] [WARN] Offline DB check error: {exc}")

    # If image is cached and no live network needed
    if result["images"]:
        _log(f"[Koskowski Provider] [OK] Using cached image for {mpn} without live fetch.")
        return result

    # 2. Live Koskowski API Fallback
    queries = [f"591|{mpn}", f"Dorman {mpn}", mpn]
    for q in queries:
        time.sleep(random.uniform(1.0, 1.8))
        encoded_q = urllib.parse.quote(q)
        url = f"https://www.koskowskiautoparts.com/search/suggest.json?q={encoded_q}&resources[type]=product"
        _log(f"[Koskowski Provider] Searching live store for '{q}'...")
        try:
            resp = requests.get(url, headers=HUMAN_HEADERS, timeout=_TIMEOUT)
            if resp.status_code == 200:
                products = resp.json().get("resources", {}).get("results", {}).get("products", [])
                for prod in products:
                    title = prod.get("title", "")
                    vendor = prod.get("vendor", "")
                    title_l, vendor_l = title.lower(), vendor.lower()
                    if not ("dorman" in title_l or "dorman" in vendor_l or "help" in title_l or "help" in vendor_l):
                        continue

                    result["title"] = title
                    img_url = prod.get("image", "")
                    if img_url:
                        if not img_url.startswith("http"):
                            img_url = "https:" + img_url
                        result["images"] = [img_url]
                        _save_to_local_cache(mpn, img_url, "koskowski_live")
                    _log(f"[Koskowski Provider] [OK] Found live Koskowski Dorman product: '{title}'")
                    return result
        except Exception as exc:
            _log(f"[Koskowski Provider] [WARN] Live fetch failed for '{q}': {exc}")

    if result["images"]:
        _save_to_local_cache(mpn, "|".join(result["images"]), "koskowski")

    return result


# ---------------------------------------------------------------------------
# PartCatalog Fetcher & Parser
# ---------------------------------------------------------------------------

def fetch_partcatalog_data(mpn: str, brand: str = "", subtype: str = "", log_callback=None) -> dict:
    """Fetch PartCatalog product specs and fitment tables for Dorman + MPN."""
    def _log(msg: str):
        if log_callback:
            log_callback(msg)
        logger.info(msg)

    empty = {"header": "", "spec_text": "", "specs_dict": {}, "compatibility": [], "interchange_numbers": []}
    search_url = f"https://www.partcatalog.com/search?q=Dorman+{mpn}"
    _log(f"[PartCatalog Provider] Searching for Dorman {mpn}...")

    try:
        time.sleep(_RATE_LIMIT_SECS)
        resp = requests.get(search_url, headers=_PARTCATALOG_HEADERS, timeout=_TIMEOUT)
        if resp.status_code != 200:
            return empty

        soup = BeautifulSoup(resp.text, "html.parser")
        link_pattern = re.compile(rf"/products/[-a-z0-9]*{re.escape(mpn)}[-a-z0-9]*", re.IGNORECASE)
        product_link = None
        
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if link_pattern.search(href):
                href_l, text_l = href.lower(), a.get_text().lower()
                if "dorman" in href_l or "dorman" in text_l or "help" in href_l or "help" in text_l:
                    product_link = href
                    break

        if not product_link:
            _log(f"[PartCatalog Provider] No matching Dorman page on PartCatalog for {mpn}.")
            return empty

        product_url = product_link if product_link.startswith("http") else f"https://www.partcatalog.com{product_link}"
        time.sleep(_RATE_LIMIT_SECS)
        prod_resp = requests.get(product_url, headers=_PARTCATALOG_HEADERS, timeout=_TIMEOUT)
        if prod_resp.status_code != 200:
            return empty

        psoup = BeautifulSoup(prod_resp.text, "html.parser")
        h1 = psoup.find("h1")
        header = h1.get_text(strip=True) if h1 else ""

        if not ("dorman" in header.lower() or "help" in header.lower()):
            return empty

        # Tables
        specs_dict = {}
        compatibility = []
        interchanges = []

        tables = psoup.find_all("table")
        if tables:
            for row in tables[0].find_all("tr"):
                cells = row.find_all(["td", "th"])
                if len(cells) == 2:
                    k, v = cells[0].get_text(strip=True), cells[1].get_text(strip=True)
                    if k and v:
                        specs_dict[k] = v

        if len(tables) > 1:
            headers = []
            for row_idx, row in enumerate(tables[1].find_all("tr")):
                if row_idx == 0:
                    headers = [c.get_text(strip=True) for c in row.find_all(["th", "td"])]
                else:
                    cells = [c.get_text(strip=True) for c in row.find_all("td")]
                    if len(cells) == len(headers):
                        compatibility.append(dict(zip(headers, cells)))

        interchange_container = psoup.find("div", class_="pv2-interchange-grid")
        if interchange_container:
            chips = interchange_container.find_all("span", class_="pv2-interchange-chip")
            interchanges = [c.get_text(strip=True) for c in chips if c.get_text(strip=True)]

        _log(f"[PartCatalog Provider] [OK] Loaded PartCatalog data for {mpn} ({len(compatibility)} fitment rows)")
        return {
            "header": header,
            "spec_text": " | ".join([f"{k}: {v}" for k, v in specs_dict.items()]),
            "specs_dict": specs_dict,
            "compatibility": compatibility,
            "interchange_numbers": interchanges
        }

    except Exception as exc:
        _log(f"[PartCatalog Provider] [WARN] Scrape error for {mpn}: {exc}")
        return empty


# ---------------------------------------------------------------------------
# Unified Dual-Source Merger Entrypoint
# ---------------------------------------------------------------------------

def fetch_combined_dorman_data(mpn: str, brand: str = "", subtype: str = "", log_callback=None) -> dict:
    """
    Main pipeline entrypoint to get unified, combined data from Koskowski + PartCatalog + Local Photos.
    """
    def _log(msg: str):
        if log_callback:
            log_callback(msg)
        logger.info(msg)

    _log(f"[Provider] -- Resolving combined Dorman data for MPN '{mpn}' --")

    # 1. Resolve Images: Physical local photos first, Koskowski CDN fallback
    pic_url = upload_images_for_part(mpn, _log)

    # 2. Fetch Koskowski Primary Data
    k_data = fetch_koskowski_data(mpn, _log)

    if not pic_url and k_data["images"]:
        pic_url = "|".join(k_data["images"])
        _log(f"[Provider] [OK] Assigned {len(k_data['images'])} Koskowski CDN image URL(s) to PicURL.")

    # 3. Fetch PartCatalog Secondary Data
    pc_data = fetch_partcatalog_data(mpn, brand=brand, subtype=subtype, log_callback=_log)

    # 4. Deduplicate and Combine Fitment Tables
    combined_compatibility = []
    seen_fitment = set()

    for fit in k_data["compatibility"] + pc_data["compatibility"]:
        yr = fit.get("Year", "").strip()
        mk = fit.get("Make", "").strip()
        md = fit.get("Model", "").strip()
        key = f"{yr}|{mk}|{md}".lower()
        if key and key not in seen_fitment:
            seen_fitment.add(key)
            combined_compatibility.append(fit)

    # 5. Combine Specifications Dictionaries
    combined_specs = dict(k_data["specs_dict"])
    combined_specs.update(pc_data["specs_dict"])

    # 6. Combine OE Interchange Numbers
    combined_interchanges = list(dict.fromkeys(k_data["interchange_numbers"] + pc_data["interchange_numbers"]))

    # 7. Build Spec Text Summary
    spec_lines = [f"{k}: {v}" for k, v in combined_specs.items()]
    combined_spec_text = " | ".join(spec_lines)

    header = k_data["title"] or pc_data["header"] or f"Dorman {mpn}"

    _log(f"[Provider] [OK] Combined resolution complete for {mpn} - Total Fitment: {len(combined_compatibility)} rows | Specs: {len(combined_specs)} attributes | Interchanges: {len(combined_interchanges)} cross numbers.")

    return {
        "mpn": mpn,
        "product_header": header,
        "spec_text": combined_spec_text,
        "specs_dict": combined_specs,
        "compatibility": combined_compatibility,
        "interchange_numbers": combined_interchanges,
        "pic_url": pic_url,
        "koskowski_body_html": k_data.get("body_html", "")
    }
