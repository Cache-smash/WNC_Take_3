import csv
from pathlib import Path

REF_HEADERS = [
    "Action(SiteID=eBayMotors|Country=US|Currency=USD|Version=1193|CC=UTF-8)",
    "ItemID",
    "PicURL"
]

rows = [
    {
        "Action(SiteID=eBayMotors|Country=US|Currency=USD|Version=1193|CC=UTF-8)": "Revise",
        "ItemID": "318668407022",
        "PicURL": "https://cdn.shopify.com/s/files/1/0645/2074/9130/files/47303-007.jpg|https://cdn.shopify.com/s/files/1/0645/2074/9130/files/47303-003.jpg"
    }
]

out_path = Path(r'C:\Users\kbcha\Documents\Coding_Projects_002\WNC_Take_3\store_discovery\eBay_Bulk_Revise_Help_47011_Koskowski_Images.csv')

with open(out_path, 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=REF_HEADERS)
    writer.writeheader()
    writer.writerows(rows)

print("Created clean Koskowski image revision CSV: eBay_Bulk_Revise_Help_47011_Koskowski_Images.csv")
