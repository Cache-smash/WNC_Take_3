---
name: fitment-sanitizer
description: Automotive fitment parser to standardize legacy year ranges into structured vehicle compatibility tables.
---

# Fitment Sanitizer Skill

Use this skill when converting unstructured fitment text into clean eBay-compatible HTML tables or CSV fitment payloads.

## Guidelines
1. **Year Normalization**: Convert legacy year syntax (e.g. `1977-87`, `'77 up`, `1973-62`) into standard 4-digit year ranges.
2. **Make & Model Disambiguation**: Group vehicle applications by Make (`Ford`, `GM`, `Chrysler`, `AMC`) and position (`Front`, `Rear`, `Left`, `Right`).
3. **HTML Output Styling**: Format vehicle fitment application tables using clean, centered HTML blocks (`font-family: Arial; text-align: center; max-width: 800px;`).
