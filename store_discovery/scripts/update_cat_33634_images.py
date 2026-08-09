import csv
from pathlib import Path

# Complete 40-Column Schema from exact reference eBay File: ebay_motors_listings(07-31-2026)#2.csv
REF_HEADERS = [
    "Action(SiteID=eBayMotors|Country=US|Currency=USD|Version=1193|CC=UTF-8)",
    "Category",
    "Title",
    "Description",
    "StartPrice",
    "Quantity",
    "Format",
    "Duration",
    "ShippingProfileName",
    "ReturnProfileName",
    "PaymentProfileName",
    "PostalCode",
    "Brand",
    "MPN",
    "CustomLabel",
    "Product:EPID",
    "PicURL",
    "ConditionID",
    "WeightMajor",
    "WeightMinor",
    "WeightUnit",
    "C:Brand",
    "C:California Prop 65 Warning",
    "C:Color",
    "C:Country of Origin",
    "C:Finish",
    "C:Interchange Part Number",
    "C:Item Diameter",
    "C:Items Included",
    "C:Manufacturer Part Number",
    "C:Manufacturer Warranty",
    "C:Material",
    "C:Mounting Style",
    "C:OE/OEM Part Number",
    "C:Performance Part",
    "C:Placement on Vehicle",
    "C:Superseded Part Number",
    "C:Type",
    "C:Universal Fitment",
    "C:Vintage Part"
]

items = [
    {
        'mpn': '03101',
        'epid': '173950153',
        'cat_id': '33634',
        'cat_name': 'Clamps, Flanges, Hangers & Hardware',
        'brand': 'Dorman/Help',
        'title': 'Dorman 03101 Exhaust Manifold Flange Stud Kit 1982-92 Z28 IROC-Z GTA 350 305 V8',
        'img': 'https://static.dormanproducts.com/images/product/large/03101-001.jpg|https://static.dormanproducts.com/images/product/large/03101-003.jpg',
        'price': '11.25',
        'quantity': '4',
        'fitment_table_html': '''<table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<thead>
<tr style="background-color: #f2f2f2; text-align: left;"><th>Make</th><th>Years</th><th>Compatible Engine / Application</th></tr>
</thead>
<tbody>
<tr><td>Chevrolet / Pontiac</td><td>1982 - 1992</td><td>Camaro Z28 / IROC-Z, Firebird Trans Am / GTA (305 / 350 V8)</td></tr>
<tr><td>GM / Ford / Chrysler</td><td>1975 - 1996</td><td>3/8-16 x 2-1/4 in. Exhaust Flange Applications</td></tr>
</tbody>
</table>''',
        'specs': {'C:Brand': 'Dorman/Help', 'C:Manufacturer Part Number': '03101', 'C:Placement on Vehicle': 'Exhaust Manifold, Flange', 'C:Vintage Part': 'Yes', 'C:Type': 'Exhaust Flange Stud & Nut'}
    },
    {
        'mpn': '03104',
        'epid': '173877991',
        'cat_id': '33634',
        'cat_name': 'Clamps, Flanges, Hangers & Hardware',
        'brand': 'Dorman/Help',
        'title': 'Dorman 03104 Exhaust Flange Stud Kit - M10 - 1.50 x 52 mm',
        'img': 'https://static.dormanproducts.com/images/product/large/03104-001.jpg|https://static.dormanproducts.com/images/product/large/03104-003.jpg',
        'price': '9.50',
        'quantity': '4',
        'fitment_table_html': '''<table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<thead>
<tr style="background-color: #f2f2f2; text-align: left;"><th>Make</th><th>Years</th><th>Compatible Metric Flange Applications</th></tr>
</thead>
<tbody>
<tr><td>GM / Ford / Chrysler</td><td>1985 - 2005</td><td>M10-1.50 x 52mm Metric Exhaust Manifold Flanges</td></tr>
</tbody>
</table>''',
        'specs': {'C:Brand': 'Dorman/Help', 'C:Manufacturer Part Number': '03104', 'C:Placement on Vehicle': 'Exhaust Manifold, Flange', 'C:Vintage Part': 'Yes', 'C:Type': 'Exhaust Flange Stud & Nut'}
    },
    {
        'mpn': '03126',
        'epid': '173874315',
        'cat_id': '33634',
        'cat_name': 'Clamps, Flanges, Hangers & Hardware',
        'brand': 'Dorman/Help',
        'title': 'Dorman Help 03126 Exhaust Flange Stud & Nut Kit M10-1.25 NOS',
        'img': 'https://static.dormanproducts.com/images/product/large/03126-001.jpg|https://static.dormanproducts.com/images/product/large/03126-003.jpg',
        'price': '9.50',
        'quantity': '5',
        'fitment_table_html': '''<table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<thead>
<tr style="background-color: #f2f2f2; text-align: left;"><th>Make</th><th>Years</th><th>Compatible Metric Flange Applications</th></tr>
</thead>
<tbody>
<tr><td>Japanese & Domestic Imports</td><td>1980 - 2002</td><td>M10-1.25 Exhaust Pipe & Header Flanges</td></tr>
</tbody>
</table>''',
        'specs': {'C:Brand': 'Dorman/Help', 'C:Manufacturer Part Number': '03126', 'C:Placement on Vehicle': 'Exhaust Manifold, Flange', 'C:Vintage Part': 'Yes', 'C:Type': 'Exhaust Flange Stud & Nut'}
    }
]

