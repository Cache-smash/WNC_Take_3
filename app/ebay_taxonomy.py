"""
ebay_taxonomy.py — Fetch item aspects for an eBay category.

Calls the eBay Commerce Taxonomy API (v1) for site ID 100 (US Motors)
and returns a deduplicated, sorted list of C:-prefixed column name strings
suitable for direct use as eBay CSV header columns.
"""

import logging

import requests

from .ebay_auth import get_token

logger = logging.getLogger(__name__)

_TAXONOMY_URL = (
    "https://api.ebay.com/commerce/taxonomy/v1/"
    "category_tree/100/get_item_aspects_for_category"
)


def get_aspects_for_category(category_id: str) -> list[str]:
    """
    Return a list of 'C:<aspect name>' strings for the given eBay category ID.
    Results are sorted alphabetically and deduplicated.
    Raises requests.HTTPError on API failure.
    """
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept":        "application/json",
    }
    params = {"category_id": category_id}

    logger.info("[Taxonomy] Fetching aspects for category_id=%s", category_id)
    resp = requests.get(_TAXONOMY_URL, headers=headers, params=params, timeout=15)
    resp.raise_for_status()

    data    = resp.json()
    aspects = data.get("aspects", [])

    seen:    set[str] = set()
    columns: list[str] = []

    for aspect in aspects:
        name = aspect.get("localizedAspectName", "").strip()
        if name and name not in seen:
            columns.append(f"C:{name}")
            seen.add(name)

    columns.sort()
    logger.info("[Taxonomy] [OK] category_id=%s -> %d aspect columns.", category_id, len(columns))
    return columns
