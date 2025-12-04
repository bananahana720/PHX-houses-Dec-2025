# Implementation Recommendations

### For PHX Houses Analysis Pipeline

#### 1. FEMA NFHL Integration (Recommended)

**Priority: High** | **Effort: Low** | **Confidence: [High]**

Create a new script `scripts/extract_flood_zone.py`:

```python
# Integration approach
# 1. Add flood_zone field to enrichment_data.json schema
# 2. Query FEMA NFHL during Phase 0 (alongside county data)
# 3. Add flood zone to kill-switch criteria:
#    - HARD FAIL: Zone A, AE, AH, AO, VE (SFHA = True)
#    - WARNING: Zone X (shaded), Zone D
#    - PASS: Zone X (unshaded)
```

**Data Model Addition:**
```python
class FloodData(BaseModel):
    flood_zone: str  # "X", "AE", etc.
    zone_subtype: Optional[str]
    sfha: bool  # Special Flood Hazard Area
    base_flood_elevation: Optional[float]
    query_timestamp: datetime
```

#### 2. Maricopa County Assessor API Integration

**Priority: Medium** | **Effort: Medium** | **Confidence: [High]**

The existing `scripts/extract_county_data.py` likely already uses this API. Verify the following fields are being extracted:

- `year_built` - For age calculations
- `lot_sqft` - For kill-switch criteria
- `garage_spaces` - For kill-switch criteria
- `pool` - For Arizona context scoring
- `living_sqft` - For value analysis

#### 3. Permit Data Access (Not Recommended for Automation)

**Priority: Low** | **Effort: High** | **Confidence: [Medium]**

Due to lack of API access, permit data should be:
- Obtained via manual inspection of seller disclosures
- Requested via public records when evaluating serious candidates
- Used for due diligence, not initial screening

#### 4. Future Considerations

**Accela API Monitoring:**
- Monitor Maricopa County for potential API access
- Contact form: https://preview.mcassessor.maricopa.gov/contact/

**OpenFEMA Integration:**
- Consider querying NFIP claims history for property addresses
- High claim counts indicate recurring flood issues

---
