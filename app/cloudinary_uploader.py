"""
cloudinary_uploader.py — Scan photo_input/ and upload matched images.

Searches the project-local photo_input/ directory for files that match
the pattern  {mpn}_<sequence>.(jpg|jpeg|png)  for a given part number.
Uploads each file (max 24) to Cloudinary with a smart-crop transformation
and returns the secure HTTPS URLs concatenated with pipe ( | ) separators.
"""

import logging
import os
import re
from pathlib import Path

import cloudinary
import cloudinary.uploader

logger = logging.getLogger(__name__)

PHOTO_DIR   = Path(__file__).parent.parent / "photo_input"
MAX_IMAGES  = 24

# Cloudinary smart-crop transformation applied to every upload
_TRANSFORM = [
    {
        "gravity": "auto",
        "crop":    "fill",
        "width":   1600,
        "height":  1200,
        "quality": "auto:best",
        "fetch_format": "auto",
    }
]


def _configure() -> None:
    cloudinary.config(
        cloud_name=os.environ["CLOUDINARY_CLOUD_NAME"],
        api_key=   os.environ["CLOUDINARY_API_KEY"],
        api_secret=os.environ["CLOUDINARY_API_SECRET"],
        secure=True,
    )


def upload_images_for_part(mpn: str, log_callback=None) -> str:
    """
    Scan photo_input/ for images belonging to `mpn`, upload them to
    Cloudinary, and return a pipe-separated string of secure URLs.
    Returns an empty string if no matching files are found.
    """
    def _log(msg: str) -> None:
        if log_callback:
            log_callback(msg)
        logger.info(msg)

    _configure()

    pattern = re.compile(rf"^{re.escape(mpn)}_\d+\.(jpg|jpeg|png)$", re.IGNORECASE)
    candidates = sorted(
        [f for f in PHOTO_DIR.iterdir() if pattern.match(f.name)]
    )[:MAX_IMAGES]

    if not candidates:
        _log(f"[Images] No images found for {mpn} in photo_input/ — skipping.")
        return ""

    _log(f"[Images] Found {len(candidates)} image(s) for {mpn}. Uploading to Cloudinary...")

    urls: list[str] = []
    for img in candidates:
        try:
            result = cloudinary.uploader.upload(
                str(img),
                public_id=f"wnc_parts/{mpn}/{img.stem}",
                overwrite=True,
                transformation=_TRANSFORM,
            )
            url = result.get("secure_url", "")
            if url:
                urls.append(url)
                _log(f"[Images]   ✓ {img.name} → {url}")
        except Exception as exc:
            _log(f"[Images]   ⚠ Failed to upload {img.name}: {exc}")

    return "|".join(urls)
