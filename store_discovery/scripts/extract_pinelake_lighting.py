import sqlite3
import csv
import json

DB_PATH = "store_discovery/pinelakeparts_com.db"
OUT_CSV = "store_discovery/PINELAKEPARTS_GROTE_AND_DIETZ_LIGHTING.csv"
OUT_TXT = "store_discovery/PINELAKEPARTS_GROTE_AND_DIETZ_LIGHTING.txt"

def extract_pinelake_grote_dietz():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = """
    SELECT id, title, vendor, product_type, handle, sku, barcode, price, body_html, images_json
    FROM shopify_products
    WHERE UPPER(vendor) LIKE '%GROTE%' 
       OR UPPER(vendor) LIKE '%DIETZ%'
       OR UPPER(title) LIKE '%GROTE%'
       OR UPPER(title) LIKE '%DIETZ%'
    """
    rows = cursor.execute(query).fetchall()

    records = []
    print(f"=== PINELAKEPARTS.COM GROTE & DIETZ LIGHTING LIST ({len(rows)} items) ===")

    for r in rows:
        p_id, title, vendor, p_type, handle, sku, barcode, price, body_html, images_json = r
        title_str = str(title or "").strip()
        vendor_str = str(vendor or "").strip()
        sku_str = str(sku or "").strip()
        handle_str = str(handle or "").strip()

        brand = []
        if "GROTE" in vendor_str.upper() or "GROTE" in title_str.upper():
            brand.append("Grote")
        if "DIETZ" in vendor_str.upper() or "DIETZ" in title_str.upper():
            brand.append("Dietz")

        try:
            imgs = json.loads(images_json)
            img_url = imgs[0] if imgs and len(imgs) > 0 else ""
        except Exception:
            img_url = ""

        records.append({
            "brand": "/".join(brand),
            "product_title": title_str,
            "sku": sku_str if sku_str else handle_str,
            "vendor": vendor_str,
            "price": f"${price:.2f}" if price else "$0.00",
            "product_url": f"https://pinelakeparts.com/products/{handle_str}",
            "image_url": img_url
        })

    conn.close()

    # Write CSV
    fieldnames = ["brand", "product_title", "sku", "vendor", "price", "product_url", "image_url"]
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    # Write clean TXT list
    with open(OUT_TXT, "w", encoding="utf-8") as f:
        f.write("BRAND\tPRODUCT_TITLE\tSKU_OR_HANDLE\tPRICE\tPRODUCT_URL\tIMAGE_URL\n")
        for rec in records:
            f.write(f"{rec['brand']}\t{rec['product_title']}\t{rec['sku']}\t{rec['price']}\t{rec['product_url']}\t{rec['image_url']}\n")

    print(f"CSV saved to: {OUT_CSV}")
    print(f"TXT saved to: {OUT_TXT}")

if __name__ == "__main__":
    extract_pinelake_grote_dietz()
