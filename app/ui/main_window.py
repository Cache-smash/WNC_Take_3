"""
main_window.py — PySide6 Main Window (baseline layout; pre-styling pass).

Layout
------
┌─────────────────────────────────────────────────────────────┐
│  Title Bar: "WNC Parts Slingers — eBay Motors CSV Generator"│
├──────────────────────┬──────────────────────────────────────┤
│  LEFT PANEL          │  RIGHT PANEL                         │
│  • Part # label      │  • Status Log label                  │
│  • QPlainTextEdit    │  • QPlainTextEdit (read-only mono)   │
│    (input, max 15)   │                                      │
│  • [Process Parts]   │                                      │
├──────────────────────┴──────────────────────────────────────┤
│  [⬇ Download CSV]  (disabled until pipeline completes)      │
└─────────────────────────────────────────────────────────────┘
"""

import logging

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QBrush, QTextCursor
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..worker import PipelineWorker
from .pricing_tab import PricingTabWidget

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("WNC Parts Slingers — eBay Motors Suite")
        self.setMinimumSize(1050, 680)

        self._csv_bytes: bytes | None    = None
        self._worker: PipelineWorker | None = None

        self._build_ui()
        self._apply_stylesheet()

    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(12)

        # ── App Title & Header Controls ───────────────────────────────
        header_bar = QHBoxLayout()
        title_lbl = QLabel("WNC Parts Slingers — E-Commerce Suite")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_lbl.setFont(title_font)
        header_bar.addWidget(title_lbl)

        header_bar.addStretch()

        # Shipping Policy Selector Dropdown (3 Business Profiles)
        ship_lbl = QLabel("Active Shipping Policy:")
        ship_lbl.setFont(QFont("Segoe UI", 9, QFont.Bold))
        header_bar.addWidget(ship_lbl)

        self.shipping_policy_combo = QComboBox()
        self.shipping_policy_combo.addItems([
            "Free Shipping",
            "Calculated Shipping (USPS Ground)",
            "Flat Rate $4.25 Shipping",
        ])
        self.shipping_policy_combo.setToolTip("Select the default eBay Shipping Business Policy profile for CSV exports.")
        header_bar.addWidget(self.shipping_policy_combo)

        root.addLayout(header_bar)

        # ── Main Tab Widget ───────────────────────────────────────────
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #333333;
                background-color: #121212;
            }
            QTabBar::tab {
                background: #1E1E1E;
                color: #B0B0B0;
                padding: 8px 16px;
                font-weight: bold;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #2D2D2D;
                color: #03DAC6;
                border-bottom: 2px solid #03DAC6;
            }
        """)

        # ── TAB 1: CSV Listing Generator (Original App) ───────────────
        tab1 = QWidget()
        t1_layout = QVBoxLayout(tab1)
        t1_layout.setContentsMargins(10, 10, 10, 10)
        t1_layout.setSpacing(10)

        sub_lbl = QLabel(
            "Enter up to 15 Dorman/Help part numbers and click Process to generate your listing CSV."
        )
        sub_lbl.setWordWrap(True)
        t1_layout.addWidget(sub_lbl)

        splitter = QSplitter(Qt.Horizontal)

        # Left panel — part number input & Terapeak helper
        left_widget = QWidget()
        left = QVBoxLayout(left_widget)
        left.setContentsMargins(0, 0, 8, 0)
        left.setSpacing(8)

        input_lbl = QLabel("Part Numbers (one per line, max 15):")
        input_lbl.setFont(QFont("Segoe UI", 9, QFont.Bold))
        left.addWidget(input_lbl)

        self.part_input = QPlainTextEdit()
        self.part_input.setPlaceholderText("e.g.\n61103\n61105\n61108\n76970")
        self.part_input.setMinimumHeight(100)
        self.part_input.setMaximumHeight(130)
        self.part_input.textChanged.connect(self._on_part_input_changed)
        left.addWidget(self.part_input)

        # Terapeak Price Override Table
        terapeak_hdr = QHBoxLayout()
        terapeak_lbl = QLabel("🏷️  Terapeak Price Overrides (Optional):")
        terapeak_lbl.setFont(QFont("Segoe UI", 9, QFont.Bold))
        terapeak_hdr.addWidget(terapeak_lbl)

        self.launch_all_terapeak_btn = QPushButton("🔗  Open Terapeak Tabs")
        self.launch_all_terapeak_btn.setToolTip("Open 3-Year Sold Terapeak research tabs in Chrome for all entered parts")
        self.launch_all_terapeak_btn.setStyleSheet("""
            QPushButton {
                background-color: #1E1E1E;
                color: #03DAC6;
                border: 1px solid #03DAC6;
                padding: 3px 8px;
                font-size: 11px;
                font-weight: bold;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #03DAC6;
                color: #121212;
            }
        """)
        self.launch_all_terapeak_btn.clicked.connect(self._on_launch_all_terapeak)
        terapeak_hdr.addWidget(self.launch_all_terapeak_btn)
        left.addLayout(terapeak_hdr)

        self.terapeak_table = QTableWidget()
        self.terapeak_table.setColumnCount(3)
        self.terapeak_table.setHorizontalHeaderLabels(["Part #", "Terapeak Link", "Avg Sold Price ($)"])
        self.terapeak_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.terapeak_table.setMinimumHeight(180)
        self.terapeak_table.setStyleSheet("""
            QTableWidget {
                background-color: #181818;
                gridline-color: #333333;
                color: #E0E0E0;
                font-size: 11px;
            }
            QHeaderView::section {
                background-color: #222222;
                color: #03DAC6;
                font-weight: bold;
                padding: 4px;
                border: 1px solid #333333;
            }
        """)
        left.addWidget(self.terapeak_table)

        self.process_btn = QPushButton("⚙   Process Parts")
        self.process_btn.setObjectName("primaryBtn")
        self.process_btn.setMinimumHeight(42)
        self.process_btn.setToolTip("Run pipeline: DB lookup → Scrapers → AI → CSV")
        self.process_btn.clicked.connect(self._on_process)
        left.addWidget(self.process_btn)

        left.addStretch()
        splitter.addWidget(left_widget)

        # Right panel — status log
        right_widget = QWidget()
        right = QVBoxLayout(right_widget)
        right.setContentsMargins(8, 0, 0, 0)
        right.setSpacing(6)

        log_lbl = QLabel("Status Log:")
        log_lbl.setFont(QFont("Segoe UI", 9, QFont.Bold))
        right.addWidget(log_lbl)

        self.log_view = QPlainTextEdit()
        self.log_view.setObjectName("statusLog")
        self.log_view.setReadOnly(True)
        mono = QFont("Consolas", 9)
        if not mono.exactMatch():
            mono.setFamily("Courier New")
        self.log_view.setFont(mono)
        right.addWidget(self.log_view)

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        t1_layout.addWidget(splitter, stretch=1)

        # Download Bar for Tab 1
        bottom = QHBoxLayout()
        self.download_btn = QPushButton("⬇   Download CSV")
        self.download_btn.setMinimumHeight(42)
        self.download_btn.setEnabled(False)
        self.download_btn.clicked.connect(self._on_download)
        bottom.addWidget(self.download_btn)

        self.status_lbl = QLabel("Ready.")
        self.status_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        bottom.addWidget(self.status_lbl, stretch=1)

        t1_layout.addLayout(bottom)

        self.tabs.addTab(tab1, "📦   CSV Listing Generator")

        # ── TAB 2: Competitive Pricing Engine ─────────────────────────
        self.pricing_tab = PricingTabWidget()
        self.tabs.addTab(self.pricing_tab, "🏷️   Competitive Pricing Engine")

        # ── TAB 3: Live CSV Data Inspector (Color-Coded) ──────────────
        tab3 = QWidget()
        t3_layout = QVBoxLayout(tab3)
        t3_layout.setContentsMargins(10, 10, 10, 10)
        t3_layout.setSpacing(8)

        t3_lbl = QLabel(
            "<b>Semantic CSV Cell Highlights:</b> "
            "<span style='color: #4CAF50;'>■ Valid / Hosted PicURL / Profitable</span> &nbsp;|&nbsp; "
            "<span style='color: #F44336;'>■ Missing Photo / Low Margin</span> &nbsp;|&nbsp; "
            "<span style='color: #2196F3;'>■ eBay Category / ePID Matched</span> &nbsp;|&nbsp; "
            "<span style='color: #FF9800;'>■ Blank Required Aspect</span>"
        )
        t3_lbl.setWordWrap(True)
        t3_layout.addWidget(t3_lbl)

        self.csv_table = QTableWidget()
        self.csv_table.setAlternatingRowColors(True)
        self.csv_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.csv_table.setStyleSheet("""
            QTableWidget {
                background-color: #121212;
                gridline-color: #333333;
                color: #E0E0E0;
                font-size: 11px;
            }
            QHeaderView::section {
                background-color: #1E1E1E;
                color: #03DAC6;
                font-weight: bold;
                padding: 6px;
                border: 1px solid #333333;
            }
        """)
        t3_layout.addWidget(self.csv_table, stretch=1)
        self.tabs.addTab(tab3, "📊   Live CSV Inspector")

        root.addWidget(self.tabs, stretch=1)


    # ------------------------------------------------------------------
    # Styling
    # ------------------------------------------------------------------

    def _apply_stylesheet(self) -> None:
        self.setStyleSheet("""
            /* Global Background & Typography */
            QMainWindow, QWidget#central {
                background-color: #121212;
                color: #FFFFFF;
                font-family: "Segoe UI", "Helvetica Neue", sans-serif;
            }

            /* Container Panels */
            QSplitter::handle {
                background-color: #333333;
                width: 2px;
            }
            QLabel {
                color: #E0E0E0;
            }

            /* Input Fields (QPlainTextEdit) */
            QPlainTextEdit {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 6px;
                font-size: 13px;
            }
            QPlainTextEdit:focus {
                border: 1px solid #0078D4;
            }

            /* Status Log Specific */
            QPlainTextEdit#statusLog {
                background-color: #0A0A0A;
                color: #A3E635; /* Crisp pale green */
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 8px;
            }

            /* Buttons */
            QPushButton {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: 1px solid #333333;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2D2D2D;
                border: 1px solid #0078D4;
            }
            QPushButton:pressed {
                background-color: #0078D4;
                color: #FFFFFF;
            }
            QPushButton:disabled {
                background-color: #121212;
                color: #666666;
                border: 1px solid #222222;
            }
            
            /* Primary Button overrides */
            QPushButton#primaryBtn {
                background-color: #0078D4;
                color: #FFFFFF;
                border: none;
            }
            QPushButton#primaryBtn:hover {
                background-color: #0086F0;
            }
            QPushButton#primaryBtn:pressed {
                background-color: #005A9E;
            }
            QPushButton#primaryBtn:disabled {
                background-color: #1E1E1E;
                color: #666666;
                border: 1px solid #333333;
            }
        """)

    # ------------------------------------------------------------------
    # Slot implementations
    # ------------------------------------------------------------------

    def _append_log(self, msg: str) -> None:
        self.log_view.appendPlainText(msg)
        self.log_view.moveCursor(QTextCursor.End)

    def _set_status(self, msg: str) -> None:
        self.status_lbl.setText(msg)

    def _on_part_input_changed(self) -> None:
        import webbrowser
        from PySide6.QtWidgets import QLineEdit

        raw = self.part_input.toPlainText().strip()
        mpn_list: list[str] = []
        seen: set[str] = set()
        for line in raw.splitlines():
            mpn = line.strip()
            if mpn and mpn not in seen:
                mpn_list.append(mpn)
                seen.add(mpn)
                if len(mpn_list) == 15:
                    break

        self.terapeak_table.setRowCount(len(mpn_list))
        for r_idx, mpn in enumerate(mpn_list):
            # Column 0: MPN
            item_mpn = QTableWidgetItem(mpn)
            item_mpn.setFlags(Qt.ItemIsEnabled)
            self.terapeak_table.setItem(r_idx, 0, item_mpn)

            # Column 1: Terapeak Link Launch Button
            btn = QPushButton("🔍 Search Terapeak")
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #222222;
                    color: #03DAC6;
                    border: 1px solid #333333;
                    padding: 2px 6px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #03DAC6;
                    color: #121212;
                }
            """)
            import time
            end_ms = int(time.time() * 1000)
            start_ms = end_ms - (3 * 365 * 24 * 60 * 60 * 1000)
            url = f"https://www.ebay.com/sh/research?keywords=dorman+{mpn}&dayRange=1095&startDate={start_ms}&endDate={end_ms}&tabName=SOLD"
            btn.clicked.connect(lambda _, u=url: webbrowser.open(u))
            self.terapeak_table.setCellWidget(r_idx, 1, btn)

            # Column 2: Price Input LineEdit (preserve existing text if present)
            existing_widget = self.terapeak_table.cellWidget(r_idx, 2)
            if not existing_widget or not isinstance(existing_widget, QLineEdit):
                price_edit = QLineEdit()
                price_edit.setPlaceholderText("Auto (Floor)")
                price_edit.setStyleSheet("""
                    QLineEdit {
                        background-color: #0A0A0A;
                        color: #00FF66;
                        border: 1px solid #333333;
                        padding: 2px 4px;
                        font-weight: bold;
                    }
                """)
                self.terapeak_table.setCellWidget(r_idx, 2, price_edit)

    def _on_launch_all_terapeak(self) -> None:
        import webbrowser
        import time
        end_ms = int(time.time() * 1000)
        start_ms = end_ms - (3 * 365 * 24 * 60 * 60 * 1000)
        raw = self.part_input.toPlainText().strip()
        seen: set[str] = set()
        count = 0
        for line in raw.splitlines():
            mpn = line.strip()
            if mpn and mpn not in seen:
                seen.add(mpn)
                url = f"https://www.ebay.com/sh/research?keywords=dorman+{mpn}&dayRange=1095&startDate={start_ms}&endDate={end_ms}&tabName=SOLD"
                webbrowser.open(url)
                count += 1
                if count == 15:
                    break
        if count > 0:
            self._append_log(f"\n🌐 Opened {count} Terapeak research tab(s) in Chrome.")

    def _on_process(self) -> None:
        raw = self.part_input.toPlainText().strip()
        if not raw:
            QMessageBox.warning(self, "Input Required", "Please enter at least one part number.")
            return

        mpn_list: list[str] = []
        seen: set[str] = set()
        for line in raw.splitlines():
            mpn = line.strip()
            if mpn and mpn not in seen:
                mpn_list.append(mpn)
                seen.add(mpn)
                if len(mpn_list) == 15:
                    break

        if self._worker and self._worker.isRunning():
            QMessageBox.warning(
                self, "Pipeline Running",
                "A pipeline is already in progress. Please wait for it to complete."
            )
            return

        # Extract price overrides from Terapeak table
        from PySide6.QtWidgets import QLineEdit
        price_overrides: dict[str, float] = {}
        for r_idx in range(self.terapeak_table.rowCount()):
            mpn_item = self.terapeak_table.item(r_idx, 0)
            price_widget = self.terapeak_table.cellWidget(r_idx, 2)
            if mpn_item and isinstance(price_widget, QLineEdit):
                mpn_val = mpn_item.text().strip()
                val_text = price_widget.text().replace("$", "").strip()
                if val_text:
                    try:
                        price_overrides[mpn_val] = float(val_text)
                    except ValueError:
                        pass

        if price_overrides:
            self._append_log(f"\n🏷️ Applied {len(price_overrides)} custom Terapeak selling price override(s):")
            for k, v in price_overrides.items():
                self._append_log(f"   - MPN {k}: ${v:.2f}")

        # Reset UI state
        self.log_view.clear()
        self._csv_bytes = None
        self.download_btn.setEnabled(False)
        self.process_btn.setEnabled(False)
        self._set_status("Processing…")

        # Launch worker thread with selected shipping policy profile and price overrides
        selected_policy = self.shipping_policy_combo.currentText()
        self._worker = PipelineWorker(
            mpn_list,
            shipping_profile=selected_policy,
            price_overrides=price_overrides,
        )

        self._worker.log_signal.connect(self._append_log)
        self._worker.finished_signal.connect(self._on_pipeline_complete)
        self._worker.error_signal.connect(self._on_pipeline_error)
        self._worker.finished.connect(lambda: self.process_btn.setEnabled(True))
        self._worker.start()

    def _on_pipeline_complete(self, csv_bytes: bytes) -> None:
        self._csv_bytes = csv_bytes
        self.download_btn.setEnabled(True)
        self._set_status(f"✅ Complete — {len(csv_bytes):,} bytes ready.")
        self._append_log("\n✅ Pipeline complete!  Click  ⬇ Download CSV  to save your file.")
        self._populate_preview_table(csv_bytes)

    def _populate_preview_table(self, csv_bytes: bytes) -> None:
        import csv
        import io

        text = csv_bytes.decode("utf-8-sig", errors="ignore")
        reader = csv.reader(io.StringIO(text))
        rows = list(reader)
        if not rows:
            return

        headers = rows[0]
        data = rows[1:]

        self.csv_table.clear()
        self.csv_table.setRowCount(len(data))
        self.csv_table.setColumnCount(len(headers))
        self.csv_table.setHorizontalHeaderLabels(headers)

        # Color tokens
        CLR_GREEN  = QBrush(QColor(27, 94, 32, 180))   # #1B5E20 - Hosted pic / good price
        CLR_RED    = QBrush(QColor(183, 28, 28, 180))   # #B71C1C - Missing photo
        CLR_BLUE   = QBrush(QColor(13, 71, 161, 180))   # #0D47A1 - Category / ePID matched
        CLR_AMBER  = QBrush(QColor(230, 81, 0, 180))    # #E65100 - Missing aspect
        CLR_PURPLE = QBrush(QColor(74, 20, 140, 180))   # #4A148C - Add Action

        for r_idx, row in enumerate(data):
            for c_idx, val in enumerate(row):
                col_name = headers[c_idx] if c_idx < len(headers) else ""
                item = QTableWidgetItem(val)

                # Apply semantic rules
                if col_name == "PicURL":
                    if val.strip():
                        item.setBackground(CLR_GREEN)
                        item.setToolTip("✅ Hosted Cloudinary URL Ready")
                    else:
                        item.setBackground(CLR_RED)
                        item.setToolTip("⚠️ Warning: No image found")
                elif col_name in ("Category", "Product:EPID"):
                    if val.strip():
                        item.setBackground(CLR_BLUE)
                        item.setToolTip("🔵 eBay Catalog Matched")
                elif col_name.startswith("C:"):
                    if not val.strip():
                        item.setBackground(CLR_AMBER)
                        item.setToolTip("🔸 Empty Item Specific (Aspect)")
                elif col_name.startswith("Action"):
                    item.setBackground(CLR_PURPLE)
                elif col_name == "StartPrice":
                    try:
                        price = float(val)
                        if price >= 8.0:
                            item.setBackground(CLR_GREEN)
                        else:
                            item.setBackground(CLR_AMBER)
                    except ValueError:
                        pass

                self.csv_table.setItem(r_idx, c_idx, item)

    def _on_pipeline_error(self, error_msg: str) -> None:
        self._set_status("❌ Error — see log.")
        self._append_log(f"\n❌ PIPELINE ERROR:\n{error_msg}")
        QMessageBox.critical(self, "Pipeline Error", error_msg)

    def _on_download(self) -> None:
        if not self._csv_bytes:
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save eBay Listing CSV",
            "ebay_motors_listings.csv",
            "CSV Files (*.csv);;All Files (*)",
        )
        if not path:
            return
        try:
            with open(path, "wb") as fh:
                fh.write(self._csv_bytes)
            self._append_log(f"\n💾 CSV saved to: {path}")
            self._set_status(f"Saved → {path}")
        except OSError as exc:
            QMessageBox.critical(self, "Save Error", f"Could not write file:\n{exc}")
