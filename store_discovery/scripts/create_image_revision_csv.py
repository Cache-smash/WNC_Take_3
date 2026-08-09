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
        "ItemID": "318667769283",
        "PicURL": "https://static.dormanproducts.com/images/product/large/03101-001.jpg|https://static.dormanproducts.com/images/product/large/03101-003.jpg"
    },
    {
        "Action(SiteID=eBayMotors|Country=US|Currency=USD|Version=1193|CC=UTF-8)": "Revise",
        "ItemID": "318667769273",
        "PicURL": "https://static.dormanproducts.com/images/product/large/03104-001.jpg|https://static.dormanproducts.com/images/product/large/03104-003.jpg"
    },
    {
        "Action(SiteID=eBayMotors|Country=US|Currency=USD|Version=1193|CC=UTF-8)": "Revise",
        "ItemID": "318667769278",
        "PicURL": "https://static.dormanproducts.com/images/product/large/03126-001.jpg|https://static.dormanproducts.com/images/product/large/03126-003.jpg"
    }
]

out_path = Path(r'C:\Users\kbcha\Documents\Coding_Projects_002\WNC_Take_3\store_discovery\eBay_Bulk_Revise_Help_Cat_33634_Images.csv')

with open(out_path, 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=REF_HEADERS)
    writer.writeheader()
    writer.writerows(rows)

print("Created clean image revision CSV: eBay_Bulk_Revise_Help_Cat_33634_Images.csv")
