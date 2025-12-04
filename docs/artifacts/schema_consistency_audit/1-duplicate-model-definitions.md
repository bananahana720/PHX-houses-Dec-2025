# 1. DUPLICATE MODEL DEFINITIONS

### 1.1 SourceStats (EXACT DUPLICATE)

**Location 1:** `src/phx_home_analysis/services/image_extraction/extraction_stats.py:12`
```python
@dataclass
class SourceStats:
    """Statistics for a single image source."""
    source: str
    properties_processed: int = 0
    properties_failed: int = 0
    images_found: int = 0
    images_downloaded: int = 0
    images_failed: int = 0
    duplicates_detected: int = 0
```

**Location 2:** `src/phx_home_analysis/services/image_extraction/orchestrator.py:40`
```python
@dataclass
class SourceStats:
    """Statistics for a single image source."""
    source: str
    properties_processed: int = 0
    properties_failed: int = 0
    images_found: int = 0
    images_downloaded: int = 0
    images_failed: int = 0
    duplicates_detected: int = 0
```

**Differences:** NONE - Exact duplicates with identical fields and methods.

**Canonical:** `extraction_stats.py` (has computed properties: `success_rate`, `download_success_rate`)

**Recommendation:** Delete duplicate in `orchestrator.py`, import from `extraction_stats.py`

---

### 1.2 ExtractionResult (EXACT DUPLICATE)

**Location 1:** `src/phx_home_analysis/services/image_extraction/extraction_stats.py:51`
```python
@dataclass
class ExtractionResult:
    """Aggregated results from image extraction process."""
    total_properties: int = 0
    properties_completed: int = 0
    properties_failed: int = 0
    properties_skipped: int = 0
    total_images: int = 0
    unique_images: int = 0
    duplicate_images: int = 0
    failed_downloads: int = 0
    by_source: Dict[str, SourceStats] = field(default_factory=dict)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
```

**Location 2:** `src/phx_home_analysis/services/image_extraction/orchestrator.py:53`
```python
@dataclass
class ExtractionResult:
    """Results from image extraction process."""
    total_properties: int
    properties_completed: int
    properties_failed: int
    properties_skipped: int
    total_images: int
    unique_images: int
    duplicate_images: int
    failed_downloads: int
    by_source: dict[str, SourceStats] = field(default_factory=dict)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
```

**Differences:**
- Different default values (`= 0` vs required in orchestrator.py)
- Type hint difference: `Dict` vs `dict`
- Docstring wording

**Canonical:** `extraction_stats.py` (has computed properties: `duration_seconds`, `success_rate`, `properties_per_minute`, `to_dict()`)

**Recommendation:** Delete duplicate in `orchestrator.py`, import from `extraction_stats.py`

---

### 1.3 ExtractionState (EXACT DUPLICATE)

**Location 1:** `src/phx_home_analysis/services/image_extraction/state_manager.py:17`
```python
@dataclass
class ExtractionState:
    """Persistent state for resumable extraction."""
    completed_properties: Set[str] = field(default_factory=set)
    failed_properties: Set[str] = field(default_factory=set)
    last_updated: Optional[str] = None
```

**Location 2:** `src/phx_home_analysis/services/image_extraction/orchestrator.py:124`
```python
@dataclass
class ExtractionState:
    """Persistent state for resumable extraction."""
    completed_properties: Set[str] = field(default_factory=set)
    failed_properties: Set[str] = field(default_factory=set)
    last_updated: Optional[str] = None
```

**Differences:** NONE - Exact duplicates

**Canonical:** `state_manager.py` (has methods: `to_dict()`, `from_dict()`)

**Recommendation:** Delete duplicate in `orchestrator.py`, import from `state_manager.py`

---
