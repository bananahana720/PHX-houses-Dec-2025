# APPENDICES

### A. Complete Field Name Cross-Reference

| Canonical Name | Synonyms | Type | Sources |
|----------------|----------|------|---------|
| lot_sqft | - | int | County, Schema, Entity |
| hoa_fee | - | float | Enrichment, Schema, Entity |
| price_num | list_price, price | int | CSV, JSON, Entity |
| school_rating | - | float | Enrichment, Entity |
| safety_neighborhood_score | safety_score | float | JSON, Entity, Schema(mismatch) |
| high_ceilings_score | ceiling_height_score | float | JSON(both), Entity, Schema |
| kitchen_layout_score | kitchen_quality_score | float | JSON(both), Entity, Schema |
| master_suite_score | master_quality_score | float | JSON(both), Entity, Schema |
| laundry_area_score | laundry_score | float | JSON(both), Entity, Schema |
| fireplace_present | - | bool | Entity, Schema |
| fireplace_score | - | float | JSON only |

### B. Recommended Import Structure

```python
# Canonical locations after consolidation
from phx_home_analysis.validation.schemas import (
    PropertySchema,
    EnrichmentDataSchema,
    SewerTypeSchema,
    SolarStatusSchema,
    OrientationSchema,
)

from phx_home_analysis.domain.entities import Property, EnrichmentData

from phx_home_analysis.domain.enums import (
    RiskLevel,
    Tier,
    SolarStatus,
    SewerType,
    Orientation,
)

from phx_home_analysis.services.image_extraction.extraction_stats import (
    SourceStats,
    ExtractionResult,
    StatsTracker,
)

from phx_home_analysis.services.image_extraction.state_manager import (
    ExtractionState,
    StateManager,
)
```

---

**END OF REPORT**
