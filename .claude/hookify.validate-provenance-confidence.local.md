---
name: validate-provenance-confidence
enabled: true
event: file
conditions:
  - field: new_text
    operator: regex_match
    pattern: confidence\s*[=:]\s*0\.[0-9]+
action: warn
---

## ⚠️ Verify Provenance Confidence Level

**Per E1.S3 and epic-2:349-361**

### Canonical Confidence Levels
| Data Source | Confidence | Rationale |
|-------------|------------|-----------|
| MARICOPA_ASSESSOR | 0.95 | County official records |
| CSV_INPUT | 0.90 | User-provided, verified |
| GOOGLE_MAPS | 0.90 | Authoritative geocoding |
| GREATSCHOOLS | 0.90 | Official school ratings |
| PHOENIX_MLS | 0.87 | MLS feed data |
| ZILLOW | 0.85 | Web scraped |
| REDFIN | 0.85 | Web scraped |
| IMAGE_ANALYSIS | 0.80 | AI vision assessment |
| AI_INFERRED | 0.70 | LLM-generated |
| USER_OVERRIDE | 1.00 | Explicit user input |

### FieldProvenance Structure
```python
@dataclass
class FieldProvenance:
    source: DataSource
    confidence: float  # 0.0 - 1.0
    fetched_at: datetime
    derived_from: list[str] = field(default_factory=list)
```

### Confidence Degradation
| Age | Adjustment |
|-----|------------|
| < 14 days | No change |
| 14-30 days | -0.15 |
| > 30 days | -0.30 |

### Multi-Source Minimum Rule
When data comes from multiple sources:
```python
confidence = min(source1.confidence, source2.confidence)
```

### Display Mapping
| Range | Display | Color |
|-------|---------|-------|
| >= 0.90 | HIGH | Green |
| 0.70-0.89 | MEDIUM | Amber |
| < 0.70 | LOW | Gray |
