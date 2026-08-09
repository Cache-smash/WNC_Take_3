import sqlite3
import json

conn = sqlite3.connect("store_discovery/pinelakeparts_com.db")
cursor = conn.cursor()

total = cursor.execute("SELECT COUNT(*) FROM shopify_products").fetchone()[0]
grote_rows = cursor.execute("SELECT id, title, sku, vendor, price, handle FROM shopify_products WHERE UPPER(vendor) LIKE '%GROTE%' OR UPPER(title) LIKE '%GROTE%'").fetchall()
dietz_rows = cursor.execute("SELECT id, title, sku, vendor, price, handle FROM shopify_products WHERE UPPER(vendor) LIKE '%DIETZ%' OR UPPER(title) LIKE '%DIETZ%'").fetchall()

print(f"=== PINELAKEPARTS.COM BRAND INSPECTION ===")
print(f"Total Products Ingested: {total:,}")
print(f"Grote Lighting Items:    {len(grote_rows):,}")
print(f"Dietz Lighting Items:    {len(dietz_rows):,}\n")

print("Sample Grote Lighting Items:")
for r in grote_rows[:5]:
    print(f" - Title: {r[1]} | SKU: {r[2]} | Vendor: {r[3]} | Price: ${r[4]}")

print("\nSample Dietz Lighting Items:")
for r in dietz_rows[:5]:
    print(f" - Title: {r[1]} | SKU: {r[2]} | Vendor: {r[3]} | Price: ${r[4]}")

conn.close()