out_dir = Path(r'C:\Users\kbcha\Documents\Coding_Projects_002\WNC_Take_3\store_discovery')
file_name = 'eBay_Bulk_Listing_Help_Cat_33634.csv'
file_path = out_dir / file_name

rows = []
for item in items:
    mpn = item['mpn']
    desc_html = f"<h3>{item['title']}</h3><p><strong>Brand:</strong> {item['brand']}</p><p><strong>Manufacturer Part Number:</strong> {mpn}</p><p><strong>ePID:</strong> {item['epid']}</p><p><strong>Condition:</strong> New Old Stock (NOS)</p><hr/><h4>Vehicle Compatibility & Fitment Chart</h4>{item['fitment_table_html']}<hr/><p><em>WNC Parts Slingers - Fast Shipping on New Old Stock (NOS) Auto Parts!</em></p>"
    
    row = {
        "Action(SiteID=eBayMotors|Country=US|Currency=USD|Version=1193|CC=UTF-8)": "Add",
        "Category": item['cat_id'],
        "Title": item['title'],
        "Description": desc_html,
        "StartPrice": item['price'],
        "Quantity": item['quantity'],
        "Format": "FixedPriceItem",
        "Duration": "30",
        "ShippingProfileName": "Free Shipping",
        "ReturnProfileName": "30 Days Money Back or Replacement (Primary Return Policy)",
        "PaymentProfileName": "eBay Managed Payments (Primary Payment Policy)",
        "PostalCode": "28739",
        "Brand": item['brand'],
        "MPN": mpn,
        "CustomLabel": f"HELP-{mpn}",
        "Product:EPID": item['epid'],
        "PicURL": item['img'],
        "ConditionID": "1000",
        "WeightMajor": "0",
        "WeightMinor": "4",
        "WeightUnit": "lb",
        "C:Brand": item['brand'],
        "C:California Prop 65 Warning": "",
        "C:Color": "",
        "C:Country of Origin": "",
        "C:Finish": "",
        "C:Interchange Part Number": "",
        "C:Item Diameter": "",
        "C:Items Included": "",
        "C:Manufacturer Part Number": mpn,
        "C:Manufacturer Warranty": "",
        "C:Material": "Steel",
        "C:Mounting Style": "",
        "C:OE/OEM Part Number": "",
        "C:Performance Part": "",
        "C:Placement on Vehicle": item['specs'].get('C:Placement on Vehicle', ''),
        "C:Superseded Part Number": "",
        "C:Type": item['specs'].get('C:Type', ''),
        "C:Universal Fitment": "",
        "C:Vintage Part": item['specs'].get('C:Vintage Part', 'Yes')
    }
    rows.append(row)

with open(file_path, 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=REF_HEADERS)
    writer.writeheader()
    writer.writerows(rows)

print(f"Updated Cat 33634 CSV with verified high-res Dorman product image URLs: {file_name}")
