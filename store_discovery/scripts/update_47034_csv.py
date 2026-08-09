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
        'mpn': '47034',
        'epid': '192323719',
        'cat_id': '46097',
        'cat_name': 'Other Exhaust & Emission Parts',
        'item_name': 'Engine Crankcase Vent Hose PCV Elbow',
        'brand': 'Dorman/Help',
        'title': 'Dorman Help 47034 PCV Elbow Crankcase Vent Hose GM Ford NOS',
        'img': 'https://cdn.shopify.com/s/files/1/0645/2074/9130/files/47034-007.jpg?v=1748812835',
        'price': '11.95',
        'fitment_table_html': '''<table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<thead>
<tr style="background-color: #f2f2f2; text-align: left;">
<th>Make</th>
<th>Years</th>
<th>Popular Compatible Models</th>
</tr>
</thead>
<tbody>
<tr><td>Buick</td><td>1976 - 1988</td><td>Century, Electra, LeSabre, Regal, Riviera, Skylark, Estate Wagon</td></tr>
<tr><td>Cadillac</td><td>1978 - 1990</td><td>DeVille, Eldorado, Fleetwood, Brougham, Seville</td></tr>
<tr><td>Chevrolet</td><td>1979 - 1990</td><td>Chevette, Monte Carlo, Suburban K10, G30/3500 Van</td></tr>
<tr><td>GMC</td><td>1978 - 1984</td><td>C1500, K1500, Jimmy, Suburban, G2500/G3500 Vans</td></tr>
<tr><td>Oldsmobile</td><td>1976 - 1990</td><td>Cutlass, Cutlass Supreme, Delta 88, Custom Cruiser, Toronado, Omega</td></tr>
<tr><td>Pontiac</td><td>1976 - 1989</td><td>Bonneville, Catalina, Firebird, Grand Am, Grand Prix, LeMans, Ventura</td></tr>
</tbody>
</table>''',
        'specs': {'C:Brand': 'Dorman/Help', 'C:Manufacturer Part Number': '47034', 'C:Placement on Vehicle': 'Engine Compartment, Valve Cover', 'C:Vintage Part': 'Yes', 'C:Type': 'PCV Elbow', 'C:OE/OEM Part Number': '25526950'}
    }
]

out_dir = Path(r'C:\Users\kbcha\Documents\Coding_Projects_002\WNC_Take_3\store_discovery')

for item in items:
    cat_id = item['cat_id']
    file_name = f'eBay_Bulk_Listing_Help_Cat_{cat_id}.csv'
    file_path = out_dir / file_name
    
    mpn = item['mpn']
    desc_html = f"<h3>{item['title']}</h3><p><strong>Brand:</strong> {item['brand']}</p><p><strong>Manufacturer Part Number:</strong> {mpn}</p><p><strong>OE/OEM Cross Reference:</strong> {item['specs']['C:OE/OEM Part Number']}</p><p><strong>ePID:</strong> {item['epid']}</p><p><strong>Condition:</strong> New Old Stock (NOS)</p><hr/><h4>Vehicle Compatibility & Fitment Chart</h4>{item['fitment_table_html']}<hr/><p><em>WNC Parts Slingers - Fast Shipping on New Old Stock (NOS) Auto Parts!</em></p>"
    
    row = {
        "Action(SiteID=eBayMotors|Country=US|Currency=USD|Version=1193|CC=UTF-8)": "Add",
        "Category": item['cat_id'],
        "Title": item['title'],
        "Description": desc_html,
        "StartPrice": item['price'],
        "Quantity": "1",
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
        "C:Material": "Rubber",
        "C:Mounting Style": "Push-on",
        "C:OE/OEM Part Number": item['specs']['C:OE/OEM Part Number'],
        "C:Performance Part": "",
        "C:Placement on Vehicle": item['specs'].get('C:Placement on Vehicle', ''),
        "C:Superseded Part Number": "",
        "C:Type": item['specs'].get('C:Type', ''),
        "C:Universal Fitment": "",
        "C:Vintage Part": item['specs'].get('C:Vintage Part', 'Yes')
    }
    
    with open(file_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=REF_HEADERS)
        writer.writeheader()
        writer.writerow(row)
    print(f"Updated eBay Bulk CSV with Full HTML Fitment Table: {file_name}")
