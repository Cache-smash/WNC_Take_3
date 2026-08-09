import csv
from pathlib import Path

csv_path = Path(r'C:\Users\kbcha\Documents\Coding_Projects_002\WNC_Take_3\store_discovery\eBay_Bulk_Listing_Help_47011.csv')

with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
    reader = csv.reader(f)
    headers = next(reader)
    row = next(reader)

# Find Duration column index
dur_idx = headers.index('Duration')
row[dur_idx] = 'GTC'

with open(csv_path, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(headers)
    writer.writerow(row)

print("Updated Duration from '30' to 'GTC' in 47011 CSV!")
