import os
import shutil
import csv
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(r"C:\Users\kbcha\Documents\Coding_Projects_002\WNC_Take_3\store_discovery")

# Define Destination Subfolders
FOLDERS = {
    "scripts": BASE_DIR / "scripts",
    "uploads": BASE_DIR / "csv_archive" / "01_Ready_To_Upload",
    "revisions": BASE_DIR / "csv_archive" / "02_Listing_Revisions",
    "reports": BASE_DIR / "csv_archive" / "03_eBay_Return_Reports",
    "sweeps": BASE_DIR / "csv_archive" / "04_Store_Sweeps_And_Inventories",
    "references": BASE_DIR / "csv_archive" / "05_Reference_Listing_Reports",
}

for folder in FOLDERS.values():
    folder.mkdir(parents=True, exist_ok=True)

def organize():
    moved_scripts = 0
    moved_csvs = 0

    # 1. Organize Python Scripts
    # Keep main core workflow scripts in root, move 1-off utility scripts to scripts/
    core_scripts = {"store_scraper_engine.py", "full_koskowski_store_sweep.py"}
    for item in BASE_DIR.glob("*.py"):
        if item.name not in core_scripts:
            shutil.move(str(item), str(FOLDERS["scripts"] / item.name))
            moved_scripts += 1

    # 2. Organize CSV Files
    for item in BASE_DIR.glob("*.csv"):
        mtime = datetime.fromtimestamp(item.stat().st_mtime)
        timestamp_str = mtime.strftime("%Y-%m-%d_%H%M")
        name = item.name

        # Case A: eBay Return Error Reports (Contain long batch numbers like ...-12336197326.csv)
        if "-Aug-" in name or "-Jul-" in name or "report-202" in name:
            clean_name = name.split("-Aug-")[0].split("-Jul-")[0].replace("eBay_Bulk_Listing_", "")
            dest_name = f"{timestamp_str}_Report_{clean_name}.csv"
            shutil.move(str(item), str(FOLDERS["reports"] / dest_name))
            moved_csvs += 1

        # Case B: Revision CSVs
        elif "Revise" in name or "revise" in name:
            dest_name = f"{timestamp_str}_Revise_{name}"
            shutil.move(str(item), str(FOLDERS["revisions"] / dest_name))
            moved_csvs += 1

        # Case C: Store Sweeps & Inventory Exports
        elif "INVENTORY" in name or "matched" in name or "SWEEP" in name:
            dest_name = f"{timestamp_str}_{name}"
            shutil.move(str(item), str(FOLDERS["sweeps"] / dest_name))
            moved_csvs += 1

        # Case D: Active Listing Reference Reports
        elif "active-listings" in name or "ebay_motors_listings" in name:
            dest_name = f"{timestamp_str}_Reference_{name}"
            shutil.move(str(item), str(FOLDERS["references"] / dest_name))
            moved_csvs += 1

        # Case E: Ready-To-Upload Listing CSVs
        elif "eBay_Bulk_Listing_" in name:
            dest_name = f"{timestamp_str}_Upload_{name}"
            shutil.move(str(item), str(FOLDERS["uploads"] / dest_name))
            moved_csvs += 1

    print("==========================================================")
    print("       STORE DISCOVERY AUTOMATED ORGANIZER COMPLETE")
    print("==========================================================")
    print(f"One-off Utility Scripts Moved to /scripts/: {moved_scripts}")
    print(f"CSV Files Timestamped & Categorized:         {moved_csvs}")

if __name__ == "__main__":
    organize()
