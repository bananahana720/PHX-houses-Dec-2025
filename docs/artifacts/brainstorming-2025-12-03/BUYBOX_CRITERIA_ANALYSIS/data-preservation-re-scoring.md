# DATA PRESERVATION & RE-SCORING

### Current Architecture: CSV + JSON Layered Strategy

**Base Layer** (`data/phx_homes.csv`):
- Immutable original listings (price, beds, baths, sqft, etc.)
- ~20 columns of basic data

**Enrichment Layer** (`data/enrichment_data.json`):
- Phase 0: County assessor data (lot_sqft, year_built, garage, sewer, tax)
- Phase 1: Listing extraction (images, hoa_fee, school_rating, orientation, distances)
- Phase 2: Image assessment (kitchen_layout_score, master_suite_score, etc.)
- Phase 3: Scoring results (score_breakdown, tier, kill_switch_verdict)

**Re-Scoring Capability:**
✓ Raw data preserved (fields NOT recalculated)
✓ Can change weights in `ScoringWeights` dataclass
✓ Can change severity thresholds in `constants.py`
✓ Can update scoring logic in strategy classes
✓ Scripts can reload CSV + JSON and re-score entire portfolio

**Current Limitation:**
- No version control on enrichment data (when last updated?)
- No audit trail on weight changes (when did we switch from 230 to 250pt Section A?)
- Staleness detection exists but not enforcement

---
