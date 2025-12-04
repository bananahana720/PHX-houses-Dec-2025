# 3. Data Lineage & Provenance (85/100)

### ✅ Strengths

#### 3.1 Comprehensive Lineage Tracking
**File:** `src/phx_home_analysis/services/quality/lineage.py`

Excellent field-level lineage:

```python
@dataclass
class FieldLineage:
    field_name: str
    source: DataSource  # Enum: ASSESSOR_API, MANUAL, WEB_SCRAPE, etc.
    confidence: float   # 0.0-1.0
    updated_at: datetime
    original_value: Any
    notes: str | None

class LineageTracker:
    def record_field(self, property_hash: str, field_name: str,
                    source: DataSource, confidence: float):
        # Track every field update
        lineage = FieldLineage(...)
        self._lineage[property_hash][field_name] = lineage
        self.save()  # Atomic save to field_lineage.json
```

**Strengths:**
- ✅ Per-field source tracking
- ✅ Confidence scoring by data source
- ✅ Temporal tracking (updated_at timestamps)
- ✅ Original value preservation
- ✅ Atomic persistence

#### 3.2 Source-Specific Confidence Levels
**File:** `src/phx_home_analysis/services/quality/models.py`

```python
class DataSource(Enum):
    ASSESSOR_API = "assessor_api"
    MANUAL = "manual"
    WEB_SCRAPE = "web_scrape"

    @property
    def default_confidence(self) -> float:
        return {
            DataSource.ASSESSOR_API: 0.95,  # Official county records
            DataSource.MANUAL: 0.85,         # Human verification
            DataSource.WEB_SCRAPE: 0.75,     # May be stale
            DataSource.AI_INFERENCE: 0.70,   # Estimation
        }[self]
```

**Strengths:**
- ✅ Source-based confidence weighting
- ✅ Extensible data source taxonomy
- ✅ Clear confidence hierarchy

#### 3.3 Lineage Reporting
**File:** `src/phx_home_analysis/services/quality/lineage.py`

```python
def generate_report(self) -> str:
    # Source breakdown
    source_counts = {}
    for fields in self._lineage.values():
        for lineage in fields.values():
            source_counts[lineage.source.value] += 1

    # Confidence metrics
    avg_confidence = sum(confidences) / len(confidences)
    high_conf_pct = sum(1 for c in confidences if c >= 0.8) / len(confidences)
```

**Strengths:**
- ✅ Source distribution statistics
- ✅ Confidence aggregation
- ✅ Human-readable reports

### ⚠️ Issues Identified

#### Issue #8: Lineage Not Fully Integrated
**Severity:** MEDIUM

**Problem:** Lineage tracking is **optional** and not enforced at all data entry points.

**Evidence:**
```python
# merge_service.py - Lineage is optional!
def __init__(self, lineage_tracker: LineageTracker | None = None):
    self.lineage_tracker = lineage_tracker  # Can be None!

def _record_lineage(self, prop_hash: str | None, ...):
    if not self.lineage_tracker or not prop_hash:
        return  # Silently skipped if tracker not provided
```

**Impact:**
- Some data updates may not be tracked
- Lineage gaps make debugging difficult
- Can't guarantee complete provenance

**Recommendation:**
```python
# Make lineage tracking mandatory
def __init__(self, lineage_tracker: LineageTracker):
    # Remove Optional - always required
    self.lineage_tracker = lineage_tracker

# Add validation
@dataclass
class EnrichmentEntry:
    def update_field(self, field: str, value: Any, source: DataSource):
        # Enforce lineage recording
        if not hasattr(self, '_lineage_tracker'):
            raise RuntimeError("LineageTracker not configured")

        self._lineage_tracker.record_field(...)
```

#### Issue #9: No Cross-Source Lineage
**Severity:** LOW

**Problem:** Can't track when a field is derived from **multiple sources**.

**Example:**
```python
# Current: orientation field
# - Google Maps API: "North" (confidence 0.90)
# - Satellite imagery AI: "NNE" (confidence 0.75)
# Final value: "North" (averaged/arbitrated)

# But lineage only records ONE source
lineage = FieldLineage(
    field_name="orientation",
    source=DataSource.MANUAL,  # Which source actually contributed?
    confidence=0.85,            # How was this calculated?
)
```

**Recommendation:**
```python
@dataclass
class MultiSourceLineage:
    field_name: str
    sources: list[tuple[DataSource, Any, float]]  # [(source, value, confidence)]
    final_value: Any
    resolution_method: str  # "highest_confidence", "averaged", "manual_override"

# Example
lineage = MultiSourceLineage(
    field_name="orientation",
    sources=[
        (DataSource.MAPS_API, "North", 0.90),
        (DataSource.AI_INFERENCE, "NNE", 0.75),
    ],
    final_value="North",
    resolution_method="highest_confidence"
)
```

#### Issue #10: Limited Lineage Querying
**Severity:** LOW

**Problem:** No advanced lineage queries (e.g., "Show all fields from county API in last 7 days").

**Missing Queries:**
- ❌ `get_fields_by_source(source: DataSource) -> list[str]`
- ❌ `get_fields_updated_after(timestamp: datetime) -> list[str]`
- ❌ `get_low_confidence_sources() -> dict[str, list[str]]`
- ❌ `generate_lineage_graph(property_hash: str) -> DiGraph`

**Recommendation:**
```python
class LineageTracker:
    def get_fields_by_source(self, source: DataSource) -> dict[str, list[str]]:
        """Return properties grouped by fields from specified source."""
        result = defaultdict(list)
        for prop_hash, fields in self._lineage.items():
            for field_name, lineage in fields.items():
                if lineage.source == source:
                    result[field_name].append(prop_hash)
        return result

    def get_fields_updated_after(self, cutoff: datetime) -> list[tuple[str, str]]:
        """Return (property_hash, field_name) updated after cutoff."""
        updates = []
        for prop_hash, fields in self._lineage.items():
            for field_name, lineage in fields.items():
                if lineage.updated_at > cutoff:
                    updates.append((prop_hash, field_name))
        return updates
```

---
