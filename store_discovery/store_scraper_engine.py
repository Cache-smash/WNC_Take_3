import json
import sqlite3
import urllib.request
import urllib.parse
import ssl
import csv
import sys
import os
from typing import Dict, List, Set
from stealth_config import get_stealth_headers, human_delay

HELP_5_FILE = "store_discovery/dorman_help_5digit_part_numbers.txt"
DORMAN_6_FILE = "store_discovery/dorman_6digit_part_numbers.txt"
MASTER_CSV = "store_discovery/MASTER_MATCHED_INVENTORY.csv"

def load_target_parts():
    parts = set()
    help_5 = set()
    dorman_6 = set()

    if os.path.exists(HELP_5_FILE):
        with open(HELP_5_FILE, "r", encoding="utf-8") as f:
            for l in f:
                c = l.strip()
                if c:
                    help_5.add(c)
                    parts.add(c)

    if os.path.exists(DORMAN_6_FILE):
        with open(DORMAN_6_FILE, "r", encoding="utf-8") as f:
            for l in f:
                c = l.strip()
                if c:
                    dorman_6.add(c)
                    parts.add(c)

    return parts, help_5, dorman_6

def init_db(db_path: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shopify_products (
            id INTEGER PRIMARY KEY,
            domain TEXT,
            title TEXT,
            vendor TEXT,
            product_type TEXT,
            handle TEXT,
            sku TEXT,
            barcode TEXT,
            price REAL,
            body_html TEXT,
            tags TEXT,
            images_json TEXT,
            raw_json TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def scrape_and_match_store(domain: str):
    """
    Universal, reusable engine to scrape any Shopify store domain and cross-reference inventory.
    """
    clean_domain = domain.lower().replace("https://", "").replace("http://", "").strip("/")
    db_path = f"store_discovery/{clean_domain.replace('.', '_').replace('-', '_')}.db"
    matched_csv = f"store_discovery/{clean_domain.replace('.', '_').replace('-', '_')}_matched_inventory.csv"
    matched_json = f"store_discovery/{clean_domain.replace('.', '_').replace('-', '_')}_matched_inventory.json"
    part_list_out = f"store_discovery/{clean_domain.replace('.', '_').replace('-', '_')}_matched_parts_list.txt"

    init_db(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    page = 1
    total_ingested = 0
    print(f"\n=== [UNIVERSAL PIPELINE] Ingesting Catalog for: {clean_domain} ===")

    while True:
        url = f"https://{clean_domain}/products.json?limit=250&page={page}"
        headers = get_stealth_headers()
        req = urllib.request.Request(url, headers=headers)
        human_delay(1.5, 3.0)

        print(f"Fetching Page {page:02d} for {clean_domain}...")

        try:
            with urllib.request.urlopen(req, context=ctx, timeout=12) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode('utf-8'))
                    products = data.get("products", [])
                    if not products:
                        break

                    for p in products:
                        p_id = p.get("id")
                        title = p.get("title", "")
                        vendor = p.get("vendor", "")
                        p_type = p.get("product_type", "")
                        handle = p.get("handle", "")
                        body_html = p.get("body_html", "")
                        tags_str = ", ".join(p.get("tags", [])) if isinstance(p.get("tags"), list) else str(p.get("tags", ""))
                        variants = p.get("variants", [])
                        sku = variants[0].get("sku", "") if variants else ""
                        barcode = variants[0].get("barcode", "") if variants else ""
                        price = variants[0].get("price", 0.0) if variants else 0.0
                        images_json = json.dumps([img.get("src") for img in p.get("images", [])])
                        raw_json = json.dumps(p)

                        cursor.execute("""
                            INSERT OR REPLACE INTO shopify_products (
                                id, domain, title, vendor, product_type, handle, sku, barcode,
                                price, body_html, tags, images_json, raw_json, created_at, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            p_id, clean_domain, title, vendor, p_type, handle, sku, barcode,
                            float(price) if price else 0.0, body_html, tags_str, images_json, raw_json,
                            p.get("created_at"), p.get("updated_at")
                        ))

                    conn.commit()
                    count_page = len(products)
                    total_ingested += count_page
                    print(f"  -> Ingested {count_page} products from {clean_domain} (Total: {total_ingested:,})")

                    if count_page < 250:
                        break
                    page += 1
                else:
                    break
        except Exception as e:
            print(f"Error fetching page {page} for {clean_domain}: {e}")
            break

    print(f"Finished Ingestion for {clean_domain}! Total Products: {total_ingested:,}")

    # Cross-reference step
    print(f"\n=== Cross-Referencing {clean_domain} Inventory ===")
    target_parts, help_5, dorman_6 = load_target_parts()

    rows = cursor.execute("SELECT id, title, sku, vendor, price, handle, body_html, images_json FROM shopify_products").fetchall()
    matched_records = []
    matched_parts_set = set()

    for r in rows:
        p_id, title, sku, vendor, price, handle, body_html, images_json = r
        sku_str = str(sku or "").upper()
        full_blob = f"{title or ''} {sku_str} {handle or ''} {body_html or ''}".upper()
        hits = []

        for part in help_5:
            if part in full_blob or part in sku_str:
                hits.append(f"{part} (Help! 5-Digit)")
                matched_parts_set.add(part)

        for part in dorman_6:
            p_no_h = part.replace("-", "")
            if part in full_blob or p_no_h in full_blob or part in sku_str or p_no_h in sku_str:
                hits.append(f"{part} (Dorman 6-Digit)")
                matched_parts_set.add(part)

        if hits:
            matched_records.append({
                "source_store": clean_domain,
                "database_id": p_id,
                "matched_part_numbers": ", ".join(hits),
                "product_title": title,
                "sku": sku,
                "vendor": vendor,
                "price": price,
                "product_url": f"https://{clean_domain}/products/{handle}",
                "image_url": json.loads(images_json)[0] if images_json and len(json.loads(images_json)) > 0 else ""
            })

    conn.close()

    fieldnames = ["source_store", "database_id", "matched_part_numbers", "product_title", "sku", "vendor", "price", "product_url", "image_url"]
    with open(matched_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(matched_records)

    with open(matched_json, "w", encoding="utf-8") as f:
        json.dump(matched_records, f, indent=2)

    with open(part_list_out, "w", encoding="utf-8") as f:
        for p in sorted(matched_parts_set):
            f.write(f"{p}\t{clean_domain}\n")

    print(f"\n=== MATCH RESULTS FOR {clean_domain} ===")
    print(f"Total Products Scanned: {len(rows):,}")
    print(f"Matched Listings:       {len(matched_records):,}")
    print(f"Unique Part Numbers:    {len(matched_parts_set):,}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_domain = sys.argv[1]
        scrape_and_match_store(target_domain)
    else:
        print("Usage: python store_discovery/store_scraper_engine.py <domain_name>")
