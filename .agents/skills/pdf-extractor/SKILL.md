---
name: pdf-extractor
description: High-density PDF catalog text and fitment table extractor for NOS parts catalogs.
---

# PDF Extractor Skill

Use this skill when processing raw automotive catalog PDFs (e.g. Perfect Parts, Dorman, Motormite).

## Guidelines
1. **Per-MPN Isolation**: Extract text blocks strictly bounded between consecutive part numbers to prevent text contamination across items.
2. **Table Reconstruction**: Preserve tabular alignment for multi-column vehicle application tables (Year, Make, Model, Position).
3. **OCR / Raw Text**: When processing scanned PDFs, strip non-printable artifact characters while keeping hyphenated part numbers intact (`FL-18B`, `BHD-21B`).
