"""
ai_engine.py — Gemini 3.5 Flash listing title and HTML description generator.

Sends scraped product data to the Gemini 3.5 Flash model and parses
a structured JSON response containing:
  - title          : eBay listing title (≤80 characters)
  - description_html : Clean, eBay-compatible HTML description block

Falls back to rule-based construction if the API call fails so the
pipeline never stalls on a single bad Gemini response.
"""

import logging
import os
import time

from pydantic import BaseModel, Field

import google.genai as genai
from google.genai import types as genai_types

logger = logging.getLogger(__name__)

_MODEL_NAME = "gemini-3.5-flash"
_client: genai.Client | None = None   # Lazy singleton


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "GEMINI_API_KEY is not set in .env. "
                "Add it before running the pipeline."
            )
        _client = genai.Client(api_key=api_key)
        logger.info("[AI] Gemini client initialised (model: %s).", _MODEL_NAME)
    return _client


_PROMPT = """\
You are an expert automotive eBay listing assistant.
Below is the raw data for Dorman/Help part number {mpn}.

Raw Data
--------
Brand              : {brand}
Product Header     : {product_header}
Category / SubType : {subtype}
Scraped Specs      : {spec_text}

Task
----
1. Write an eBay Listing TITLE that is STRICTLY UNDER 80 CHARACTERS.
   Use this exact format (no deviations):
   [Brand] [Part Description] [MPN] [1-2 Key Technical Specs]
   Example: "Dorman Window Crank Handle 76970 Chrome OEM-Style Replacement"

2. Write a clean HTML DESCRIPTION block using standard black font.
   Include:
   a) A short introductory paragraph (2-3 sentences) describing what
      the part does and why it matters to the vehicle owner.
   b) An HTML bulleted list (<ul><li>…</li></ul>) listing the key
      technical attributes, dimensions, and fitment notes extracted
      from the scraped specs. If specs are unavailable, use only the
      known brand, part number, and category data.
   Rules: No external CSS. No JavaScript. No inline style attributes
   other than color:#000000 if needed. Keep markup eBay-compatible.

Return ONLY this exact JSON object — no prose, no code fences:
{{"title": "YOUR TITLE (max 80 chars)", "description_html": "<p>…</p><ul><li>…</li></ul>"}}
"""


class eBayListing(BaseModel):
    title: str = Field(
        description="eBay listing title, strictly under 80 characters"
    )
    description_html: str = Field(
        description="Clean HTML listing description block using standard black font"
    )


def _append_fitment_and_oe(description_html: str, scraped_data: dict) -> str:
    """Appends structured HTML sections for Interchange numbers and Compatibility table."""
    interchanges = scraped_data.get("interchange_numbers", [])
    interchange_html = ""
    if interchanges:
        interchange_html = (
            "<br/><h3>Interchange / Cross Reference Part Numbers</h3>"
            "<p>This part directly replaces or is cross-referenced with the following part numbers:</p>"
            "<ul>"
            + "".join(f"<li>{num}</li>" for num in interchanges) +
            "</ul>"
        )

    compatibility = scraped_data.get("compatibility", [])
    fitment_html = ""
    if compatibility:
        fitment_html = (
            "<br/><h3>Vehicle Fitment / Compatibility</h3>"
            "<table border='1' cellpadding='5' style='border-collapse:collapse; width:100%; max-width:800px; color:#000000; font-family:sans-serif; font-size:13px;'>"
            "<tr style='background-color:#f2f2f2; text-align:left;'>"
            "<th>Year</th><th>Make</th><th>Model</th><th>Position</th><th>Notes</th>"
            "</tr>"
        )
        for fit in compatibility:
            fitment_html += (
                f"<tr>"
                f"<td>{fit.get('Year', 'N/A')}</td>"
                f"<td>{fit.get('Make', 'N/A')}</td>"
                f"<td>{fit.get('Model', 'N/A')}</td>"
                f"<td>{fit.get('Position', 'N/A')}</td>"
                f"<td>{fit.get('Notes', 'N/A')}</td>"
                f"</tr>"
            )
        fitment_html += "</table>"

    return f"{description_html}{interchange_html}{fitment_html}"


