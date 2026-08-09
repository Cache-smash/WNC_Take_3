import glob
import json
import csv
import sqlite3
import os

OUT_MASTER_CSV = "store_discovery/MASTER_MATCHED_INVENTORY.csv"
OUT_MASTER_JSON = "store_discovery/MASTER_MATCHED_INVENTORY.json"
OUT_MASTER_TXT = "store_discovery/MASTER_MATCHED_PART_NUMBERS.txt"

def build_master_lists():
    csv_files = [f for f in glob.glob("store_discovery/*_matched_inventory.csv") if "MASTER" not in f]
    txt_files = [f for f in glob.glob("store_discovery/*_matched_parts_list.txt") if "MASTER" not in f]

    print(f"=== Merging {len(csv_files)} Store Inventory CSVs into Master List ===")

    all_matched_records = []
    part_to_stores = {}

    for csv_file in csv_files:
        print(f"Reading: {csv_file}")
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                all_matched_records.append(row)
                
                # Extract parts & store domain
                domain = row.get("source_store", "partcatalog.com")
                matched_parts_raw = row.get("matched_part_numbers", "")
                
                for p_entry in matched_parts_raw.split(", "):
                    clean_part = p_entry.split()[0].strip()
                    if clean_part:
                        if clean_part not in part_to_stores:
                            part_to_stores[clean_part] = set()
                        part_to_stores[clean_part].add(domain)

    # 1. Write Master CSV
    fieldnames = ["source_store", "database_id", "matched_part_numbers", "product_title", "sku", "vendor", "price", "product_url", "image_url"]
    with open(OUT_MASTER_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_matched_records)

    # 2. Write Master JSON
    with open(OUT_MASTER_JSON, "w", encoding="utf-8") as f:
        json.dump(all_matched_records, f, indent=2)

    # 3. Write Master Part Numbers TXT (Part Number <TAB> Available Store Domains)
    with open(OUT_MASTER_TXT, "w", encoding="utf-8") as f:
        f.write("PART_NUMBER\tAVAILABLE_STORES\tSTORE_COUNT\n")
        for part in sorted(part_to_stores.keys()):
            stores_str = ", ".join(sorted(part_to_stores[part]))
            count = len(part_to_stores[part])
            f.write(f"{part}\t{stores_str}\t{count}\n")

    print("\n=== MASTER MERGE COMPLETE ===")
    print(f"Total Matched Product Listings Across All Stores: {len(all_matched_records):,}")
    print(f"Total Unique Target Part Numbers Found:         {len(part_to_stores):,}")
    print(f"Master Inventory CSV:      {OUT_MASTER_CSV}")
    print(f"Master Inventory JSON:     {OUT_MASTER_JSON}")
    print(f"Master Part Numbers List:  {OUT_MASTER_TXT}")

if __name__ == "__main__":
    build_master_lists()
