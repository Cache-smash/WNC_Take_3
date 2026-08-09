import json
import urllib.request
import urllib.error
import ssl
from typing import List, Dict

# Sample seed domains to validate Shopify products.json access & Dorman presence
DOMAINS_TO_CHECK = [
    "partcatalog.com",
    # Add more target domains here as we gather them from dorking/search
]

# Sample Dorman Help 5-digit part numbers to cross-check
TARGET_PART_NUMBERS = ["41001", "13870", "03130", "85620", "42001", "03107", "42060"]

from stealth_config import get_stealth_headers, human_delay

def check_shopify_store(domain: str) -> Dict:
    """
    Checks if a given domain is a Shopify store and exposes /products.json.
    Inspects products for Dorman or target part numbers with stealth headers.
    """
    url = f"https://{domain}/products.json?limit=250"
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    # Human delay before request
    human_delay(1.0, 2.5)

    req = urllib.request.Request(
        url,
        headers=get_stealth_headers()
    )

    result = {
        "domain": domain,
        "is_shopify": False,
        "has_products_json": False,
        "dorman_found": False,
        "matched_parts": [],
        "total_sample_products": 0
    }

    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
            if response.status == 200:
                result["is_shopify"] = True
                result["has_products_json"] = True
                data = json.loads(response.read().decode("utf-8"))
                products = data.get("products", [])
                result["total_sample_products"] = len(products)

                for prod in products:
                    title = prod.get("title", "").upper()
                    vendor = prod.get("vendor", "").upper()
                    body = prod.get("body_html", "") or ""
                    text_blob = f"{title} {vendor} {body}".upper()

                    if "DORMAN" in text_blob or "HELP!" in text_blob:
                        result["dorman_found"] = True

                    for pnum in TARGET_PART_NUMBERS:
                        if pnum in text_blob and pnum not in result["matched_parts"]:
                            result["matched_parts"].append(pnum)

    except urllib.error.HTTPError as e:
        result["error"] = f"HTTP Error {e.code}"
    except urllib.error.URLError as e:
        result["error"] = f"URL Error {e.reason}"
    except Exception as e:
        result["error"] = str(e)

    return result

if __name__ == "__main__":
    print("Testing Store Discovery Tool...")
    for domain in DOMAINS_TO_CHECK:
        res = check_shopify_store(domain)
        print(json.dumps(res, indent=2))
