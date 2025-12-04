# 7. FIELD INVENTORY SUMMARY

### Models Across Codebase

| Category | Count | Status |
|----------|-------|--------|
| Pydantic Schemas | 5 | PropertySchema, EnrichmentDataSchema, KillSwitchCriteriaSchema, SewerTypeSchema, SolarStatusSchema, OrientationSchema |
| Domain Entities | 2 | Property, EnrichmentData |
| Domain Value Objects | 7 | Address, Score, RiskAssessment, ScoreBreakdown, RenovationEstimate, PerceptualHash, ImageMetadata |
| Domain Enums | 6 | RiskLevel, Tier, SolarStatus, SewerType, Orientation, ImageSource, ImageStatus |
| Service Models | 10+ | ParcelData, FieldInference, TriageResult, MonthlyCosts, CostEstimate, FieldLineage, QualityScore, etc. |
| Pipeline Models | 2 | PipelineResult, AnalysisPipeline |
| **Duplicates** | **3** | **SourceStats, ExtractionResult, ExtractionState** |

---

### Field Count by Schema

| Schema/Entity | Field Count | Notes |
|---------------|-------------|-------|
| Property | 47 | Aggregate entity with all analysis data |
| PropertySchema | 16 | Validates core listing + enrichment |
| EnrichmentData | 19 | DTO for external research |
| EnrichmentDataSchema | 32 | Validates enrichment sources |
| CSV (phx_homes.csv) | 11 | Listing data only |
| JSON (enrichment_data.json) | 60+ | All enrichment + metadata + synonyms |

**Gap Analysis:**
- PropertySchema missing ~31 fields from Property entity (expected - many are computed)
- EnrichmentDataSchema missing ~28 fields from JSON (metadata, synonyms, computed)
- JSON has ~7 synonym fields (duplicates)
- JSON has ~6 computed fields (should be removed)

---
