import os
import re
from pathlib import Path

ARCH_DIR = Path(r"C:\Users\kbcha\Documents\Coding_Projects_002\WNC_Take_3\store_discovery\csv_archive")

def standardize_names():
    renamed_count = 0

    # 1. Standardize 01_Ready_To_Upload
    upload_dir = ARCH_DIR / "01_Ready_To_Upload"
    if upload_dir.exists():
        for f in upload_dir.glob("*.csv"):
            # Extract timestamp prefix (YYYY-MM-DD_HHMM)
            m_time = re.match(r"^(\d{4}-\d{2}-\d{2}_\d{4})", f.name)
            ts = m_time.group(1) if m_time else "2026-08-02_0000"
            
            # Extract category or part number
            cat_match = re.search(r"Cat_(\d+)", f.name, re.IGNORECASE)
            part_match = re.search(r"Help_(\d+)", f.name, re.IGNORECASE)
            
            if cat_match:
                new_name = f"{ts}_UPLOAD_Cat_{cat_match.group(1)}.csv"
            elif part_match:
                new_name = f"{ts}_UPLOAD_Part_{part_match.group(1)}.csv"
            else:
                new_name = f"{ts}_UPLOAD_Batch.csv"

            dest = upload_dir / new_name
            if f != dest:
                f.rename(dest)
                renamed_count += 1
                print(f"Renamed: {f.name} -> {new_name}")

    # 2. Standardize 02_Listing_Revisions
    rev_dir = ARCH_DIR / "02_Listing_Revisions"
    if rev_dir.exists():
        for f in rev_dir.glob("*.csv"):
            m_time = re.match(r"^(\d{4}-\d{2}-\d{2}_\d{4})", f.name)
            ts = m_time.group(1) if m_time else "2026-08-02_0000"
            
            cat_match = re.search(r"Cat_(\d+)", f.name, re.IGNORECASE)
            part_match = re.search(r"Help_(\d+)", f.name, re.IGNORECASE)
            
            if cat_match:
                new_name = f"{ts}_REVISE_Cat_{cat_match.group(1)}_Images.csv"
            elif part_match:
                new_name = f"{ts}_REVISE_Part_{part_match.group(1)}_Images.csv"
            else:
                new_name = f"{ts}_REVISE_Images.csv"

            dest = rev_dir / new_name
            if f != dest:
                f.rename(dest)
                renamed_count += 1
                print(f"Renamed: {f.name} -> {new_name}")

    # 3. Standardize 03_eBay_Return_Reports
    rep_dir = ARCH_DIR / "03_eBay_Return_Reports"
    if rep_dir.exists():
        for f in rep_dir.glob("*.csv*"):
            m_time = re.match(r"^(\d{4}-\d{2}-\d{2}_\d{4})", f.name)
            ts = m_time.group(1) if m_time else "2026-08-02_0000"
            
            cat_match = re.search(r"Cat_(\d+)", f.name, re.IGNORECASE)
            part_match = re.search(r"Help_(\d+)", f.name, re.IGNORECASE)
            active_match = "active-listings" in f.name
            
            if active_match:
                new_name = f"{ts}_REPORT_Active_Store_Listings.csv"
            elif cat_match:
                new_name = f"{ts}_REPORT_Cat_{cat_match.group(1)}.csv"
            elif part_match:
                new_name = f"{ts}_REPORT_Part_{part_match.group(1)}.csv"
            else:
                new_name = f"{ts}_REPORT_Response.csv"

            dest = rep_dir / new_name
            if f != dest:
                f.rename(dest)
                renamed_count += 1
                print(f"Renamed: {f.name} -> {new_name}")

    # 4. Standardize 04_Store_Sweeps_And_Inventories
    sweep_dir = ARCH_DIR / "04_Store_Sweeps_And_Inventories"
    if sweep_dir.exists():
        for f in sweep_dir.glob("*.csv"):
            m_time = re.match(r"^(\d{4}-\d{2}-\d{2}_\d{4})", f.name)
            ts = m_time.group(1) if m_time else "2026-08-02_0000"
            name_u = f.name.upper()

            if "FULL_SWEEP" in name_u:
                new_name = f"{ts}_SWEEP_Koskowski_Full_Store.csv"
            elif "KOSKOWSKI" in name_u:
                new_name = f"{ts}_SWEEP_Koskowski_Help5.csv"
            elif "YOUNGPARTS" in name_u or "YOUNG" in name_u:
                new_name = f"{ts}_SWEEP_YoungFartsRV.csv"
            elif "PARTCATALOG" in name_u:
                new_name = f"{ts}_SWEEP_PartCatalog.csv"
            elif "STRICT" in name_u:
                new_name = f"{ts}_SWEEP_Strict_Dorman_Inventory.csv"
            elif "GROTE_DIETZ" in name_u:
                new_name = f"{ts}_SWEEP_Dorman_Grote_Dietz.csv"
            elif "GROTE" in name_u:
                new_name = f"{ts}_SWEEP_Dorman_Grote.csv"
            elif "MASTER" in name_u:
                new_name = f"{ts}_SWEEP_Master_Matched_Inventory.csv"
            else:
                new_name = f"{ts}_SWEEP_{f.name}"

            dest = sweep_dir / new_name
            if f != dest:
                f.rename(dest)
                renamed_count += 1
                print(f"Renamed: {f.name} -> {new_name}")

    # 5. Standardize 05_Reference_Listing_Reports
    ref_dir = ARCH_DIR / "05_Reference_Listing_Reports"
    if ref_dir.exists():
        for f in ref_dir.glob("*.csv"):
            m_time = re.match(r"^(\d{4}-\d{2}-\d{2}_\d{4})", f.name)
            ts = m_time.group(1) if m_time else "2026-08-02_0000"
            new_name = f"{ts}_REFERENCE_eBay_Accepted_Template.csv"
            dest = ref_dir / new_name
            if f != dest:
                f.rename(dest)
                renamed_count += 1
                print(f"Renamed: {f.name} -> {new_name}")

    print(f"\nStandardized naming for {renamed_count} files!")

if __name__ == "__main__":
    standardize_names()
