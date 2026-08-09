import json
import logging
import re
import time
from typing import Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_RATE_LIMIT_SECS = 2.0
_TIMEOUT         = 15
_MAX_SPEC_BLOCKS = 5

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    )
}

# CSS class keyword fragments that typically mark spec/feature containers
_SPEC_KEYWORDS = {"spec", "feature", "detail", "attribute", "description", "tech"}


def _extract_header(soup: BeautifulSoup) -> str:
    """Return ONLY the primary product title from the page."""
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)
    return ""


def _extract_specs(soup: BeautifulSoup) -> str:
    """Return concatenated text from all tab containers."""
    blocks: list[str] = []
    # Target all PartCatalog tab panels (Description, Specs, Fitment, Interchange)
    for tag in soup.find_all("div", class_="pv2-tab-panel"):
        text = tag.get_text(separator=" ", strip=True)
        if len(text) > 20:          # Skip trivially short matches
            blocks.append(text)
    return " | ".join(blocks)


def scrape_part(mpn: str, brand: str = "", subtype: str = "", log_callback=None) -> dict:
    """
    Fetch and parse the PartCatalog product page for `mpn` via their search endpoint.
    Always returns a dict with keys: mpn, product_header, spec_text, specs_dict, compatibility, interchange_numbers.
    Never raises — failures are logged and return empty string fields.
    """
    def _log(msg: str) -> None:
        if log_callback:
            log_callback(msg)
        logger.info(msg)

    empty = {
        "mpn": mpn, 
        "product_header": "", 
        "spec_text": "", 
        "specs_dict": {}, 
        "compatibility": [], 
        "interchange_numbers": []
    }

    # ── Step 1: Search ──
    search_url = f"https://www.partcatalog.com/search?q=Dorman+{mpn}"
    _log(f"[Scraper] Fetching PartCatalog search for Dorman {mpn} (rate-limit: {_RATE_LIMIT_SECS}s)...")
    time.sleep(_RATE_LIMIT_SECS)

    try:
        search_resp = requests.get(search_url, headers=_HEADERS, timeout=_TIMEOUT, allow_redirects=True)
        search_resp.raise_for_status()

        search_soup = BeautifulSoup(search_resp.text, "html.parser")
        product_link = None
        
        # Regex to match the specific PartCatalog product slug containing the MPN
        # e.g., /products/dorman-76916-window-crank-handle
        link_pattern = re.compile(rf"/products/[-a-z0-9]*{re.escape(mpn)}[-a-z0-9]*", re.IGNORECASE)
        
        # Scoring keywords
        brand_words = [w.lower().strip() for w in re.split(r'[^a-zA-Z0-9]', brand) if w.strip()]
        subtype_words = [w.lower().strip() for w in re.split(r'[^a-zA-Z0-9]', subtype) if w.strip()]
        
        # Require Dorman / Help brand match in href or text
        best_score = 0
        for a in search_soup.find_all("a", href=True):
            href = a["href"]
            if link_pattern.search(href):
                href_lower = href.lower()
                text_lower = a.get_text().lower()

                # MUST contain Dorman or Help to be considered
                if not ("dorman" in href_lower or "dorman" in text_lower or "help" in href_lower or "help" in text_lower):
                    continue

                score = 10
                for word in subtype_words:
                    if word in href_lower or word in text_lower:
                        score += 2

                if score > best_score:
                    best_score = score
                    product_link = href

        # PartCatalog requires exact Dorman slugs. If we can't find Dorman in search, do not guess.
        if not product_link:
            _log(f"[Scraper] ⚠ No Dorman/Help product link containing {mpn} found in search results. Using fallback.")
            return empty

        product_url = product_link if product_link.startswith("http") else f"https://www.partcatalog.com{product_link}"

        # ── Step 2: Product Page ──
        _log(f"[Scraper] Found Dorman product page, fetching (rate-limit: {_RATE_LIMIT_SECS}s)...")
        time.sleep(_RATE_LIMIT_SECS)
        
        prod_resp = requests.get(product_url, headers=_HEADERS, timeout=_TIMEOUT, allow_redirects=True)
        
        if prod_resp.status_code == 404:
            _log(f"[Scraper] ⚠ 404 — Product page {product_url} not found. Using fallback.")
            return empty

        prod_resp.raise_for_status()

        soup           = BeautifulSoup(prod_resp.text, "html.parser")
        product_header = _extract_header(soup)

        # Verify page header contains Dorman or Help
        if not ("dorman" in product_header.lower() or "help" in product_header.lower()):
            _log(f"[Scraper] ⚠ Product header '{product_header}' does not match Dorman/Help brand. Using fallback.")
            return empty
        spec_text      = _extract_specs(soup)

        # Extract structured specifications (Table 0)
        specs_dict = {}
        tables = soup.find_all("table")
        if tables:
            for row in tables[0].find_all("tr"):
                cells = row.find_all(["td", "th"])
                if len(cells) == 2:
                    key = cells[0].get_text(strip=True)
                    val = cells[1].get_text(strip=True)
                    specs_dict[key] = val

        # Extract compatibility table (Table 1)
        compatibility = []
        if len(tables) > 1:
            headers = []
            for row_idx, row in enumerate(tables[1].find_all("tr")):
                if row_idx == 0:
                    headers = [cell.get_text(strip=True) for cell in row.find_all(["th", "td"])]
                else:
                    cells = [cell.get_text(strip=True) for cell in row.find_all("td")]
                    if len(cells) == len(headers):
                        compatibility.append(dict(zip(headers, cells)))

        # Extract interchange numbers
        interchange_numbers = []
        interchange_container = soup.find("div", class_="pv2-interchange-grid")
        if interchange_container:
            chips = interchange_container.find_all("span", class_="pv2-interchange-chip")
            interchange_numbers = [chip.get_text(strip=True) for chip in chips]
        else:
            # Fallback to json-ld search
            json_ld_script = soup.find("script", type="application/ld+json")
            if json_ld_script:
                try:
                    data = json.loads(json_ld_script.string)
                    if isinstance(data, dict):
                        for prop in data.get("additionalProperty", []):
                            if prop.get("name") == "Interchange Numbers":
                                interchange_numbers = [n.strip() for n in prop.get("value", "").split(",") if n.strip()]
                except Exception:
                    pass

        _log(f"[Scraper] ✓ {mpn} — header: {product_header[:70]!r}")
        return {
            "mpn": mpn,
            "product_header": product_header,
            "spec_text": spec_text,
            "specs_dict": specs_dict,
            "compatibility": compatibility,
            "interchange_numbers": interchange_numbers
        }

    except requests.RequestException as exc:
        _log(f"[Scraper] ⚠ Request error for {mpn}: {exc}. Using fallback.")
        return empty

