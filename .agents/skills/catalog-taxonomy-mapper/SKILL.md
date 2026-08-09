---
name: catalog-taxonomy-mapper
description: Automated category tree and dynamic C: aspect column resolver for eBay File Exchange CSV exports.
---

# Catalog Taxonomy Mapper Skill

Use this skill to map catalog item descriptions to official eBay Category IDs and construct mandatory/recommended `C:` item specific headers.

## Guidelines
1. **Category Mapping**: Match product keywords against local `ebay_categories` SQLite indexes.
2. **Item Specific Guardrails**: Limit all `C:` header values (e.g. `C:OE/OEM Part Number`, `C:Interchange Part Number`) to **65 characters max** to comply with eBay bulk upload validation rules.
3. **Stand-Alone Headers**: Always include root `Brand`, `MPN`, `CustomLabel` (`{MPN}-1`), `ConditionID` (`1000`), and `PostalCode` (`28739`).
