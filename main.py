"""
main.py — Application entry point.

Start-up sequence
-----------------
1. Load .env from project root into os.environ
2. Configure root logger
3. Initialize SQLite database (ingests TSV on first run only)
4. Launch PySide6 QApplication + MainWindow
"""

import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

# ── Load .env before any module-level os.environ reads ────────────────────
_ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(_ENV_PATH)

# ── Logging ───────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)-8s]  %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("main")

# ── Qt + App imports (after env is loaded) ────────────────────────────────
from PySide6.QtWidgets import QApplication, QMessageBox  # noqa: E402

from app import db_manager                               # noqa: E402
from app.ui.main_window import MainWindow                # noqa: E402


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("WNC eBay Motors CSV Generator")
    app.setOrganizationName("WNC Parts Slingers")

    # ── Phase 0: SQLite initialisation (runs in main thread at startup) ──
    logger.info("Checking local database...")
    try:
        db_manager.init_database()
    except FileNotFoundError as exc:
        QMessageBox.critical(
            None,
            "Catalog File Missing",
            f"{exc}\n\nEnsure US_Parts_Catalog_Dorman_Help.tsv is in the project root.",
        )
        sys.exit(1)
    except Exception as exc:
        QMessageBox.critical(
            None,
            "Database Initialization Error",
            f"Failed to build local database:\n\n{exc}",
        )
        sys.exit(1)

    logger.info("Database ready. Launching UI...")
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
