---
name: validate-extractor-priority
enabled: true
event: file
conditions:
  - field: file_path
    operator: regex_match
    pattern: (orchestrator|extractor|image_extraction).*\.py$
  - field: new_text
    operator: regex_match
    pattern: (priority|order|chain|sources).*\[
action: warn
---

## ⚠️ Verify Extractor Priority Chain

**Per E2.R1: PhoenixMLS is PRIMARY data source**

### Canonical Priority Order
```python
EXTRACTOR_PRIORITY = [
    "PHOENIX_MLS",      # 1. Primary - no anti-bot, 95%+ reliability
    "MARICOPA_ASSESSOR", # 2. County API - authoritative lot/year/garage
    "ZILLOW_ZPID",       # 3. Fallback - ZPID direct URLs
    "REDFIN",            # 4. Last resort
]
```

### Why PhoenixMLS First
- No anti-bot systems (no CAPTCHA, no fingerprinting)
- Actual MLS feed data (not scraped)
- 70+ fields extracted (vs 10 from Zillow)
- 95%+ success rate

### Critical: Kill-Switch Field Sources
| Field | Primary Source | Confidence |
|-------|----------------|------------|
| HOA | PhoenixMLS | 0.87 |
| beds, baths, sqft | PhoenixMLS | 0.87 |
| lot_sqft, garage | Maricopa Assessor | 0.95 |
| sewer_type, year | Maricopa Assessor | 0.95 |

### If Changing Priority
- Document rationale
- Update `epic-2-property-data-acquisition.md`
- Verify kill-switch field coverage maintained
- Run full pipeline validation
