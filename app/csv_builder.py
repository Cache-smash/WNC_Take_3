"""
csv_builder.py — Assemble the final eBay Motors CSV listing file.

Accepts a list of fully-enriched part dicts (from worker.py) and outputs
a UTF-8 BOM-encoded CSV (compatible with Microsoft Excel) containing:

  Standard headers    : Action, Category, Title, Description, Price,
                        Quantity, Format, Duration
  Business profiles   : ShippingProfileName, ReturnProfileName,
                        PaymentProfileName  (eBay managed business policies)
  Location header     : PostalCode
  Catalog / inventory : Brand (standalone, for eBay catalog matching),
                        CustomLabel ({mpn}-1 SKU format),
                        Product:EPID (eBay catalog link)
  Image header        : PicURL (pipe-separated Cloudinary URLs)
  Dynamic headers     : C:<Aspect> (from eBay Taxonomy API, merged across
                        all categories present in the batch)

Pre-filled C: columns:
  C:Brand                      <- part brand (e.g. "Dorman/Help")
  C:Manufacturer Part Number   <- MPN
  All other C: columns         <- empty string (manual fill)
"""

import csv
import io
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Fixed columns in the order they appear in the output CSV.
# Column names are case-sensitive and must match eBay File Exchange exactly.
_STANDARD_HEADERS: list[str] = [
    "Action(SiteID=eBayMotors|Country=US|Currency=USD|Version=1193|CC=UTF-8)",
    "Category",
    "Title",
    "Description",
    "StartPrice",
    "Quantity",
    "Format",
    "Duration",
    # eBay Business Policy profile names (replaces individual shipping/return fields)
    "ShippingProfileName",
    "ReturnProfileName",
    "PaymentProfileName",
    # Item location
    "PostalCode",
    # Catalog matching + inventory tracking
    "Brand",
    "MPN",
    "CustomLabel",
    "Product:EPID",
    "PicURL",
    # Item Condition ID (e.g. 1000 for New)
    "ConditionID",
    # Package weight details (required for calculated shipping policy or category validation)
    "WeightMajor",
    "WeightMinor",
    "WeightUnit",
]

_STATIC_ROW: dict[str, str] = {
    "Action(SiteID=eBayMotors|Country=US|Currency=USD|Version=1193|CC=UTF-8)": "Add",
    "Format":              "FixedPriceItem",
    "Duration":            "GTC",
    "Quantity":            "1",
    "StartPrice":          "ADD_PRICE",
    "ConditionID":         "1000",
    # Business policy profiles — must exactly match the saved profile names in Seller Hub
    "ShippingProfileName": "Free Shipping",
    "ReturnProfileName":   "30 Days Money Back or Replacement (Primary Return Policy)",
    "PaymentProfileName":  "eBay Managed Payments (Primary Payment Policy)",
    # WNC Parts Slingers — Hendersonville, NC
    "PostalCode":          "28739",
    # Default package weight properties (1 lb 0 oz)
    "WeightMajor":         "1",
    "WeightMinor":         "0",
    "WeightUnit":          "lb",
}


def build_csv(enriched_parts: list[dict]) -> bytes:
    """
    Build and return a UTF-8 BOM CSV as raw bytes.

    Each item in `enriched_parts` must be a dict with:
        part_data : dict  — row from db_manager.lookup_parts()
        listing   : dict  — {"title": str, "description_html": str}
        pic_url   : str   — pipe-separated Cloudinary URLs (may be "")
        aspects   : list[str] — ["C:Brand", "C:Fitment Type", …]
    """
    # Collect all unique C: columns, preserving insertion order across parts
    seen_aspects: set[str]  = set()
    all_aspects:  list[str] = []
    for ep in enriched_parts:
        for col in ep.get("aspects", []):
            if col not in seen_aspects:
                all_aspects.append(col)
                seen_aspects.add(col)

    final_headers = _STANDARD_HEADERS + all_aspects

    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=final_headers,
        extrasaction="ignore",
        lineterminator="\r\n",
    )
    writer.writeheader()

    for ep in enriched_parts:
        pd      = ep.get("part_data", {})
        listing = ep.get("listing", {})
        mpn     = pd.get("mpn", "")
        brand   = pd.get("brand", "Dorman/Help")

        row: dict[str, Any] = {**_STATIC_ROW}
        row["Category"]     = pd.get("category_id", "")
        row["Title"]        = listing.get("title", "")
        raw_desc = listing.get("description_html", "")
        # Hard safety guardrail: Cap Description at 25,000 chars to prevent Excel display line breaks and eBay errors
        if len(raw_desc) > 25000:
            parts = raw_desc.split("<tr>")
            raw_desc = "<tr>".join(parts[:41]) + "</table><p><em>...and additional vehicle applications. Please refer to eBay compatibility table above.</em></p>"
        row["Description"]  = raw_desc

        # Standalone Brand + MPN — guarantees catalog matching alongside Product:EPID
        row["Brand"]        = brand
        row["MPN"]          = mpn
        # CustomLabel = SKU in {mpn}-1 format for inventory tracking
        row["CustomLabel"]  = f"{mpn}-1"
        row["Product:EPID"] = pd.get("epid", "")
        row["PicURL"]       = ep.get("pic_url", "")

        scraped_data = ep.get("scraped_data", {})
        specs_dict   = scraped_data.get("specs_dict", {})
        interchanges = scraped_data.get("interchange_numbers", [])

        # Pre-fill recognisable C: columns; leave others blank for manual entry
        for col in all_aspects:
            # Strip "C:" prefix and clean
            aspect_name = col[2:] if col.lower().startswith("c:") else col
            aspect_clean = aspect_name.lower().strip()

            if "manufacturer part number" in aspect_clean or aspect_clean == "mpn":
                row[col] = mpn
            elif aspect_clean == "brand":
                row[col] = brand
            elif "interchange" in aspect_clean or "cross reference" in aspect_clean or "replaces" in aspect_clean:
                row[col] = ", ".join(interchanges) if interchanges else ""
            else:
                # Dynamic matching against scraped specifications
                matched_val = ""
                for spec_key, spec_val in specs_dict.items():
                    spec_key_clean = spec_key.lower().strip()
                    if aspect_clean == spec_key_clean or aspect_clean in spec_key_clean or spec_key_clean in aspect_clean:
                        matched_val = spec_val
                        break
                row[col] = matched_val

        writer.writerow(row)

    csv_bytes = output.getvalue().encode("utf-8-sig")  # BOM → Excel auto-detects UTF-8
    logger.info(
        "[CSV] ✓ Built %d-row CSV with %d total columns (%d C: aspect columns).",
        len(enriched_parts),
        len(final_headers),
        len(all_aspects),
    )
    return csv_bytes
