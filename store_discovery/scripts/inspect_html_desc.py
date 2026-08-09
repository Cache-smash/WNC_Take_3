import sqlite3

conn = sqlite3.connect("store_discovery/koskowskiautoparts_com.db")
cursor = conn.cursor()

row = cursor.execute("SELECT title, body_html FROM shopify_products WHERE title LIKE '%42064%'").fetchone()

if row:
    print("=== TITLE ===")
    print(row[0])
    print("\n=== RAW HTML DESCRIPTION / FITMENT FROM DB ===")
    print(row[1])
else:
    print("Not found")

conn.close()
