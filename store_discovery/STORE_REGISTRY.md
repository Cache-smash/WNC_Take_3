# MASTER STORE DISCOVERY & PART NUMBER ORIGIN REGISTRY

This registry tracks all target e-commerce stores scraped, their exact domain origin, catalog sizes, and output files containing matched part numbers.

---

| Store Domain | Full Catalog DB | Matched Inventory CSV | Matched Part Numbers List | Status / Date |
| :--- | :--- | :--- | :--- | :--- |
| **`partcatalog.com`** | `store_discovery/partcatalog.db` | `store_discovery/matched_dorman_partcatalog_inventory.csv` | `store_discovery/matched_part_numbers_list.txt` | ✅ Complete (25,000 items, 155 matched parts) |
| **`hotcarparts.com`** | `store_discovery/hotcarparts_com.db` | `store_discovery/hotcarparts_com_matched_inventory.csv` | `store_discovery/hotcarparts_com_matched_parts_list.txt` | ✅ Complete (13,168 items, 313 matched parts) |
| **`koskowskiautoparts.com`** | `store_discovery/koskowskiautoparts_com.db` | `store_discovery/koskowskiautoparts_com_matched_inventory.csv` | `store_discovery/koskowskiautoparts_com_matched_parts_list.txt` | ✅ Complete (25,000 items, 297 matched parts) |
| **`rvpartshop.com`** | `store_discovery/rvpartshop_com.db` | `store_discovery/rvpartshop_com_matched_inventory.csv` | `store_discovery/rvpartshop_com_matched_parts_list.txt` | ✅ Complete (25,000 items, 162 matched parts) |
| **`youngfartsrvparts.com`** | `store_discovery/youngfartsrvparts_com.db` | `store_discovery/youngfartsrvparts_com_matched_inventory.csv` | `store_discovery/youngfartsrvparts_com_matched_parts_list.txt` | ✅ Complete (25,000 items, 163 matched parts) |
| **`sstubes.com`** | `store_discovery/sstubes_com.db` | `store_discovery/sstubes_com_matched_inventory.csv` | `store_discovery/sstubes_com_matched_parts_list.txt` | ✅ Complete (4,634 items, 1 matched part) |

---

## Detailed File Attribution Map

### 1. Store: `partcatalog.com`
- **Origin Domain:** `https://www.partcatalog.com`
- **Database File:** `store_discovery/partcatalog.db`
- **CSV Inventory:** `store_discovery/matched_dorman_partcatalog_inventory.csv`
- **Matched Part Numbers List:** `store_discovery/matched_part_numbers_list.txt`
- **Description:** 25,000 raw products downloaded; 155 unique matched Dorman Help! / 6-digit part numbers.

### 2. Store: `hotcarparts.com`
- **Origin Domain:** `https://www.hotcarparts.com`
- **Database File:** `store_discovery/hotcarparts_com.db`
- **CSV Inventory:** `store_discovery/hotcarparts_com_matched_inventory.csv`
- **Matched Part Numbers List:** `store_discovery/hotcarparts_com_matched_parts_list.txt`
- **Description:** Active ingestion & matching pipeline.

---

*This registry is automatically updated as additional stores (FleetPro, Koskowski, Young Farts RV, RV Part Shop, etc.) are processed.*
