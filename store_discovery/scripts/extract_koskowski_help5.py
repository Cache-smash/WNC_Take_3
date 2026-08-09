import sqlite3
import csv
import re
import json

DB_PATH = "store_discovery/koskowskiautoparts_com.db"
HELP_5_FILE = "store_discovery/dorman_help_5digit_part_numbers.txt"

OUT_CSV = "store_discovery/KOSKOWSKI_DORMAN_HELP_5DIGIT_INVENTORY.csv"
OUT_TXT = "store_discovery/KOSKOWSKI_DORMAN_HELP_5DIGIT_PARTS.txt"

def load_help_5_targets():
    targets = set()
    with open(HELP_5_FILE, "r", encoding="utf-8") as f:
        for l in f:
            c = l.strip()
            if c:
                targets.add(c)
    return targets

def parse_koskowski_help_5():
    help_5_targets = load_help_5_targets()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Query items where vendor or title is Dorman/Help
    query = """
    SELECT id, title, vendor, product_type, handle, sku, barcode, price, body_html, images_json
    FROM shopify_products
    WHERE UPPER(vendor) LIKE '%DORMAN%' 
       OR UPPER(vendor) LIKE '%HELP%'
       OR UPPER(title) LIKE '%DORMAN%'
       OR UPPER(title) LIKE '%HELP!%'
    """
    rows = cursor.execute(query).fetchall()

    records = []
    matched_parts_set = set()

    for r in rows:
        p_id, title, vendor, p_type, handle, sku, barcode, price, body_html, images_json = r
        title_u = str(title or "").upper()
        sku_u = str(sku or "").upper()
        handle_u = str(handle or "").upper()

        matched_5digit = []

        # Check against target 5-digit Help! list
        for p in help_5_targets:
            # Exact token boundary check
            tokens = f" {title_u} {sku_u} {handle_u} ".replace("-", " ").replace("/", " ").replace("_", " ")
            if f" {p} " in tokens or sku_u == p or f"591|{p}" in sku_u:
                matched_5digit.append(p)
                matched_parts_set.add(p)

        if matched_5digit:
            try:
                imgs = json.loads(images_json)
                img_url = imgs[0] if imgs and len(imgs) > 0 else ""
            except Exception:
                img_url = ""

            records.append({
                "source_store": "koskowskiautoparts.com",
                "database_id": p_id,
                "help_5digit_part_numbers": ", ".join(sorted(list(set(matched_5digit)))),
                "product_title": title,
                "sku": sku,
                "vendor": vendor,
                "price": price,
                "product_url": f"https://koskowskiautoparts.com/products/{handle}",
                "image_url": img_url
            })

    conn.close()

    # Write CSV
    fieldnames = ["source_store", "database_id", "help_5digit_part_numbers", "product_title", "sku", "vendor", "price", "product_url", "image_url"]
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    # Write clean TXT list
    with open(OUT_TXT, "w", encoding="utf-8") as f:
        f.write("HELP_5DIGIT_PART_NUMBER\tPRODUCT_TITLE\tSKU\tPRICE\tPRODUCT_URL\tIMAGE_URL\n")
        for part in sorted(matched_parts_set):
            # Find representative record for title
            rep = next(r for r in records if part in r["help_5digit_part_numbers"])
            f.write(f"{part}\t{rep['product_title']}\t{rep['sku']}\t${rep['price']:.2f}\t{rep['product_url']}\t{rep['image_url']}\n")

    print(f"=== KOSKOWSKI AUTO PARTS 5-DIGIT DORMAN HELP! EXTRACTION ===")
    print(f"Matched Product Listings:       {len(records):,}")
    print(f"Unique 5-Digit Help! Part Numbers: {len(matched_parts_set):,}")
    print(f"CSV File: {OUT_CSV}")
    print(f"TXT File: {OUT_TXT}")

if __name__ == "__main__":
    parse_koskowski_help_5()
