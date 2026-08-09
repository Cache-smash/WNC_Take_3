import urllib.request
import json
import time
import re
import csv
from pathlib import Path

# Load target 5-digit Dorman Help list
HELP_5_FILE = Path(r"C:\Users\kbcha\Documents\Coding_Projects_002\WNC_Take_3\store_discovery\dorman_help_5digit_part_numbers.txt")
OUT_CSV = Path(r"C:\Users\kbcha\Documents\Coding_Projects_002\WNC_Take_3\store_discovery\KOSKOWSKI_DORMAN_HELP_FULL_SWEEP_INVENTORY.csv")

def load_help_targets():
    targets = set()
    if HELP_5_FILE.exists():
        with open(HELP_5_FILE, "r", encoding="utf-8") as f:
            for line in f:
                c = line.strip()
                if c:
                    targets.add(c)
    print(f"Loaded {len(targets):,} target 5-digit Dorman Help part numbers.")
    return targets

def sweep_koskowski_store():
    help_targets = load_help_targets()
    page = 1
    total_scraped = 0
    matched_records = []
    unique_parts_found = set()

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    while True:
        url = f"https://www.koskowskiautoparts.com/products.json?limit=250&page={page}"
        print(f"Fetching Page {page}... ({url})")
        
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                products = data.get('products', [])
                
                if not products:
                    print(f"No more products found. Reached end of catalog at page {page-1}.")
                    break

                total_scraped += len(products)

                for prod in products:
                    title = prod.get('title', '')
                    vendor = prod.get('vendor', '')
                    handle = prod.get('handle', '')
                    images = prod.get('images', [])
                    img_url = images[0].get('src', '') if images else ''
                    
                    for var in prod.get('variants', []):
                        sku = str(var.get('sku', '') or '')
                        price = var.get('price', '')

                        # Check SKU, Title, and Handle for 5-digit patterns & 591| prefixes
                        combined_text = f" {title} {sku} {handle} ".replace("-", " ").replace("/", " ").replace("_", " ").upper()
                        
                        matched_in_item = []

                        # Match 1: 591| SKU prefix format (Koskowski Dorman SKU format: 591|XXXXX)
                        sku_match = re.search(r'591\|(\d{5})', sku)
                        if sku_match:
                            matched_in_item.append(sku_match.group(1))

                        # Match 2: Standalone 5-digit numbers matched against Help! master index
                        for num in re.findall(r'\b\d{5}\b', combined_text):
                            if num in help_targets or sku_match:
                                matched_in_item.append(num)

                        if matched_in_item:
                            clean_matches = sorted(list(set(matched_in_item)))
                            for m in clean_matches:
                                unique_parts_found.add(m)

                            matched_records.append({
                                "source_store": "koskowskiautoparts.com",
                                "database_id": prod.get('id'),
                                "help_5digit_part_numbers": ", ".join(clean_matches),
                                "product_title": title,
                                "sku": sku,
                                "vendor": vendor,
                                "price": price,
                                "product_url": f"https://www.koskowskiautoparts.com/products/{handle}",
                                "image_url": img_url
                            })

                page += 1
                time.sleep(0.2)  # Respectful rate limit

        except Exception as e:
            print(f"Stopped or error on page {page}: {e}")
            break

    print(f"\n=======================================================")
    print(f"       KOSKOWSKI AUTO PARTS FULL STORE SWEEP COMPLETE")
    print(f"=======================================================")
    print(f"Total Koskowski Products Scraped: {total_scraped:,}")
    print(f"Matched Dorman / 5-Digit Listings: {len(matched_records):,}")
    print(f"Unique 5-Digit Dorman Numbers Found: {len(unique_parts_found):,}")

    # Write CSV
    if matched_records:
        fieldnames = ["source_store", "database_id", "help_5digit_part_numbers", "product_title", "sku", "vendor", "price", "product_url", "image_url"]
        with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(matched_records)
        print(f"Saved full inventory results to: {OUT_CSV}")

if __name__ == "__main__":
    sweep_koskowski_store()
