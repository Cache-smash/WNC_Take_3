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
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ..worker import PipelineWorker

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("WNC Parts Slingers — eBay Motors CSV Generator")
        self.setMinimumSize(1000, 640)

        self._csv_bytes: bytes | None    = None
        self._worker: PipelineWorker | None = None

        self._build_ui()
        self._apply_stylesheet()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(12)

        # ── App title ─────────────────────────────────────────────────
        title_lbl = QLabel("WNC Parts Slingers — eBay Motors CSV Generator")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_lbl.setFont(title_font)
        root.addWidget(title_lbl)

        sub_lbl = QLabel(
            "Enter up to 15 Dorman/Help part numbers and click Process to generate your listing CSV."
        )
        sub_lbl.setWordWrap(True)
        root.addWidget(sub_lbl)

        # ── Horizontal splitter: input | log ──────────────────────────
        splitter = QSplitter(Qt.Horizontal)

        # Left panel — part number input
        left_widget = QWidget()
        left = QVBoxLayout(left_widget)
        left.setContentsMargins(0, 0, 8, 0)
        left.setSpacing(8)

        input_lbl = QLabel("Part Numbers (one per line, max 15):")
        input_font = QFont()
        input_font.setBold(True)
        input_lbl.setFont(input_font)
        left.addWidget(input_lbl)

        self.part_input = QPlainTextEdit()
        self.part_input.setPlaceholderText(
            "e.g.\n76970\n42317\n13938\n51729"
        )
        self.part_input.setMinimumHeight(180)
        self.part_input.setMaximumHeight(280)
        left.addWidget(self.part_input)

        self.process_btn = QPushButton("⚙   Process Parts")
        self.process_btn.setObjectName("primaryBtn")
        self.process_btn.setMinimumHeight(42)
        self.process_btn.setToolTip(
            "Run the full pipeline: DB lookup → eBay API → Cloudinary → AI → CSV"
        )
        self.process_btn.clicked.connect(self._on_process)
        left.addWidget(self.process_btn)

        left.addStretch()
        splitter.addWidget(left_widget)

        # Right panel — scrolling status log
        right_widget = QWidget()
        right = QVBoxLayout(right_widget)
        right.setContentsMargins(8, 0, 0, 0)
        right.setSpacing(6)

        log_lbl = QLabel("Status Log:")
        log_font = QFont()
        log_font.setBold(True)
        log_lbl.setFont(log_font)
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

        # Give the log panel 2× the horizontal space of the input panel
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        root.addWidget(splitter, stretch=1)

        # ── Download bar ──────────────────────────────────────────────
        bottom = QHBoxLayout()

        self.download_btn = QPushButton("⬇   Download CSV")
        self.download_btn.setMinimumHeight(42)
        self.download_btn.setEnabled(False)
        self.download_btn.setToolTip("Save the generated eBay listing CSV file to disk.")
        self.download_btn.clicked.connect(self._on_download)
        bottom.addWidget(self.download_btn)

        self.status_lbl = QLabel("Ready.")
        self.status_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        bottom.addWidget(self.status_lbl, stretch=1)

        root.addLayout(bottom)

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

    def _on_process(self) -> None:
        raw = self.part_input.toPlainText().strip()
        if not raw:
            QMessageBox.warning(self, "Input Required", "Please enter at least one part number.")
            return

        # Parse, deduplicate, cap at 15.
        # The break lives inside the deduplication guard so blank lines and
        # duplicate rows are skipped without consuming slots in the cap.
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

        # Reset UI state
        self.log_view.clear()
        self._csv_bytes = None
        self.download_btn.setEnabled(False)
        self.process_btn.setEnabled(False)
        self._set_status("Processing…")

        # Launch worker thread
        self._worker = PipelineWorker(mpn_list)
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
