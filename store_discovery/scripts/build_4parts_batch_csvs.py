import csv
from pathlib import Path

REF_HEADERS = [
    "Action(SiteID=eBayMotors|Country=US|Currency=USD|Version=1193|CC=UTF-8)",
    "Category", "Title", "Description", "StartPrice", "Quantity", "Format", "Duration",
    "ShippingProfileName", "ReturnProfileName", "PaymentProfileName", "PostalCode",
    "Brand", "MPN", "CustomLabel", "Product:EPID", "PicURL", "ConditionID",
    "WeightMajor", "WeightMinor", "WeightUnit", "C:Brand", "C:California Prop 65 Warning",
    "C:Color", "C:Country of Origin", "C:Finish", "C:Interchange Part Number", "C:Item Diameter",
    "C:Items Included", "C:Manufacturer Part Number", "C:Manufacturer Warranty", "C:Material",
    "C:Mounting Style", "C:OE/OEM Part Number", "C:Performance Part", "C:Placement on Vehicle",
    "C:Superseded Part Number", "C:Type", "C:Universal Fitment", "C:Vintage Part"
]

items = [
    {
        'mpn': '74324',
        'epid': '74326117',
        'cat_id': '262211',
        'brand': 'Dorman/Help',
        'title': 'Dorman Help 74324 Dome Light Lens Base Assembly GM Chevrolet NOS',
        'price': '13.99',
        'img': 'https://cdn.shopify.com/s/files/1/0645/2074/9130/files/74324-007.jpg?v=1748895887',
        'fitment_table': '''<table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<thead><tr style="background-color: #f2f2f2; text-align: left;"><th>Make</th><th>Years</th><th>Compatible Models</th></tr></thead>
<tbody>
<tr><td>Buick</td><td>1968 - 1990</td><td>LeSabre, Regal, Riviera, Skylark, Century, Electra</td></tr>
<tr><td>Chevrolet</td><td>1968 - 1990</td><td>Caprice, Chevelle, Impala, Monte Carlo, El Camino</td></tr>
<tr><td>Oldsmobile</td><td>1968 - 1990</td><td>Cutlass, Cutlass Supreme, Delta 88, 98, Toronado</td></tr>
<tr><td>Pontiac</td><td>1968 - 1990</td><td>Bonneville, Catalina, Firebird, Grand Am, Grand Prix, LeMans</td></tr>
</tbody></table>''',
        'specs': {'C:Brand': 'Dorman/Help', 'C:Manufacturer Part Number': '74324', 'C:Placement on Vehicle': 'Interior, Overhead', 'C:Type': 'Dome Light Assembly', 'C:Vintage Part': 'Yes'}
    },
    {
        'mpn': '41066',
        'epid': '230400927',
        'cat_id': '42604',
        'brand': 'Dorman/Help',
        'title': 'Dorman Help 41066 Air Cleaner Hold Down Kit Wing Nut & Stud NOS',
        'price': '12.90',
        'img': 'https://cdn.shopify.com/s/files/1/0645/2074/9130/files/41255-007.jpg?v=1748635683',
        'fitment_table': '''<table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<thead><tr style="background-color: #f2f2f2; text-align: left;"><th>Application</th><th>Type</th><th>Compatibility</th></tr></thead>
<tbody>
<tr><td>Carbureted & TBI Air Cleaners</td><td>Wing Nut & Threaded Stud Hardware Kit</td><td>Universal Fits AMC, Buick, Chevrolet, Chrysler, Dodge, Ford, Plymouth, Pontiac</td></tr>
</tbody></table>''',
        'specs': {'C:Brand': 'Dorman/Help', 'C:Manufacturer Part Number': '41066', 'C:Placement on Vehicle': 'Engine Compartment', 'C:Type': 'Air Cleaner Hold Down Kit', 'C:Vintage Part': 'Yes'}
    },
    {
        'mpn': '49015',
        'epid': '75647794',
        'cat_id': '42605',
        'brand': 'Dorman/Help',
        'title': 'Dorman Help 49015 Brake Caliper Bolt Socket Specialty Tool NOS',
        'price': '17.06',
        'img': 'https://cdn.shopify.com/s/files/1/0645/2074/9130/files/49015-007.jpg?v=1748814065',
        'fitment_table': '''<table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<thead><tr style="background-color: #f2f2f2; text-align: left;"><th>Tool Type</th><th>Drive Size</th><th>Application</th></tr></thead>
<tbody>
<tr><td>Brake Caliper Bolt Removal Socket</td><td>3/8 in. Drive Specialty Tool</td><td>Fits Disc Brake Caliper Mounting Bolts on GM, Ford, Chrysler & Imports</td></tr>
</tbody></table>''',
        'specs': {'C:Brand': 'Dorman/Help', 'C:Manufacturer Part Number': '49015', 'C:Placement on Vehicle': 'Front, Rear', 'C:Type': 'Brake Caliper Bolt Socket', 'C:Vintage Part': 'Yes'}
    },
    {
        'mpn': '59001',
        'epid': '230335606',
        'cat_id': '43998',
        'brand': 'Dorman/Help',
        'title': 'Dorman Help 59001 Extension Spring Assortment Kit Multi-Size NOS',
        'price': '14.04',
        'img': 'https://cdn.shopify.com/s/files/1/0645/2074/9130/files/59001-007.jpg?v=1748740544',
        'fitment_table': '''<table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<thead><tr style="background-color: #f2f2f2; text-align: left;"><th>Kit Type</th><th>Contents</th><th>Compatibility</th></tr></thead>
<tbody>
<tr><td>Automotive & General Extension Spring Kit</td><td>Multi-Size Assorted Tension Springs</td><td>Universal Automotive, Throttle Return, Clutch & General Utility Use</td></tr>
</tbody></table>''',
        'specs': {'C:Brand': 'Dorman/Help', 'C:Manufacturer Part Number': '59001', 'C:Placement on Vehicle': 'Engine Compartment, Chassis', 'C:Type': 'Extension Spring Assortment', 'C:Vintage Part': 'Yes'}
    }
]

out_dir = Path(r'C:\Users\kbcha\Documents\Coding_Projects_002\WNC_Take_3\store_discovery')

categories = {}
for item in items:
    cat_id = item['cat_id']
    if cat_id not in categories:
        categories[cat_id] = []
    categories[cat_id].append(item)

for cat_id, cat_items in categories.items():
    file_name = f'eBay_Bulk_Listing_Help_Cat_{cat_id}.csv'
    file_path = out_dir / file_name
    
    rows = []
    for item in cat_items:
        mpn = item['mpn']
        desc_html = f"<h3>{item['title']}</h3><p><strong>Brand:</strong> {item['brand']}</p><p><strong>Manufacturer Part Number:</strong> {mpn}</p><p><strong>ePID:</strong> {item['epid']}</p><p><strong>Condition:</strong> New Old Stock (NOS)</p><hr/><h4>Application & Fitment Information</h4>{item['fitment_table']}<hr/><p><em>WNC Parts Slingers - Fast Shipping on New Old Stock (NOS) Auto Parts!</em></p>"
        
        row = {
            "Action(SiteID=eBayMotors|Country=US|Currency=USD|Version=1193|CC=UTF-8)": "Add",
            "Category": item['cat_id'],
            "Title": item['title'],
            "Description": desc_html,
            "StartPrice": item['price'],
            "Quantity": "1",
            "Format": "FixedPriceItem",
            "Duration": "GTC",
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
            "C:Material": "",
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
    print(f"Generated eBay Bulk CSV: {file_name} ({len(rows)} items)")
