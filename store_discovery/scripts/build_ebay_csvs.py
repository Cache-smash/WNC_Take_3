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
        'mpn': '56452',
        'epid': '261895697',
        'cat_id': '262198',
        'cat_name': 'Power Outlets & Lighters',
        'item_name': 'Cigarette Lighter Knob & Element',
        'brand': 'Dorman/Help',
        'title': 'Dorman Help 56452 Cigarette Lighter Knob & Element NOS Vintage',
        'img': 'https://cdn.shopify.com/s/files/1/0645/2074/9130/files/56452-007.jpg?v=1748722410',
        'price': '14.95',
        'fitment_summary': 'Universal / Fits Various AMC, Buick, Chevrolet, Chrysler, Dodge, Ford, Plymouth, Pontiac Models',
        'specs': {'C:Brand': 'Dorman/Help', 'C:Manufacturer Part Number': '56452', 'C:Placement on Vehicle': 'Front, Center, Dashboard', 'C:Vintage Part': 'Yes', 'C:Type': 'Cigarette Lighter Element'}
    },
    {
        'mpn': '56458',
        'epid': '75765799',
        'cat_id': '262198',
        'cat_name': 'Power Outlets & Lighters',
        'item_name': 'Cigarette Lighter Element',
        'brand': 'Dorman/Help',
        'title': 'Dorman Help 56458 Cigarette Lighter Element Rochester Style NOS',
        'img': 'https://cdn.shopify.com/s/files/1/0645/2074/9130/files/56458-007.jpg?v=1748722427',
        'price': '12.95',
        'fitment_summary': 'Fits Rochester-style lighter sockets on GM, Ford, Chrysler & AMC Vehicles',
        'specs': {'C:Brand': 'Dorman/Help', 'C:Manufacturer Part Number': '56458', 'C:Placement on Vehicle': 'Front, Dashboard', 'C:Vintage Part': 'Yes', 'C:Type': 'Cigarette Lighter Element'}
    },
    {
        'mpn': '56462',
        'epid': '262137682',
        'cat_id': '262198',
        'cat_name': 'Power Outlets & Lighters',
        'item_name': 'Cigarette Lighter Assembly',
        'brand': 'Dorman/Help',
        'title': 'Dorman Help 56462 Cigarette Lighter Assembly Chrome NOS Vintage',
        'img': 'https://cdn.shopify.com/s/files/1/0645/2074/9130/files/56462-007.jpg?v=1748722431',
        'price': '16.95',
        'fitment_summary': 'Universal 12V Power Outlet & Lighter Assembly for Classic Cars & Trucks',
        'specs': {'C:Brand': 'Dorman/Help', 'C:Manufacturer Part Number': '56462', 'C:Placement on Vehicle': 'Front, Center, Dashboard', 'C:Vintage Part': 'Yes', 'C:Type': 'Cigarette Lighter Assembly'}
    },
    {
        'mpn': '56464',
        'epid': '174003328',
        'cat_id': '262198',
        'cat_name': 'Power Outlets & Lighters',
        'item_name': 'Cigarette Lighter Knob & Element',
        'brand': 'Dorman/Help',
        'title': 'Dorman Help 56464 Cigarette Lighter Knob & Element Casco NOS',
        'img': 'https://cdn.shopify.com/s/files/1/0645/2074/9130/files/56464-007.jpg?v=1748722440',
        'price': '13.95',
        'fitment_summary': 'Fits Casco-style lighter sockets on Vintage Ford, GM & Mopar Models',
        'specs': {'C:Brand': 'Dorman/Help', 'C:Manufacturer Part Number': '56464', 'C:Placement on Vehicle': 'Front, Dashboard', 'C:Vintage Part': 'Yes', 'C:Type': 'Cigarette Lighter Element'}
    },
    {
        'mpn': '03101',
        'epid': '173950153',
        'cat_id': '33634',
        'cat_name': 'Clamps, Flanges, Hangers & Hardware',
        'item_name': 'Exhaust Flange Stud and Nut Hardware Kit',
        'brand': 'Dorman/Help',
        'title': 'Dorman Help 03101 Exhaust Flange Stud & Nut Hardware Kit GM Ford NOS',
        'img': 'https://koskowskiautoparts.com/cdn/shop/files/03101_Help_Exhaust.jpg',
        'price': '9.95',
        'fitment_summary': 'Fits 3/8-16 x 2-1/4 in. Exhaust Flange Applications for GM, Ford & Chrysler',
        'specs': {'C:Brand': 'Dorman/Help', 'C:Manufacturer Part Number': '03101', 'C:Placement on Vehicle': 'Exhaust Manifold, Flange', 'C:Vintage Part': 'Yes', 'C:Type': 'Exhaust Flange Stud & Nut'}
    },
    {
        'mpn': '03104',
        'epid': '173877991',
        'cat_id': '33634',
        'cat_name': 'Clamps, Flanges, Hangers & Hardware',
        'item_name': 'Exhaust Flange Stud and Nut Hardware Kit',
        'brand': 'Dorman/Help',
        'title': 'Dorman Help 03104 Exhaust Flange Stud & Nut Kit M10-1.50 NOS',
        'img': 'https://koskowskiautoparts.com/cdn/shop/files/03104_Help_Exhaust.jpg',
        'price': '10.95',
        'fitment_summary': 'Fits M10-1.50 x 68mm Metric Exhaust Manifold Flanges (GM, Ford, Import)',
        'specs': {'C:Brand': 'Dorman/Help', 'C:Manufacturer Part Number': '03104', 'C:Placement on Vehicle': 'Exhaust Manifold, Flange', 'C:Vintage Part': 'Yes', 'C:Type': 'Exhaust Flange Stud & Nut'}
    },
    {
        'mpn': '03126',
        'epid': '173874315',
        'cat_id': '33634',
        'cat_name': 'Clamps, Flanges, Hangers & Hardware',
        'item_name': 'Exhaust Flange Stud and Nut Hardware Kit',
        'brand': 'Dorman/Help',
        'title': 'Dorman Help 03126 Exhaust Flange Stud & Nut Kit M10-1.25 NOS',
        'img': 'https://koskowskiautoparts.com/cdn/shop/files/03126_Help_Exhaust.jpg',
        'price': '10.95',
        'fitment_summary': 'Fits M10-1.25 Japanese & Domestic Exhaust Pipe Flanges',
        'specs': {'C:Brand': 'Dorman/Help', 'C:Manufacturer Part Number': '03126', 'C:Placement on Vehicle': 'Exhaust Manifold, Flange', 'C:Vintage Part': 'Yes', 'C:Type': 'Exhaust Flange Stud & Nut'}
    },
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
        'fitment_summary': 'Fits GM, Ford & Chrysler V6 & V8 Crankcase Ventilation PCV Valves',
        'specs': {'C:Brand': 'Dorman/Help', 'C:Manufacturer Part Number': '47034', 'C:Placement on Vehicle': 'Engine Compartment, Valve Cover', 'C:Vintage Part': 'Yes', 'C:Type': 'PCV Elbow'}
    }
]

categories = {}
for item in items:
    cat_id = item['cat_id']
    if cat_id not in categories:
        categories[cat_id] = []
    categories[cat_id].append(item)

out_dir = Path(r'C:\Users\kbcha\Documents\Coding_Projects_002\WNC_Take_3\store_discovery')

for cat_id, cat_items in categories.items():
    file_name = f'eBay_Bulk_Listing_Help_Cat_{cat_id}.csv'
    file_path = out_dir / file_name
    
    rows = []
    for item in cat_items:
        mpn = item['mpn']
        desc_html = f"<h3>{item['title']}</h3><p><strong>Brand:</strong> {item['brand']}</p><p><strong>Manufacturer Part Number:</strong> {mpn}</p><p><strong>ePID:</strong> {item['epid']}</p><p><strong>Condition:</strong> New Old Stock (NOS)</p><hr/><h4>Application & Fitment Information</h4><p>{item['fitment_summary']}</p><hr/><p><em>WNC Parts Slingers - Fast Shipping on New Old Stock (NOS) Auto Parts!</em></p>"
        
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
    print(f"Updated eBay Bulk CSV with 40 Standard Headers: {file_name} ({len(rows)} items)")
