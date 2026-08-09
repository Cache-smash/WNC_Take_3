import glob
import json
import csv
import sqlite3
import os

OUT_ALL_BRANDS_CSV = "store_discovery/VERIFIED_DORMAN_GROTE_DIETZ_INVENTORY.csv"
OUT_ALL_BRANDS_TXT = "store_discovery/VERIFIED_DORMAN_GROTE_DIETZ_PARTS.txt"

def extract_all_three_brands():
    db_files = glob.glob("store_discovery/*.db")
    print(f"=== EXTRACTING DORMAN, GROTE & DIETZ PARTS ACROSS {len(db_files)} DATABASES ===")

    records = []
    part_summary = {}

    for db_path in db_files:
        domain_name = os.path.basename(db_path).replace(".db", "").replace("_com", ".com").replace("_parts", "-parts")
        print(f"Extracting from: {db_path} ({domain_name})...")

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Query products where Vendor or Title is Dorman, Help, Grote, OR Dietz
        query = """
        SELECT id, title, vendor, product_type, handle, sku, barcode, price, body_html, images_json
        FROM shopify_products
        WHERE UPPER(vendor) LIKE '%DORMAN%' 
           OR UPPER(vendor) LIKE '%HELP%'
           OR UPPER(vendor) LIKE '%GROTE%'
           OR UPPER(vendor) LIKE '%DIETZ%'
           OR UPPER(title) LIKE '%DORMAN%'
           OR UPPER(title) LIKE '%HELP!%'
           OR UPPER(title) LIKE '%GROTE%'
           OR UPPER(title) LIKE '%DIETZ%'
        """
        rows = cursor.execute(query).fetchall()

        for r in rows:
            p_id, title, vendor, p_type, handle, sku, barcode, price, body_html, images_json = r
            title_str = str(title or "").strip()
            vendor_str = str(vendor or "").strip()
            sku_str = str(sku or "").strip()
            handle_str = str(handle or "").strip()

            # Determine brand category
            brand_cat = []
            title_u = title_str.upper()
            vendor_u = vendor_str.upper()

            if "DORMAN" in vendor_u or "HELP" in vendor_u or "DORMAN" in title_u or "HELP!" in title_u:
                brand_cat.append("Dorman")
            if "GROTE" in vendor_u or "GROTE" in title_u:
                brand_cat.append("Grote")
            if "DIETZ" in vendor_u or "DIETZ" in title_u:
                brand_cat.append("Dietz")

            # Extract standalone part numbers (SKU or handle)
            part_number = sku_str if sku_str else handle_str

            # Parse images
            try:
                imgs = json.loads(images_json)
                img_url = imgs[0] if imgs and len(imgs) > 0 else ""
            except Exception:
                img_url = ""

            record = {
                "source_store": domain_name,
                "brand": "/".join(brand_cat),
                "database_id": p_id,
                "part_number_sku": part_number,
                "product_title": title_str,
                "vendor": vendor_str,
                "price": price,
                "product_url": f"https://{domain_name}/products/{handle_str}",
                "image_url": img_url
            }

            records.append(record)

            if part_number not in part_summary:
                part_summary[part_number] = {
                    "brand": "/".join(brand_cat),
                    "title": title_str,
                    "stores": set()
                }
            part_summary[part_number]["stores"].add(domain_name)

        conn.close()

    # Write CSV
    fieldnames = ["source_store", "brand", "database_id", "part_number_sku", "product_title", "vendor", "price", "product_url", "image_url"]
    with open(OUT_ALL_BRANDS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    # Write TXT Summary List
    with open(OUT_ALL_BRANDS_TXT, "w", encoding="utf-8") as f:
        f.write("PART_NUMBER_OR_SKU\tBRAND\tSTORES_AVAILABLE\tPRODUCT_TITLE\n")
        for part, info in sorted(part_summary.items()):
            stores_str = ", ".join(sorted(info["stores"]))
            f.write(f"{part}\t{info['brand']}\t{stores_str}\t{info['title']}\n")

    print("\n=== TRIPLE BRAND (DORMAN, GROTE & DIETZ) EXTRACTION COMPLETE ===")
    print(f"Total Dorman, Grote & Dietz Listings Found: {len(records):,}")
    print(f"Total Unique SKUs/Part Numbers Found:      {len(part_summary):,}")
    print(f"CSV File: {OUT_ALL_BRANDS_CSV}")
    print(f"TXT File: {OUT_ALL_BRANDS_TXT}")

if __name__ == "__main__":
    extract_all_three_brands()
