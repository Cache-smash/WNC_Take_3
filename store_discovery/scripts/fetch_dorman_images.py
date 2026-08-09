import urllib.request
import re

urls = {
    '03101': 'https://www.dormanproducts.com/p-3101-03101.aspx',
    '03104': 'https://www.dormanproducts.com/p-3104-03104.aspx',
    '03126': 'https://www.dormanproducts.com/p-3126-03126.aspx'
}

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

for part, url in urls.items():
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            # Look for static images or dorman images
            imgs = [img for img in re.findall(r'https?://[^\s"\'\>]+\.jpg', html) if 'dorman' in img.lower() or 'images' in img.lower() or 'product' in img.lower()]
            print(f"=== PART {part} ===")
            for img in list(set(imgs))[:3]:
                print("  ", img)
    except Exception as e:
        print(f"Error for {part}: {e}")
