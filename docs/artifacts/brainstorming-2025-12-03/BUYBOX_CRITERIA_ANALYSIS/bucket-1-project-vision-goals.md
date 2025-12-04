# BUCKET 1: PROJECT VISION & GOALS

### What the Vision States

From `CLAUDE.md` and system context:

**First Home Purchase in Maricopa County**
- Target user: First-time home buyer
- Geography: Maricopa County, Phoenix metro (Arizona-specific)
- Goal: Ranked candidate property lists with interpretable decision support

**Key Deliverables Envisioned:**
1. Kill-switch filtering with hard/soft criteria
2. 600-point weighted scoring system
3. Tier classification (Unicorn/Contender/Pass)
4. Ranked candidate lists
5. Historical price/status timelines
6. Visual + tabular dashboards
7. Interpretable scoring (explain WHY good/bad)
8. Raw data preservation for re-scoring as criteria evolve

**Evaluation Dimensions** (from vision):
- Location (commute, safety/vibe, amenities, schools, growth, zoning, flood/heat risk)
- Condition (roof/foundation/HVAC/plumbing/electrical, layout fit, "bones over cosmetics")
- Climate (desert heat, power usage, outdoor living, low-water landscaping)
- Economics (property tax, HOA, utilities, insurance, commute cost, new vs older stock)
- Resale (energy efficiency, outdoor spaces, pools, patios, parking, storage)

### Implementation Status

**WHAT'S FULLY IMPLEMENTED:**
- Kill-switch filtering (7 criteria)
- 600-point scoring (18 sub-criteria across 3 sections)
- Tier classification logic
- Raw data preservation (CSV + JSON dual storage)
- Arizona-specific cost modeling (HVAC, roof, pool lifespans)
- Scoring architecture (strategy pattern, composable)

**WHAT'S PARTIALLY IMPLEMENTED:**
- Interpretability/explainability (scores calculated but rationales sparse)
- Dashboard/visualization (basic output exists, could be richer)
- Historical price/status timelines (no time-series tracking)
- Resale factor modeling (some implicit, not explicit in all cases)

**WHAT'S MISSING/UNDERDEVELOPED:**
- Zoning data (no implementation found)
- Growth/development risk assessment (not in scoring)
- Low-water landscaping preference (not modeled)
- Commute cost integration (distance captured, not $ impact)
- Explainability/decision rationale generation (scores only, no "why")

---
