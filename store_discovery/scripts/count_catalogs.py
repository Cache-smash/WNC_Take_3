import json
import urllib.request
import urllib.parse
import ssl
import re

with open("store_discovery/verified_shopify_stores.json", "r") as f:
    stores = json.load(f)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def get_exact_catalog_size(domain: str) -> str:
    """
    Checks the store sitemap index to get exact product counts instantly without looping heavy pages.
    """
    url = f"https://{domain}/sitemap.xml"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
            if resp.status == 200:
                xml_text = resp.read().decode('utf-8', errors='ignore')
                # Find all product sitemaps
                sitemaps = re.findall(r'<loc>(https://[^<]+/sitemap_products_\d+\.xml)</loc>', xml_text)
                if sitemaps:
                    total_urls = 0
                    for sm_url in sitemaps:
                        req_sm = urllib.request.Request(sm_url, headers={"User-Agent": "Mozilla/5.0"})
                        with urllib.request.urlopen(req_sm, context=ctx, timeout=5) as r_sm:
                            sm_text = r_sm.read().decode('utf-8', errors='ignore')
                            total_urls += sm_text.count('<url>')
                    return f"{total_urls:,} items"
    except Exception as e:
        pass
        
    # Quick probe limit check
    url_p = f"https://{domain}/products.json?limit=250"
    req_p = urllib.request.Request(url_p, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req_p, context=ctx, timeout=5) as resp_p:
            if resp_p.status == 200:
                data = json.loads(resp_p.read().decode('utf-8'))
                count = len(data.get("products", []))
                if count < 250:
                    return f"{count} items"
                else:
                    return "250+ items (Large Catalog)"
    except Exception:
        pass
        
    return "Unknown"

print("=== Store Catalog Size Results ===")
for s in stores:
    dom = s["domain"]
    size_str = get_exact_catalog_size(dom)
    s["catalog_size"] = size_str
    print(f"Store: {dom:<25} | Size: {size_str}")

with open("store_discovery/verified_shopify_stores.json", "w") as f:
    json.dump(stores, f, indent=2)
