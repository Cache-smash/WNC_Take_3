import csv
import sqlite3
import json
import os
import sys

from dotenv import load_dotenv

load_dotenv(dotenv_path=r"C:\Users\kbcha\Documents\Coding_Projects_002\WNC_Take_3\.env")

sys.path.append(r"C:\Users\kbcha\Documents\Coding_Projects_002\WNC_Take_3")
from app.ebay_taxonomy import get_aspects_for_category

MASTER_TSV = r"C:\Users\kbcha\Documents\Coding_Projects_002\WNC_Take_2\US_Parts_Catalog_Dorman_Help.tsv"
KOSKOWSKI_DB = r"store_discovery\koskowskiautoparts_com.db"
OUTPUT_EBAY_CSV = r"store_discovery\EBAY_BULK_UPLOAD_LISTINGS.csv"

CATEGORY_ASPECTS_CACHE = {}

def load_master_dorman_catalog():
    catalog = {}
    with open(MASTER_TSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            mpn = row.get("ManufacturePartNumber", "").strip()
            if mpn:
                catalog[mpn] = row
    return catalog

def fetch_category_aspects_live(category_id: str) -> list:
    if category_id in CATEGORY_ASPECTS_CACHE:
        return CATEGORY_ASPECTS_CACHE[category_id]

    try:
        aspect_cols = get_aspects_for_category(category_id)
        CATEGORY_ASPECTS_CACHE[category_id] = aspect_cols
        return aspect_cols
    except Exception as e:
        fallback = ["C:Brand", "C:Manufacturer Part Number", "C:Country/Region of Manufacture", "C:Fitment Type"]
        CATEGORY_ASPECTS_CACHE[category_id] = fallback
        return fallback

def generate_ebay_csv(part_numbers: list):
    catalog = load_master_dorman_catalog()
    conn = sqlite3.connect(KOSKOWSKI_DB)
    cursor = conn.cursor()

    ebay_rows = []
    all_aspect_columns = set()

    print(f"\n=== GENERATING FULL EMBEDDED FITMENT & DESCRIPTION EBAY CSV ===")

    for part_no in part_numbers:
        p_clean = str(part_no).strip()
        
        cat_info = catalog.get(p_clean) or catalog.get(p_clean.zfill(5))
        
        query = """
        SELECT id, title, sku, vendor, price, handle, body_html, images_json
        FROM shopify_products
        WHERE (UPPER(vendor) LIKE '%DORMAN%' OR UPPER(vendor) LIKE '%HELP%')
          AND (sku LIKE ? OR title LIKE ? OR handle LIKE ?)
        """
        search_pattern = f"%{p_clean}%"
        db_match = cursor.execute(query, (search_pattern, search_pattern, search_pattern)).fetchone()

        if db_match:
            p_id, db_title, sku, vendor, price, handle, body_html, images_json = db_match
            
            try:
                imgs = json.loads(images_json)
                pic_url = "|".join(imgs) if imgs else ""
            except Exception:
                pic_url = ""

            category_id = cat_info.get("CategoryID", "33696") if cat_info else "33696"
            epid = cat_info.get("ePID", "") if cat_info else ""
            title = cat_info.get("Title", db_title) if cat_info else db_title
            
            if len(title) > 80:
                title = title[:80].rsplit(" ", 1)[0]

            live_aspect_cols = fetch_category_aspects_live(category_id)
            all_aspect_columns.update(live_aspect_cols)

            # INJECT FULL STORE BODY_HTML CONTAINING COMPLETE FITMENT TABLE & SPECIFICATIONS!
            clean_body = body_html.replace("\n", " ").strip() if body_html else ""

            description = f"""
            <div style="font-family: Arial, sans-serif; max-width: 850px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px; color: #333333; line-height: 1.6;">
                <h2 style="color: #004488; text-align: center; border-bottom: 2px solid #004488; padding-bottom: 8px;">New Old Stock (NOS) Dorman / Help! Part</h2>
                <h3 style="color: #222222; text-align: center; margin-top: 5px;">Part Number: {p_clean}</h3>
                
                {clean_body}

                <br><br>
                <div style="background-color: #f9f9f9; padding: 15px; border-radius: 6px; border-left: 4px solid #004488; margin-top: 20px;">
                    <p style="margin: 0; font-size: 14px;"><strong>Shipping Policy:</strong> Fast shipping from North Carolina. All parts are carefully inspected prior to shipment.</p>
                </div>
            </div>
            """

            row_dict = {
                "Action(SiteID=eBayMotors|Country=US|Currency=USD|Version=1193|CC=UTF-8)": "Add",
                "Category": category_id,
                "Title": title,
                "Description": description.replace("\n", " ").strip(),
                "StartPrice": f"{float(price):.2f}" if price else "14.99",
                "Quantity": "5",
                "Format": "FixedPriceItem",
                "Duration": "GTC",
                "ShippingProfileName": "Free Shipping",
                "ReturnProfileName": "30 Days Money Back or Replacement (Primary Return Policy)",
                "PaymentProfileName": "eBay Managed Payments (Primary Payment Policy)",
                "PostalCode": "28739",
                "Brand": "Dorman/Help",
                "MPN": p_clean,
                "CustomLabel": f"{p_clean}-1",
                "Product:EPID": epid,
                "PicURL": pic_url,
                "ConditionID": "1000",
                "WeightMajor": "0",
                "WeightMinor": "4",
                "WeightUnit": "lb"
            }

            for col in live_aspect_cols:
                if col == "C:Brand":
                    row_dict[col] = "Dorman/Help"
                elif col in ["C:Manufacturer Part Number", "C:MPN"]:
                    row_dict[col] = p_clean
                elif col == "C:Fitment Type":
                    row_dict[col] = "Direct Replacement"
                elif col == "C:Country/Region of Manufacture":
                    row_dict[col] = "United States"
                else:
                    row_dict[col] = ""

            ebay_rows.append(row_dict)
        else:
            print(f"  -> Warning: Part number {p_clean} was not found in Koskowski DB.")

    conn.close()

    if ebay_rows:
        base_headers = [
            "Action(SiteID=eBayMotors|Country=US|Currency=USD|Version=1193|CC=UTF-8)",
            "Category", "Title", "Description", "StartPrice", "Quantity", "Format", "Duration",
            "ShippingProfileName", "ReturnProfileName", "PaymentProfileName", "PostalCode",
            "Brand", "MPN", "CustomLabel", "Product:EPID", "PicURL", "ConditionID",
            "WeightMajor", "WeightMinor", "WeightUnit"
        ]
        
        sorted_aspects = sorted(list(all_aspect_columns))
        fieldnames = base_headers + sorted_aspects

        with open(OUTPUT_EBAY_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(ebay_rows)

        print(f"\n=== SUCCESS! Generated Complete Fitment & Description eBay CSV ===")
        print(f"Total Listings Created: {len(ebay_rows)}")
        print(f"Output CSV File:       {OUTPUT_EBAY_CSV}")
    else:
        print("No valid records found to build eBay CSV.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        parts = sys.argv[1:]
        generate_ebay_csv(parts)
    else:
        generate_ebay_csv(["42064", "42065", "42067"])
