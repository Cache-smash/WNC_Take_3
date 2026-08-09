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

dorman_cdn_photos = "https://static.dormanproducts.com/images/product/large/47011-001.jpg|https://static.dormanproducts.com/images/product/large/47011-003.jpg"

fitment_table = '<table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; width: 100%;"><thead><tr style="background-color: #f2f2f2; text-align: left;"><th>Application</th><th>Tubing Size</th><th>Universal Compatibility</th></tr></thead><tbody><tr><td>Automotive Vacuum & Emissions Systems</td><td>3/16 in. x 3/16 in. Hard Vacuum Tubing</td><td>Fits Various AMC, Buick, Cadillac, Chevrolet, Chrysler, Dodge, Ford, GMC, Jeep, Oldsmobile, Plymouth, Pontiac Models</td></tr></tbody></table>'

desc_html = '<h3>Dorman Help 47011 Vacuum Connector 2-Pack 3/16" x 3/16" NOS</h3><p><strong>Brand:</strong> Dorman/Help</p><p><strong>Manufacturer Part Number:</strong> 47011</p><p><strong>ePID:</strong> 230473847</p><p><strong>Condition:</strong> New Old Stock (NOS)</p><p><strong>Quantity Per Package:</strong> 2 Connectors</p><hr/><h4>Application & Fitment Information</h4><p>Designed to replace cracked or broken factory vacuum fittings. Manufactured from durable plastic material for long service life. Straight vacuum connector suitable for 3/16" x 3/16" hard vacuum tubing in automotive vacuum and emissions systems.</p>' + fitment_table + '<hr/><p><em>WNC Parts Slingers - Fast Shipping on New Old Stock (NOS) Auto Parts!</em></p>'

row = {
    "Action(SiteID=eBayMotors|Country=US|Currency=USD|Version=1193|CC=UTF-8)": "Add",
    "Category": "46097",
    "Title": "Dorman Help 47011 Vacuum Connector 2-Pack 3/16\" x 3/16\" Hard Tubing NOS",
    "Description": desc_html,
    "StartPrice": "10.59",
    "Quantity": "1",
    "Format": "FixedPriceItem",
    "Duration": "30",
    "ShippingProfileName": "Free Shipping",
    "ReturnProfileName": "30 Days Money Back or Replacement (Primary Return Policy)",
    "PaymentProfileName": "eBay Managed Payments (Primary Payment Policy)",
    "PostalCode": "28739",
    "Brand": "Dorman/Help",
    "MPN": "47011",
    "CustomLabel": "HELP-47011",
    "Product:EPID": "230473847",
    "PicURL": dorman_cdn_photos,
    "ConditionID": "1000",
    "WeightMajor": "0",
    "WeightMinor": "4",
    "WeightUnit": "lb",
    "C:Brand": "Dorman/Help",
    "C:California Prop 65 Warning": "",
    "C:Color": "Black",
    "C:Country of Origin": "",
    "C:Finish": "",
    "C:Interchange Part Number": "",
    "C:Item Diameter": "3/16 in",
    "C:Items Included": "2 Vacuum Connectors",
    "C:Manufacturer Part Number": "47011",
    "C:Manufacturer Warranty": "",
    "C:Material": "Plastic",
    "C:Mounting Style": "Push-on",
    "C:OE/OEM Part Number": "",
    "C:Performance Part": "",
    "C:Placement on Vehicle": "Engine Compartment",
    "C:Superseded Part Number": "",
    "C:Type": "Vacuum Connector",
    "C:Universal Fitment": "Yes",
    "C:Vintage Part": "Yes"
}

file_path = Path(r'C:\Users\kbcha\Documents\Coding_Projects_002\WNC_Take_3\store_discovery\eBay_Bulk_Listing_Help_47011.csv')
with open(file_path, 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=REF_HEADERS)
    writer.writeheader()
    writer.writerow(row)

print("Updated 47011 CSV with official high-res Dorman static CDN photo URLs!")
