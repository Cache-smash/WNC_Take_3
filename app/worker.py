"""
worker.py — QThread pipeline orchestrator.

Runs all four pipeline phases off the Qt main thread so the UI stays
responsive during long-running network and AI operations.

Signals
-------
log_signal      (str)   → append a line to the status log widget
finished_signal (bytes) → CSV bytes ready for download
error_signal    (str)   → fatal error; pipeline aborted
"""

import logging

from PySide6.QtCore import QThread, Signal

from . import csv_builder, db_manager
from .ai_engine import generate_listing
from .cloudinary_uploader import upload_images_for_part
from .dorman_scraper import scrape_part
from .ebay_auth import get_token
from .ebay_taxonomy import get_aspects_for_category

logger = logging.getLogger(__name__)


class PipelineWorker(QThread):
    log_signal:      Signal = Signal(str)
    finished_signal: Signal = Signal(bytes)
    error_signal:    Signal = Signal(str)

    def __init__(self, mpn_list: list[str]) -> None:
        super().__init__()
        self.mpn_list = mpn_list

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _log(self, msg: str) -> None:
        self.log_signal.emit(msg)
        logger.info(msg)

    # ------------------------------------------------------------------
    # QThread entry point
    # ------------------------------------------------------------------

    def run(self) -> None:
        try:
            self._execute_pipeline()
        except Exception as exc:
            logger.exception("Unhandled pipeline error")
            self.error_signal.emit(str(exc))

    # ------------------------------------------------------------------
    # Pipeline phases
    # ------------------------------------------------------------------

    def _execute_pipeline(self) -> None:
        mpns = self.mpn_list
        self._log(
            f"[Pipeline] ── Starting batch for {len(mpns)} part(s): "
            f"{', '.join(mpns)} ──"
        )

        # ── Phase A: Database lookup ──────────────────────────────────
        self._log("[Phase A] Querying local SQLite index...")
        parts = db_manager.lookup_parts(mpns)

        found_mpns = {p["mpn"] for p in parts}
        for mpn in mpns:
            if mpn not in found_mpns:
                self._log(f"[Phase A] ⚠ '{mpn}' not found in database. Skipping.")

        if not parts:
            self.error_signal.emit(
                "None of the entered part numbers were found in the local database.\n"
                "Verify the part numbers are valid Dorman/Help MPNs."
            )
            return

        for p in parts:
            self._log(
                f"[Phase A] ✓ {p['mpn']} → ePID: {p['epid']}  "
                f"CategoryID: {p['category_id']}  Brand: {p['brand']}"
            )

        # ── Phase B: eBay OAuth + Taxonomy ───────────────────────────
        self._log("[Phase B] Authenticating with eBay Production API...")
        ebay_authenticated = False
        try:
            get_token()
            ebay_authenticated = True
            self._log("[Phase B] ✓ OAuth token obtained.")
        except Exception as exc:
            self._log(
                f"[Phase B] ⚠ eBay auth failed: {exc}. "
                f"Taxonomy skipped — C: columns will be omitted from this batch."
            )

        unique_cat_ids = sorted({p["category_id"] for p in parts})
        category_aspects: dict[str, list[str]] = {}

        if not ebay_authenticated:
            # Pre-populate every category with an empty list so downstream
            # code never KeyErrors when auth was unavailable.
            for cat_id in unique_cat_ids:
                category_aspects[cat_id] = []
        else:
            for cat_id in unique_cat_ids:
                self._log(f"[Phase B] Fetching aspects for CategoryID {cat_id}...")
                try:
                    aspects = get_aspects_for_category(cat_id)
                    category_aspects[cat_id] = aspects
                    self._log(
                        f"[Phase B] ✓ CategoryID {cat_id} → {len(aspects)} C: columns."
                    )
                except Exception as exc:
                    self._log(
                        f"[Phase B] ⚠ Taxonomy fetch failed for {cat_id}: {exc}. "
                        f"Continuing without aspects."
                    )
                    category_aspects[cat_id] = []

        # ── Phases C + D: Per-part enrichment ────────────────────────
        enriched_parts: list[dict] = []

        for part in parts:
            mpn = part["mpn"]
            self._log(f"\n[Part {mpn}] ─────── Enrichment starting ───────")

            # Phase C — Cloudinary image upload
            self._log(f"[Phase C] Processing images for {mpn}...")
            pic_url = upload_images_for_part(mpn, self._log)

            # Phase D — Scrape Dorman product page
            scraped = scrape_part(mpn, self._log)

            # Phase D — Gemini listing generation
            listing = generate_listing(part, scraped, self._log)

            enriched_parts.append(
                {
                    "part_data": part,
                    "listing":   listing,
                    "pic_url":   pic_url,
                    "aspects":   category_aspects.get(part["category_id"], []),
                    "scraped_data": scraped,
                }
            )
            self._log(f"[Part {mpn}] ✓ Enrichment complete.")

        # ── Phase E: CSV assembly ─────────────────────────────────────
        self._log("\n[Phase E] Assembling eBay CSV file...")
        csv_bytes = csv_builder.build_csv(enriched_parts)
        self._log(
            f"[Phase E] ✓ CSV ready — {len(enriched_parts)} listing row(s) "
            f"across {len({p['part_data']['category_id'] for p in enriched_parts})} "
            f"unique eBay categories."
        )

        self.finished_signal.emit(csv_bytes)
