import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load Env
_ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(_ENV_PATH)

# Set logging
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("test_pipeline")

from app import db_manager, csv_builder
from app.dorman_scraper import scrape_part
from app.ai_engine import generate_listing
from app.ebay_taxonomy import get_aspects_for_category
from app.ebay_auth import get_token

def run_test():
    mpn = "76916"
    logger.info(f"Initializing database...")
    db_manager.init_database()
    
    logger.info(f"Looking up part {mpn} in local SQLite index...")
    parts = db_manager.lookup_parts([mpn])
    if not parts:
        logger.error(f"Part {mpn} not found in database!")
        return
    part = parts[0]
    logger.info(f"Found part: {part}")
    
    # Try eBay OAuth & Taxonomy
    logger.info("Authenticating with eBay API...")
    aspects = []
    try:
        get_token()
        cat_id = part["category_id"]
        logger.info(f"Fetching aspects for CategoryID {cat_id}...")
        aspects = get_aspects_for_category(cat_id)
        logger.info(f"Fetched {len(aspects)} aspects.")
    except Exception as e:
        logger.warning(f"eBay OAuth or Taxonomy failed: {e}. Running without aspects.")
        # Mock standard aspects for test verification
        aspects = ["C:Brand", "C:Manufacturer Part Number", "C:Color", "C:Material", "C:Interchange Part Number"]
    
    # Run Scraper
    logger.info(f"Running scraper for MPN: {mpn}...")
    scraped = scrape_part(
        mpn,
        brand=part.get("brand", ""),
        subtype=part.get("subtype", "")
    )
    logger.info("Scraper completed successfully.")
    
    # Run AI listing generation
    logger.info("Running Gemini AI listing generation...")
    listing = generate_listing(part, scraped)
    logger.info(f"Listing Title: {listing['title']}")
    logger.info(f"Listing Description HTML snippet: {listing['description_html'][:300]}...")
    
    # Build CSV
    logger.info("Assembling CSV listing row...")
    enriched_part = {
        "part_data": part,
        "listing": listing,
        "pic_url": "http://cloudinary.com/test.jpg",
        "aspects": aspects,
        "scraped_data": scraped,
    }
    
    csv_bytes = csv_builder.build_csv([enriched_part])
    csv_text = csv_bytes.decode("utf-8-sig")
    
    print("\n" + "="*40 + "\nGENERATED CSV PREVIEW\n" + "="*40)
    lines = csv_text.splitlines()
    if len(lines) >= 2:
        headers = lines[0].split(",")
        values = lines[1].split(",")
        for h, v in zip(headers, values):
            if v.strip() or h in ["Action", "Category", "Title", "Brand", "CustomLabel"]:
                print(f"{h}: {v}")
    print("="*40)

if __name__ == "__main__":
    run_test()
