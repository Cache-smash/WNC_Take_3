import urllib.request
import re

parts = ['03101', '03104', '03126']
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

for p in parts:
    print(f"=== TESTING PART {p} ===")
    for suffix in ['001', '002', '003', '007']:
        for size in ['large', 'medium', 'icon']:
            url = f"https://static.dormanproducts.com/images/product/{size}/{p}-{suffix}.jpg"
            try:
                req = urllib.request.Request(url, headers=headers, method='HEAD')
                with urllib.request.urlopen(req) as resp:
                    if resp.status == 200:
                        print(f"  FOUND VALID IMAGE: {url}")
            except Exception:
                pass
