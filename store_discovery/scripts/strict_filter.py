import glob
import json
import csv
import sqlite3
import os

OUT_STRICT_CSV = "store_discovery/STRICT_VERIFIED_DORMAN_INVENTORY.csv"
OUT_STRICT_JSON = "store_discovery/STRICT_VERIFIED_DORMAN_INVENTORY.json"
OUT_STRICT_TXT = "store_discovery/STRICT_VERIFIED_DORMAN_PARTS.txt"

HELP_5_FILE = "store_discovery/dorman_help_5digit_part_numbers.txt"
DORMAN_6_FILE = "store_discovery/dorman_6digit_part_numbers.txt"

def load_target_parts():
    help_5 = set()
    dorman_6 = set()

    with open(HELP_5_FILE, "r", encoding="utf-8") as f:
        for l in f:
            c = l.strip()
            if c:
                help_5.add(c)

    with open(DORMAN_6_FILE, "r", encoding="utf-8") as f:
        for l in f:
            c = l.strip()
            if c:
                dorman_6.add(c)

    return help_5, dorman_6

def run_fast_strict_filter():
    help_5, dorman_6 = load_target_parts()
    db_files = glob.glob("store_discovery/*.db")

    print(f"=== FAST STRICT VERIFICATION ACROSS {len(db_files)} DATABASES ===")

    strict_records = []
    part_to_stores = {}

    for db_path in db_files:
        domain_name = os.path.basename(db_path).replace(".db", "").replace("_com", ".com").replace("_parts", "-parts")
        print(f"Scanning Database: {db_path} ({domain_name})...")

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Strict SQL Rule: Must be Dorman/Help vendor or title
        query = """
        SELECT id, title, vendor, product_type, handle, sku, barcode, price, body_html, images_json
        FROM shopify_products
        WHERE UPPER(vendor) LIKE '%DORMAN%' 
           OR UPPER(vendor) LIKE '%HELP%'
           OR UPPER(title) LIKE '%DORMAN%'
           OR UPPER(title) LIKE '%HELP!%'
        """
        rows = cursor.execute(query).fetchall()

        for r in rows:
            p_id, title, vendor, p_type, handle, sku, barcode, price, body_html, images_json = r
            actual_domain = domain_name

            title_u = str(title or "").upper()
            sku_u = str(sku or "").upper()
            handle_u = str(handle or "").upper()
            
            # Form clean space-padded token string to ensure exact word matches
            tokens = f" {title_u} {sku_u} {handle_u} ".replace("-", " ").replace("/", " ").replace("_", " ")

            matched_targets = []

            # Exact matching for Help! 5-Digit parts
            for p in help_5:
                if f" {p} " in tokens or p == sku_u or f" {p} " in f" {title_u} ":
                    matched_targets.append(f"{p} (Help! 5-Digit)")
                    if p not in part_to_stores:
                        part_to_stores[p] = set()
                    part_to_stores[p].add(actual_domain)

            # Exact matching for Dorman 6-Digit parts
            for p in dorman_6:
                p_nohyphen = p.replace("-", "")
                if f" {p.upper()} " in f" {title_u} " or f" {p_nohyphen} " in tokens or p.upper() in sku_u or p_nohyphen in sku_u:
                    matched_targets.append(f"{p} (Dorman 6-Digit)")
                    if p not in part_to_stores:
                        part_to_stores[p] = set()
                    part_to_stores[p].add(actual_domain)

            if matched_targets:
                try:
                    imgs = json.loads(images_json)
                    img_url = imgs[0] if imgs and len(imgs) > 0 else ""
                except Exception:
                    img_url = ""

                strict_records.append({
                    "source_store": actual_domain,
                    "database_id": p_id,
                    "matched_part_numbers": ", ".join(list(set(matched_targets))),
                    "product_title": title,
                    "sku": sku,
                    "vendor": vendor,
                    "price": price,
                    "product_url": f"https://{actual_domain}/products/{handle}",
                    "image_url": img_url
                })

        conn.close()

    # Output Files
    fieldnames = ["source_store", "database_id", "matched_part_numbers", "product_title", "sku", "vendor", "price", "product_url", "image_url"]
    with open(OUT_STRICT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(strict_records)

    with open(OUT_STRICT_JSON, "w", encoding="utf-8") as f:
        json.dump(strict_records, f, indent=2)

    with open(OUT_STRICT_TXT, "w", encoding="utf-8") as f:
        f.write("PART_NUMBER\tAVAILABLE_STORES\tSTORE_COUNT\n")
        for part in sorted(part_to_stores.keys()):
            stores_str = ", ".join(sorted(part_to_stores[part]))
            f.write(f"{part}\t{stores_str}\t{len(part_to_stores[part])}\n")

    print("\n=== FAST STRICT VERIFICATION RESULTS ===")
    print(f"Total True Dorman/Help! Product Listings: {len(strict_records):,}")
    print(f"Total Unique Genuine Matched Part Numbers: {len(part_to_stores):,}")
    print(f"Verified CSV Output:  {OUT_STRICT_CSV}")
    print(f"Verified JSON Output: {OUT_STRICT_JSON}")
    print(f"Verified Parts TXT:   {OUT_STRICT_TXT}")

if __name__ == "__main__":
    run_fast_strict_filter()
