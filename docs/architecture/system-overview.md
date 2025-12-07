# System Overview

### High-Level Architecture

```
+===========================================================================+
|                        EXTERNAL DATA SOURCES                               |
+===========================================================================+
|  Maricopa County    Zillow/Redfin    Google Maps    GreatSchools   FEMA   |
|  Assessor API       Listings         Geo Services   Schools API    Flood  |
+======|==================|================|===============|===========|====+
       |                  |                |               |           |
       +--------+---------+-------+--------+-------+-------+-----------+
                |                 |                |
     +----------v-----------------v----------------v-----------+
     |               EXTRACTION LAYER (Phase 0-1)              |
     |  +-------------------+  +--------------------+           |
     |  | County Assessor   |  | Stealth Browser    |           |
     |  | Client            |  | Automation         |           |
     |  | (HTTP/REST)       |  | (nodriver/curl)    |           |
     |  +-------------------+  +--------------------+           |
     |  +-------------------+  +--------------------+           |
     |  | Map Analyzer      |  | Image Extractors   |           |
     |  | Agent (Haiku)     |  | (Zillow, Redfin)   |           |
     |  +-------------------+  +--------------------+           |
     +-------------------------|-------------------------------+
                               |
     +-------------------------v-------------------------------+
     |              DATA INTEGRATION LAYER                      |
     |  +-------------------+  +--------------------+           |
     |  | Field Mappers     |  | Merge Strategies   |           |
     |  | (source -> domain)|  | (conflict resolve) |           |
     |  +-------------------+  +--------------------+           |
     |  +-------------------+  +--------------------+           |
     |  | Data Quality      |  | Deduplication      |           |
     |  | Metrics           |  | (address hash)     |           |
     |  +-------------------+  +--------------------+           |
     +-------------------------|-------------------------------+
                               |
     +-------------------------v-------------------------------+
     |               BUSINESS LOGIC LAYER                       |
     |  +-------------------+  +--------------------+           |
     |  | Kill-Switch       |  | Property Scorer    |           |
     |  | (5 HARD + 4 SOFT) |  | (605 pts, 22 strat)|           |
     |  +-------------------+  +--------------------+           |
     |  +-------------------+  +--------------------+           |
     |  | Tier Classifier   |  | Cost Estimator     |           |
     |  | (Unicorn/Contend) |  | (AZ-specific)      |           |
     |  +-------------------+  +--------------------+           |
     +-------------------------|-------------------------------+
                               |
     +-------------------------v-------------------------------+
     |               PRESENTATION LAYER                         |
     |  +-------------------+  +--------------------+           |
     |  | Console Reporter  |  | HTML Reporter      |           |
     |  | (rich library)    |  | (Jinja2 + Tailwind)|           |
     |  +-------------------+  +--------------------+           |
     |  +-------------------+  +--------------------+           |
     |  | CSV Reporter      |  | Deal Sheet Gen     |           |
     |  | (ranked list)     |  | (mobile-first)     |           |
     |  +-------------------+  +--------------------+           |
     +----------------------------------------------------------+
```

### Key Metrics

| Metric | Target | Source |
|--------|--------|--------|
| Properties per batch | 20-50 | PRD NFR1 |
| Kill-switch accuracy | 100% | PRD NFR5 |
| Scoring consistency | +/-5 pts | PRD NFR6 |
| Batch processing time | <=30 min | PRD NFR1 |
| Re-scoring time | <=5 min | PRD NFR2 |
| Operating cost | <=$90/month | PRD NFR22 |

---
