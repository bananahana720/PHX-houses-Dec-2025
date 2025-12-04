# 4. New Data Fields Required

### 4.1 enrichment_data.json Schema Updates

```json
{
  "solar_status": {
    "type": "string",
    "enum": ["owned", "leased", "none", "unknown"],
    "source": "listing_extraction, county_records",
    "kill_switch_use": true,
    "scoring_use": false,
    "default": "unknown",
    "description": "Solar panel ownership status",
    "research_basis": "Market-Beta: 75% of Phoenix solar is leased",
    "detection_hints": [
      "Look for 'solar lease' or 'leased panels' in listing",
      "Check for solar company name in HOA/encumbrances",
      "Arizona law A.R.S. 44-1763 requires seller disclosure"
    ]
  },

  "solar_lease_monthly": {
    "type": "number",
    "source": "listing_extraction, seller_disclosure",
    "kill_switch_use": false,
    "scoring_use": true,
    "default": null,
    "description": "Monthly solar lease payment if leased",
    "typical_range": [100, 200],
    "notes": "Included in cost_efficiency calculation"
  },

  "solar_lease_buyout": {
    "type": "number",
    "source": "seller_disclosure",
    "kill_switch_use": false,
    "scoring_use": false,
    "default": null,
    "description": "Lease buyout amount if available",
    "typical_range": [9000, 21000]
  },

  "hvac_age": {
    "type": "integer",
    "source": "listing_extraction, county_records, visual_inspection",
    "kill_switch_use": false,
    "scoring_use": true,
    "default": null,
    "description": "Age of HVAC system in years",
    "derivation": "If unknown, derive from year_built (assume original)",
    "research_basis": "Domain-Alpha: AZ HVAC lifespan 8-15 years"
  },

  "hvac_install_year": {
    "type": "integer",
    "source": "listing_extraction, permit_records",
    "kill_switch_use": false,
    "scoring_use": true,
    "default": null,
    "description": "Year HVAC system was installed/replaced",
    "notes": "If null, use year_built as proxy"
  },

  "hvac_condition": {
    "type": "string",
    "enum": ["new", "good", "fair", "aging", "replacement_needed", "unknown"],
    "source": "visual_inspection, listing_description",
    "kill_switch_use": false,
    "scoring_use": true,
    "default": "unknown",
    "description": "Assessed condition of HVAC system"
  },

  "roof_underlayment_age": {
    "type": "integer",
    "source": "permit_records, seller_disclosure",
    "kill_switch_use": false,
    "scoring_use": true,
    "default": null,
    "description": "Age of roof underlayment (separate from tile)",
    "research_basis": "Domain-Alpha: Tile lasts 50+ years but underlayment 12-20 years in AZ"
  }
}
```

### 4.2 Data Source Mapping

| Field | Primary Source | Fallback Source | Extraction Phase |
|-------|---------------|-----------------|------------------|
| solar_status | Listing description | Seller disclosure | Phase 1 (listing-browser) |
| solar_lease_monthly | Listing description | Seller disclosure | Phase 1 (listing-browser) |
| hvac_age | Listing description | Derived from year_built | Phase 1 / Phase 2 |
| hvac_install_year | Permit records | Listing description | Phase 1 (listing-browser) |
| hvac_condition | Visual inspection | Listing photos | Phase 2 (image-assessor) |
| roof_underlayment_age | Permit records | Seller disclosure | Phase 1 / Manual |

### 4.3 Detection Patterns for Solar Status

```python
# Patterns to identify solar lease in listing text
SOLAR_LEASE_PATTERNS = [
    r"solar\s+lease",
    r"leased\s+solar",
    r"solar\s+panel\s+lease",
    r"ppa\s+agreement",  # Power Purchase Agreement
    r"sunrun",           # Major solar lease companies
    r"vivint\s+solar",
    r"sunnova",
    r"tesla\s+lease",
    r"solar\s+city\s+lease",
    r"assume\s+solar\s+lease",
    r"solar\s+contract",
    r"transferable\s+solar"
]

SOLAR_OWNED_PATTERNS = [
    r"owned\s+solar",
    r"solar\s+panels?\s+included",
    r"paid\s+off\s+solar",
    r"solar\s+conveys",
    r"no\s+solar\s+lease"
]
```

---
