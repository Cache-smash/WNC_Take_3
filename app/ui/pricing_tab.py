"""
pricing_tab.py — PySide6 Competitive Pricing Engine tab for WNC Parts Slingers.

Displays a clean control header, batch input, and an interactive colored QTableWidget
recommending optimal eBay selling prices based on COGS tiers and competitor data.
"""

import logging
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..pricing_engine import evaluate_part_pricing, DEFAULT_SHIPPING_COST

logger = logging.getLogger(__name__)


class PricingTabWidget(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._recommendations = []
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        # ── 1. Top Controls Header ─────────────────────────────────────
        ctrl_bar = QHBoxLayout()
        ctrl_bar.setSpacing(16)

        # Shipping cost input
        ship_lbl = QLabel("Outbound Postage ($):")
        ship_lbl.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.ship_input = QLineEdit(str(DEFAULT_SHIPPING_COST))
        self.ship_input.setFixedWidth(70)
        self.ship_input.setToolTip("Estimated USPS Ground Advantage shipping cost.")

        # Strategy selector
        strat_lbl = QLabel("Pricing Strategy:")
        strat_lbl.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.strat_combo = QComboBox()
        self.strat_combo.addItems([
            "Lowest Competitor (-$0.05)",
            "Floor Price Only (COGS + Fees)",
            "NOS Rarity Boost (+15%)",
        ])

        # Undercut offset
        offset_lbl = QLabel("Undercut ($):")
        offset_lbl.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.offset_input = QLineEdit("0.05")
        self.offset_input.setFixedWidth(60)

        ctrl_bar.addWidget(ship_lbl)
        ctrl_bar.addWidget(self.ship_input)
        ctrl_bar.addWidget(strat_lbl)
        ctrl_bar.addWidget(self.strat_combo)
        ctrl_bar.addWidget(offset_lbl)
        ctrl_bar.addWidget(self.offset_input)
        ctrl_bar.addStretch()

        layout.addLayout(ctrl_bar)

        # ── 2. Splitter: Left Input | Right Interactive Table ──────────
        splitter = QSplitter(Qt.Horizontal)

        # Left side: MPN Input
        left_widget = QWidget()
        left = QVBoxLayout(left_widget)
        left.setContentsMargins(0, 0, 8, 0)
        left.setSpacing(8)

        input_lbl = QLabel("Dorman Part Numbers (one per line):")
        input_lbl.setFont(QFont("Segoe UI", 9, QFont.Bold))
        left.addWidget(input_lbl)

        self.part_input = QPlainTextEdit()
        self.part_input.setPlaceholderText("e.g.\n02336\n13850\n41050\n49025\n80000")
        self.part_input.setMinimumHeight(200)
        left.addWidget(self.part_input)

        self.calc_btn = QPushButton("🏷️   Calculate Optimal Prices")
        self.calc_btn.setObjectName("primaryBtn")
        self.calc_btn.setMinimumHeight(42)
        self.calc_btn.clicked.connect(self._on_calculate)
        left.addWidget(self.calc_btn)

        splitter.addWidget(left_widget)

        # Right side: Interactive QTableWidget
        right_widget = QWidget()
        right = QVBoxLayout(right_widget)
        right.setContentsMargins(8, 0, 0, 0)
        right.setSpacing(8)

        table_lbl = QLabel("Market Recon & Price Recommendations:")
        table_lbl.setFont(QFont("Segoe UI", 9, QFont.Bold))
        right.addWidget(table_lbl)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "MPN", "Brand", "Tier COGS", "Floor Price", "Lowest Comp", "Suggested Price", "Net Margin", "Status"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1A1A1A;
                gridline-color: #333333;
                color: #FFFFFF;
                border: 1px solid #333333;
                border-radius: 4px;
            }
            QHeaderView::section {
                background-color: #262626;
                color: #03DAC6;
                font-weight: bold;
                padding: 6px;
                border: 1px solid #333333;
            }
        """)
        right.addWidget(self.table)

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        layout.addWidget(splitter, stretch=1)

        # ── 3. Bottom Action Bar ───────────────────────────────────────
        bottom = QHBoxLayout()
        self.export_btn = QPushButton("⚡   Export Price Revision CSV")
        self.export_btn.setMinimumHeight(42)
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self._on_export)
        bottom.addWidget(self.export_btn)

        self.status_lbl = QLabel("Ready for pricing evaluation.")
        self.status_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        bottom.addWidget(self.status_lbl, stretch=1)

        layout.addLayout(bottom)

    # ── Calculation Handler ───────────────────────────────────────────
    def _on_calculate(self) -> None:
        raw_text = self.part_input.toPlainText().strip()
        if not raw_text:
            QMessageBox.warning(self, "No Input", "Please enter at least one Dorman part number.")
            return

        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        mpns = list(dict.fromkeys(lines))  # Deduplicate

        try:
            ship_cost = float(self.ship_input.text().strip() or DEFAULT_SHIPPING_COST)
            undercut = float(self.offset_input.text().strip() or "0.05")
        except ValueError:
            QMessageBox.warning(self, "Invalid Inputs", "Please enter valid numeric values for shipping and undercut.")
            return

        self._recommendations.clear()
        self.table.setRowCount(0)

        # Mock sample competitor price variance for calculation demonstration
        mock_comp_prices = {
            "02336": 12.50,
            "13850": 9.99,
            "41050": 7.50,   # Will lock at floor
            "49025": None,   # Rarity boost
            "80000": 14.25,
        }

        for mpn in mpns:
            comp_price = mock_comp_prices.get(mpn, 15.00)
            rec = evaluate_part_pricing(
                mpn=mpn,
                brand="Dorman",
                title=f"Dorman Auto Part {mpn}",
                lowest_competitor_price=comp_price,
                shipping_cost=ship_cost,
                undercut_amount=undercut,
            )
            self._recommendations.append(rec)

        self._populate_table()
        self.export_btn.setEnabled(True)
        self.status_lbl.setText(f"Processed {len(self._recommendations)} pricing recommendation(s).")

    def _populate_table(self) -> None:
        self.table.setRowCount(len(self._recommendations))
        for row, rec in enumerate(self._recommendations):
            self.table.setItem(row, 0, QTableWidgetItem(rec.mpn))
            self.table.setItem(row, 1, QTableWidgetItem(rec.brand))
            self.table.setItem(row, 2, QTableWidgetItem(f"${rec.cogs:.2f}"))
            self.table.setItem(row, 3, QTableWidgetItem(f"${rec.floor_price:.2f}"))
            
            comp_str = f"${rec.lowest_competitor_price:.2f}" if rec.lowest_competitor_price else "None"
            self.table.setItem(row, 4, QTableWidgetItem(comp_str))
            
            sug_item = QTableWidgetItem(f"${rec.suggested_price:.2f}")
            sug_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.table.setItem(row, 5, sug_item)

            margin_item = QTableWidgetItem(f"${rec.margin_dollars:.2f} ({rec.margin_pct}%)")
            self.table.setItem(row, 6, margin_item)

            # Colored Status Pill Cell
            status_item = QTableWidgetItem(rec.status_label)
            status_item.setForeground(QColor(rec.color_hex))
            status_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.table.setItem(row, 7, status_item)

    def _on_export(self) -> None:
        if not self._recommendations:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Price Revision CSV", "eBay_Price_Revisions.csv", "CSV Files (*.csv)"
        )
        if not path:
            return

        import csv
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Action", "CustomLabel", "StartPrice"])
            for rec in self._recommendations:
                writer.writerow(["Revise", f"{rec.mpn}-1", f"{rec.suggested_price:.2f}"])

        QMessageBox.information(self, "Export Complete", f"Exported {len(self._recommendations)} price revision(s) to:\n{path}")
