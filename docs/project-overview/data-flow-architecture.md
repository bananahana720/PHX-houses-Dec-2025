# Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       DATA FLOW PIPELINE                        │
└─────────────────────────────────────────────────────────────────┘

Phase 0: County Data (Optional, runs independently)
┌────────────────────────┐
│ Maricopa Assessor API  │ ─→ lot_sqft, year_built, garage, pool
└────────────────────────┘
         ↓
   enrichment_data.json

Phase 1: Listing + Map (Parallel execution)
┌────────────────────────┐   ┌────────────────────────┐
│ listing-browser (Haiku)│   │ map-analyzer (Haiku)   │
│  - Zillow/Redfin       │   │  - Google Maps         │
│  - stealth automation  │   │  - GreatSchools        │
│  - images, price, HOA  │   │  - crime, walkability  │
└────────────────────────┘   └────────────────────────┘
         ↓                              ↓
   property_images/            enrichment_data.json
         │                              │
         └──────────┬───────────────────┘
                    ↓
              [Prerequisites Met]

Phase 2: Image Assessment (REQUIRES Phase 1 complete)
┌────────────────────────┐
│ image-assessor (Sonnet)│ ─→ kitchen, master, light, ceilings,
│  - Visual analysis     │    fireplace, laundry, aesthetics scores
│  - Claude Vision       │
│  - Era calibration     │
└────────────────────────┘
         ↓
   enrichment_data.json (Section C scores)

Phase 3: Synthesis
┌────────────────────────┐
│ PropertyScorer         │
│ KillSwitchFilter       │ ─→ total_score, tier, verdict
│ TierClassifier         │
└────────────────────────┘
         ↓
   enrichment_data.json (complete analysis)

Phase 4: Report Generation
┌────────────────────────┐
│ Deal Sheets            │
│ Visualizations         │ ─→ HTML reports, CSV rankings,
│ Rankings               │    radar charts, maps
└────────────────────────┘
         ↓
   reports/ directory
```
