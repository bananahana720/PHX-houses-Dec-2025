# Coverage Statistics by Module Category

### Excellent Coverage (95%+)

| Module | Coverage | LOC | Notes |
|--------|----------|-----|-------|
| Kill Switch Criteria | 97% | 124 | HARD criteria implementation |
| Interior Scoring | 100% | 118 | All scoring strategies covered |
| Cost Estimation | 98% | 126 | Comprehensive financial calculations |
| Cost Estimation Rates | 100% | 50 | AZ-specific rate configuration |
| AI Enrichment Models | 100% | 57 | Field inference data models |
| Validation Schemas | 96% | 148 | Property validation rules |
| State Manager | 95% | 81 | Image extraction state tracking |
| Cost Efficiency Scorer | 95% | 22 | Scoring strategy |
| Scoring Weights | 89% | 44 | Configuration weights |

### Good Coverage (80-94%)

| Module | Coverage | LOC | Missing Lines |
|--------|----------|-----|----------------|
| Kill Switch Filter | 90% | 77 | 226, 276-278, 282-283 |
| CSV Reporter | 98% | 43 | 204 |
| Validator | 95% | 106 | 188, 192, 199, 205, 211 |
| Normalizer | 94% | 104 | 126-127, 135, 240, 259, 284 |
| Location Scorer | 98% | 117 | 122, 219 |
| Merger (Enrichment) | 12% | 77 | 46-87 (CRITICAL) |
| Kill Switch Base | 73% | 33 | 69, 79, 101, 114, 128-129 |
| Data Integration Field Mapper | 94% | 36 | 248, 301 |

### Critical Coverage Gaps (<50%)

| Module | Coverage | LOC | Gap | Impact |
|--------|----------|-----|-----|--------|
| **Pipeline Orchestrator** | 34% | 91 | 60 | Main analysis workflow |
| **Property Analyzer** | 24% | 46 | 35 | Single property analysis |
| **Tier Classifier** | 26% | 34 | 25 | Tier assignment logic |
| **County Assessor Client** | 16% | 200 | 167 | County data extraction |
| **Stealth HTTP Client** | 24% | 78 | 59 | Web scraping auth |
| **Redfin Extractor** | 10% | 226 | 203 | Listing data extraction |
| **Zillow Playwright** | 18% | 116 | 95 | Listing image extraction |
| **Redfin Playwright** | 18% | 137 | 113 | Redfin image extraction |
| **Proxy Manager** | 45% | 71 | 39 | Proxy rotation logic |
| **Standardizer** | 25% | 84 | 63 | Image standardization |

---
