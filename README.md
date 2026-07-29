# WNC Parts Slingers - Automated eBay CSV Generator

This application is a highly customized, robust e-commerce pipeline built for WNC Parts Slingers. It transforms raw lists of Manufacturer Part Numbers (MPNs) into fully formatted, bulk-uploadable eBay CSV templates using web scraping and Google Gemini AI.

## 🚀 How to Run the Application

To launch the graphical interface and start the pipeline, open your terminal (PowerShell) in the root project directory and execute the following command:

```bash
.venv\Scripts\python.exe main.py
```

*Note: You must run this via the `.venv` executable to ensure all isolated Python dependencies (PySide6, BeautifulSoup, Google GenAI SDK, etc.) are correctly loaded.*

## ⚙️ Prerequisites & Environment Setup

Before running the application, ensure your local environment contains a `.env` file in the root directory with the following API credentials:

```env
GEMINI_API_KEY=your_google_ai_studio_api_key
CLOUDINARY_URL=cloudinary://your_api_key:your_api_secret@your_cloud_name
```

## 🏗️ Architecture & Pipeline Flow

The application executes in a strict, asynchronous pipeline to ensure UI responsiveness and graceful error handling:

1. **Database Ingestion (Phase A):** Checks the local `app_data.db` SQLite database to retrieve internal tracking IDs, pricing, and quantities for the provided MPNs.
2. **Taxonomy & Category Mapping (Phase B):** Automatically queries the eBay Taxonomy API (if configured) or relies on fallback categories to establish item specifics requirements.
3. **Web Scraping (Phase C):** Queries `PartCatalog.com` to scrape exact fitment specs, descriptions, and OEM interchange numbers. Implements strict rate-limiting (2s) and robust 404/fallback handling.
4. **AI Generation (Phase D):** Feeds scraped specifications into **Gemini 3.5 Flash** (with exponential backoff and automatic 2.5 Flash fallbacks for 503/429 errors). The AI generates strict 80-character optimized titles and clean HTML description blocks via structured Pydantic JSON schemas.
5. **Image Processing (Phase E):** Scans the local `images/` directory and uploads matching `.jpg` files to Cloudinary, generating permanent, secure URLs for eBay hosting.
6. **CSV Compilation (Phase F):** Aggregates all data into a fully compliant, 19-column eBay File Exchange CSV (including WNC business policies like Free Shipping and 30-Day Returns).

## 🛡️ Key Features & Failsafes

*   **Dark Mode UI:** A premium, automotive-styled PyQt6 interface optimized for Windows 11.
*   **Zero-Crash Architecture:** If web scrapers, Cloudinary, or Gemini APIs fail, the pipeline falls back to rule-based generation (e.g., `"Dorman Auto Part {mpn}"`) rather than halting the batch.
*   **Duplicate Handling:** Input text boxes automatically strip whitespace, deduplicate part numbers, and cap batches at 15 items per run to prevent timeout bloat.
*   **Custom Labels (SKUs):** Automatically maps parts to the `{mpn}-1` SKU format required by internal systems.