def _rule_based_fallback(part_data: dict, scraped_data: dict) -> dict:
    """Construct a minimal listing without the AI when Gemini is unavailable."""
    mpn     = part_data.get("mpn", "")
    brand   = part_data.get("brand", "Dorman/Help")
    subtype = part_data.get("subtype", "Auto Part")
    title   = f"{brand} {subtype} {mpn}"[:80]
    html    = (
        f'<p style="color:#000000;"><b>{brand} {subtype} — Part# {mpn}</b><br/>'
        f"Genuine Dorman/Help replacement component. "
        f"Designed for direct OEM fitment.</p>"
        f"<ul>"
        f"<li>Brand: {brand}</li>"
        f"<li>Manufacturer Part Number: {mpn}</li>"
        f"<li>Category: {subtype}</li>"
        f"</ul>"
    )
    html = _append_fitment_and_oe(html, scraped_data)
    return {"title": title, "description_html": html}


def generate_listing(part_data: dict, scraped_data: dict, log_callback=None) -> dict:
    """
    Call Gemini 1.5 Pro to generate a title and HTML description for one part.
    Returns a dict with keys: title (str), description_html (str).
    Never raises — falls back to rule-based construction on any failure.
    """
    def _log(msg: str) -> None:
        if log_callback:
            log_callback(msg)
        logger.info(msg)

    mpn     = part_data.get("mpn", "")
    brand   = part_data.get("brand", "Dorman/Help")
    subtype = part_data.get("subtype", "")

    prompt = _PROMPT.format(
        mpn=mpn,
        brand=brand,
        product_header=scraped_data.get("product_header", "N/A"),
        spec_text=scraped_data.get("spec_text", "N/A"),
        subtype=subtype,
    )

    _log(f"[AI] Generating listing for {mpn} via Gemini 3.5 Flash...")

    client = _get_client()
    config = genai_types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=eBayListing,
    )

    success = False
    response = None
    
    # Retry loop for 503/429 errors
    max_attempts = 3
    sleep_times = [2, 4, 8]
    
    for attempt in range(max_attempts):
        try:
            response = client.models.generate_content(
                model=_MODEL_NAME,
                contents=prompt,
                config=config,
            )
            success = True
            break
        except Exception as exc:
            err_str = str(exc).lower()
            if "503" in err_str or "429" in err_str or "quota" in err_str or "unavailable" in err_str:
                if attempt < max_attempts - 1:
                    sleep_time = sleep_times[attempt]
                    _log(f"[AI] ⚠ API rate limited or unavailable (503/429). Retrying in {sleep_time}s (Attempt {attempt+1}/{max_attempts})...")
                    time.sleep(sleep_time)
                else:
                    _log(f"[AI] ⚠ Max retries reached for {_MODEL_NAME}.")
            else:
                _log(f"[AI] ⚠ Unexpected Gemini error for {mpn}: {exc}")
                break

    # Fallback to gemini-2.5-flash if primary model failed
    if not success:
        _log(f"[AI] ⚠ Primary model failed. Attempting fallback request with gemini-2.5-flash...")
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=config,
            )
            success = True
        except Exception as exc:
            _log(f"[AI] ⚠ Fallback model also failed: {exc}")

    # Final rule-based fallback if all AI requests failed
    if not success or not response:
        _log(f"[AI] ⚠ All AI attempts exhausted for {mpn}. Using rule-based fallback.")
        return _rule_based_fallback(part_data, scraped_data)

    try:
        listing  = eBayListing.model_validate_json(response.text)
        title    = listing.title[:80]
        description_html = _append_fitment_and_oe(listing.description_html, scraped_data)

        if not title:
            raise ValueError("Gemini returned an empty title field.")

        _log(f"[AI] Title: {title!r} ({len(title)} chars)")
        return {"title": title, "description_html": description_html}

    except Exception as exc:
        _log(f"[AI] ⚠ JSON parsing failed for {mpn}: {exc}. Using rule-based fallback.")
        return _rule_based_fallback(part_data, scraped_data)
