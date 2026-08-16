"""
inventory_ingester.py — Standalone WNC Parts Slingers CSV-to-Inventory Sync Utility.

Features:
- Windows 11 Dark Mode UI matching WNC Parts Slingers aesthetics.
- Multi-CSV selection dialog.
- Parses eBay Motors CSV exports (MPN, Brand, Title, Description, Category, StartPrice, CustomLabel, PicURL, etc.).
- Upserts rows into D:\\WNC_Archive\\data\\inventory.db & D:\\Coding_Projects_002\\WNC_Take_3\\app_data.db.
- Prevents duplicates and logs detailed import stats.
"""

import sys
import os
import csv
import sqlite3
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QColor, QBrush
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QPlainTextEdit,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QHeaderView,
)

INV_DB_PATH = Path(r"D:\WNC_Archive\data\inventory_(listed-thru-eBay).db")
APP_DB_PATH = Path(r"D:\Coding_Projects_002\WNC_Take_3\app_data_(catalog-lookup).db")


class IngestWorker(QThread):
    progress = Signal(int, int)
    log_msg = Signal(str)
    completed = Signal(int, int, list)
    error_occurred = Signal(str)

    def __init__(self, csv_filepaths: list[str]):
        super().__init__()
        self.csv_filepaths = csv_filepaths

    def run(self):
        total_inserted = 0
        total_updated = 0
        imported_rows_summary = []

        try:
            conn_inv = sqlite3.connect(INV_DB_PATH)
            conn_inv.row_factory = sqlite3.Row
            cur_inv = conn_inv.cursor()

            conn_app = None
            if APP_DB_PATH.exists():
                try:
                    conn_app = sqlite3.connect(APP_DB_PATH)
                    cur_app = conn_app.cursor()
                except Exception as e:
                    self.log_msg.emit(f"⚠️ Warning: Could not lock app_data.db: {e}")

            for f_idx, csv_path in enumerate(self.csv_filepaths):
                self.log_msg.emit(f"\n📂 Processing file [{f_idx+1}/{len(self.csv_filepaths)}]: {Path(csv_path).name}")

                with open(csv_path, "r", encoding="utf-8-sig", errors="ignore") as fh:
                    reader = csv.DictReader(fh)
                    rows = list(reader)

                total_in_file = len(rows)
                for r_idx, row in enumerate(rows):
                    mpn = str(row.get("MPN", "")).strip()
                    custom_label = str(row.get("CustomLabel", "")).strip()

                    if not mpn and custom_label:
                        mpn = custom_label.replace("-1", "").strip()

                    if not mpn:
                        self.log_msg.emit(f" ⚠️ Row {r_idx+1}: Skipped (Missing MPN and CustomLabel)")
                        continue

                    brand = str(row.get("Brand", "")).strip() or str(row.get("C:Brand", "")).strip() or "Dorman"
                    title = str(row.get("Title", "")).strip()
                    description = str(row.get("Description", "")).strip()
                    category_id = str(row.get("Category", "")).strip()
                    price_str = str(row.get("StartPrice", "")).strip()
                    quantity_str = str(row.get("Quantity", "1")).strip()
                    pic_url = str(row.get("PicURL", "")).strip()

                    try:
                        price = float(price_str) if price_str else 0.0
                    except ValueError:
                        price = 0.0

                    try:
                        quantity = int(quantity_str) if quantity_str else 1
                    except ValueError:
                        quantity = 1

                    cur_inv.execute("SELECT rowid, pic_urls FROM inventory_items WHERE mpn = ? OR custom_label = ?;", (mpn, custom_label))
                    existing = cur_inv.fetchone()

                    if existing:
                        rowid = existing["rowid"]
                        cur_inv.execute("""
                            UPDATE inventory_items 
                            SET brand = ?, title = ?, description = ?, category_id = ?, price = ?, quantity = ?, custom_label = ?, pic_urls = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE rowid = ?;
                        """, (brand, title, description, category_id, price, quantity, custom_label, pic_url, rowid))
                        total_updated += 1
                        action_type = "Updated"
                    else:
                        cur_inv.execute("""
                            INSERT INTO inventory_items (mpn, brand, title, description, category_id, price, quantity, custom_label, pic_urls)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                        """, (mpn, brand, title, description, category_id, price, quantity, custom_label, pic_url))
                        total_inserted += 1
                        action_type = "Inserted"

                    if conn_app:
                        try:
                            cur_app.execute("""
                                INSERT OR REPLACE INTO parts (mpn, brand, title, description, category_id, price, quantity, custom_label, pic_urls)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                            """, (mpn, brand, title, description, category_id, price, quantity, custom_label, pic_url))
                        except Exception:
                            pass

                    imported_rows_summary.append({
                        "action": action_type,
                        "mpn": mpn,
                        "brand": brand,
                        "title": title,
                        "price": f"${price:.2f}",
                        "pic_url": pic_url
                    })

                    self.log_msg.emit(f" [{action_type}] MPN: {mpn:12} | Title: {title[:45]}...")
                    self.progress.emit(r_idx + 1, total_in_file)

            conn_inv.commit()
            conn_inv.close()

            if conn_app:
                conn_app.commit()
                conn_app.close()

            self.completed.emit(total_inserted, total_updated, imported_rows_summary)

        except Exception as e:
            self.error_occurred.emit(str(e))


class IngesterMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WNC Parts Slingers — Inventory CSV Sync Utility")
        self.setMinimumSize(950, 650)
        self.selected_files = []

        self._build_ui()
        self._apply_stylesheet()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title_lbl = QLabel("📦 WNC Inventory DB Ingester")
        title_lbl.setFont(QFont("Segoe UI", 14, QFont.Bold))
        header.addWidget(title_lbl)

        header.addStretch()

        self.db_status_lbl = QLabel(f"Target DB: D:\\WNC_Archive\\data\\inventory.db")
        self.db_status_lbl.setStyleSheet("color: #03DAC6; font-size: 11px; font-weight: bold;")
        header.addWidget(self.db_status_lbl)

        layout.addLayout(header)

        # File Selection Bar
        file_bar = QHBoxLayout()
        self.select_btn = QPushButton("📁 Select eBay Listing CSV(s)...")
        self.select_btn.setMinimumHeight(38)
        self.select_btn.clicked.connect(self._on_select_files)
        file_bar.addWidget(self.select_btn)

        self.files_lbl = QLabel("No CSV files selected.")
        self.files_lbl.setStyleSheet("color: #AAAAAA; font-style: italic;")
        file_bar.addWidget(self.files_lbl, stretch=1)

        self.ingest_btn = QPushButton("⚡ Import CSV Data into Inventory DB")
        self.ingest_btn.setMinimumHeight(38)
        self.ingest_btn.setEnabled(False)
        self.ingest_btn.setStyleSheet("background-color: #1B5E20; color: #FFFFFF; font-weight: bold;")
        self.ingest_btn.clicked.connect(self._on_start_ingest)
        file_bar.addWidget(self.ingest_btn)

        layout.addLayout(file_bar)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        layout.addWidget(self.progress_bar)

        # Table & Log Splitter
        main_h_layout = QHBoxLayout()

        # Left Table Preview
        self.summary_table = QTableWidget()
        self.summary_table.setColumnCount(5)
        self.summary_table.setHorizontalHeaderLabels(["Action", "MPN", "Brand", "Title", "Price"])
        self.summary_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.summary_table.setEditTriggers(QTableWidget.NoEditTriggers)
        main_h_layout.addWidget(self.summary_table, stretch=2)

        # Right Log View
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFont(QFont("Consolas", 9))
        main_h_layout.addWidget(self.log_view, stretch=1)

        layout.addLayout(main_h_layout, stretch=1)

    def _apply_stylesheet(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #121212;
                color: #E0E0E0;
                font-family: 'Segoe UI', sans-serif;
            }
            QPushButton {
                background-color: #1E1E1E;
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 6px 14px;
                color: #FFFFFF;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2A2A2A;
                border-color: #03DAC6;
            }
            QPushButton:disabled {
                background-color: #1A1A1A;
                color: #555555;
                border-color: #222222;
            }
            QPlainTextEdit {
                background-color: #0A0A0A;
                border: 1px solid #252525;
                color: #00FF66;
            }
            QTableWidget {
                background-color: #181818;
                gridline-color: #2A2A2A;
                color: #E0E0E0;
            }
            QHeaderView::section {
                background-color: #222222;
                color: #03DAC6;
                padding: 4px;
                font-weight: bold;
                border: 1px solid #2A2A2A;
            }
            QProgressBar {
                background-color: #1E1E1E;
                border: none;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background-color: #03DAC6;
            }
        """)

    def _on_select_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Generated eBay Listing CSVs",
            os.path.expanduser("~/Downloads"),
            "CSV Files (*.csv);;All Files (*)",
        )
        if files:
            self.selected_files = files
            names = ", ".join([Path(f).name for f in files])
            self.files_lbl.setText(f"{len(files)} file(s) selected: {names}")
            self.ingest_btn.setEnabled(True)
            self.log_view.appendPlainText(f"Selected {len(files)} CSV file(s) for import:\n " + "\n ".join(files))

    def _on_start_ingest(self):
        if not self.selected_files:
            return

        self.select_btn.setEnabled(False)
        self.ingest_btn.setEnabled(False)
        self.log_view.appendPlainText("\n🚀 Starting DB Import...")

        self.worker = IngestWorker(self.selected_files)
        self.worker.progress.connect(self._on_progress)
        self.worker.log_msg.connect(self._on_log)
        self.worker.completed.connect(self._on_completed)
        self.worker.error_occurred.connect(self._on_error)
        self.worker.start()

    def _on_progress(self, current, total):
        pct = int((current / total) * 100)
        self.progress_bar.setValue(pct)

    def _on_log(self, msg):
        self.log_view.appendPlainText(msg)

    def _on_completed(self, inserted, updated, rows_summary):
        self.select_btn.setEnabled(True)
        self.ingest_btn.setEnabled(True)
        self.progress_bar.setValue(100)

        self.summary_table.setRowCount(len(rows_summary))
        for r_idx, row in enumerate(rows_summary):
            item_action = QTableWidgetItem(row["action"])
            item_action.setForeground(QBrush(QColor("#03DAC6") if row["action"] == "Inserted" else QColor("#FF9800")))
            
            self.summary_table.setItem(r_idx, 0, item_action)
            self.summary_table.setItem(r_idx, 1, QTableWidgetItem(row["mpn"]))
            self.summary_table.setItem(r_idx, 2, QTableWidgetItem(row["brand"]))
            self.summary_table.setItem(r_idx, 3, QTableWidgetItem(row["title"]))
            self.summary_table.setItem(r_idx, 4, QTableWidgetItem(row["price"]))

        msg = f"🎉 Import Successful!\n\nNew Parts Inserted: {inserted}\nExisting Parts Updated: {updated}\n\nMaster Inventory DB is up-to-date."
        self.log_view.appendPlainText(f"\n✅ {msg}")
        QMessageBox.information(self, "CSV Ingestion Complete", msg)

    def _on_error(self, err_msg):
        self.select_btn.setEnabled(True)
        self.ingest_btn.setEnabled(True)
        QMessageBox.critical(self, "Import Error", f"Failed to import CSV:\n\n{err_msg}")


def main():
    app = QApplication(sys.argv)
    window = IngesterMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
