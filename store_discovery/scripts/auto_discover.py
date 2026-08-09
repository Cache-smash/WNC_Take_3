import json
import re
import urllib.request
import urllib.parse
import urllib.error
import ssl
from typing import List, Dict, Set

# Brands to search for in catalogs
TARGET_BRANDS = ["DORMAN", "HELP!", "TRW", "GROTE", "DIETZ", "PERFECT PARTS"]

# Sample Dorman Help 5-digit part numbers
SAMPLE_PARTS = ["41001", "03107", "03130", "42060", "85620"]

# Known candidate domains collected from web discovery
SEED_CANDIDATE_DOMAINS = [
    "partcatalog.com",
    "koskowskiautoparts.com",
    "hotcarparts.com",
    "fleetpro-parts.com",
    "1factoryradio.com",
    "rvpartshop.com",
    "sstubes.com",
    "youngfartsrvparts.com"
]

def search_duckduckgo(query: str, max_results: int = 15) -> List[str]:
    """
    Performs a HTML scrape of DuckDuckGo search results for dorking without requiring API keys.
    Extracts external domain names.
    """
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    )
    
    domains: Set[str] = set()
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            html = resp.read().decode('utf-8')
            # Extract links from DDG html results
            links = re.findall(r'class="result__url"\s+href="([^"]+)"', html)
            for link in links:
                # Clean URL
                if "uddg=" in link:
                    actual_url = urllib.parse.unquote(link.split("uddg=")[-1].split("&")[0])
                else:
                    actual_url = link
                
                parsed = urllib.parse.urlparse(actual_url)
                netloc = parsed.netloc.lower()
                
                # Filter out search engines, major marketplaces, and social media
                ignored_domains = [
                    "ebay.com", "amazon.com", "walmart.com", "rockauto.com", 
                    "youtube.com", "facebook.com", "pinterest.com", "duckduckgo.com",
                    "google.com", "oreillyauto.com", "autozone.com", "advanceautoparts.com"
                ]
                
                if netloc and not any(ig in netloc for ig in ignored_domains):
                    domains.add(netloc)
    except Exception as e:
        print(f"Error executing dork '{query}': {e}")

    return list(domains)

from stealth_config import get_stealth_headers, human_delay

def inspect_domain(domain: str) -> Dict:
    """
    Inspects a domain to see if it's Shopify and holds target brand data using stealth header profiles.
    """
    result = {
        "domain": domain,
        "is_shopify": False,
        "products_json_open": False,
        "matched_brands": [],
        "matched_parts": [],
        "sample_count": 0
    }
    
    url = f"https://{domain}/products.json?limit=250"
    
    # Humanized pacing delay
    human_delay(1.5, 3.0)

    req = urllib.request.Request(
        url,
        headers=get_stealth_headers()
    )
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
            if resp.status == 200:
                result["is_shopify"] = True
                result["products_json_open"] = True
                data = json.loads(resp.read().decode('utf-8'))
                products = data.get("products", [])
                result["sample_count"] = len(products)

                full_text = ""
                for p in products:
                    title = p.get("title", "")
                    vendor = p.get("vendor", "")
                    body = p.get("body_html", "") or ""
                    full_text += f" {title} {vendor} {body}".upper()

                for b in TARGET_BRANDS:
                    if b in full_text:
                        result["matched_brands"].append(b)

                for part in SAMPLE_PARTS:
                    if part in full_text:
                        result["matched_parts"].append(part)

    except Exception:
        pass

    return result

if __name__ == "__main__":
    candidate_domains = set(SEED_CANDIDATE_DOMAINS)
    print(f"Loaded {len(candidate_domains)} seed domains for verification...")

    print(f"\nTotal Unique Candidate Domains to Verify: {len(candidate_domains)}")
    
    print("\n=== STAGE 2: Verifying Shopify API Accessibility & Parts Inventory ===")
    verified_stores = []
    for dom in candidate_domains:
        res = inspect_domain(dom)
        if res["is_shopify"]:
            print(f"  [MATCH FOUND] Domain: {dom} | Open API: {res['products_json_open']} | Brands: {res['matched_brands']} | Sample Parts: {res['matched_parts']}")
            verified_stores.append(res)
        else:
            print(f"  [SKIP] Domain: {dom} (Not open Shopify store)")

    # Save to JSON in store_discovery directory
    out_file = "store_discovery/verified_shopify_stores.json"
    with open(out_file, "w") as f:
        json.dump(verified_stores, f, indent=2)
    
    print(f"\nSaved {len(verified_stores)} verified Shopify store(s) to {out_file}")
