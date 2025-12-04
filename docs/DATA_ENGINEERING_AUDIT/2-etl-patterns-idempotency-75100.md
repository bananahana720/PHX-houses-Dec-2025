# 2. ETL Patterns & Idempotency (75/100)

### ✅ Strengths

#### 2.1 Atomic File Operations
**File:** `src/phx_home_analysis/utils/file_ops.py`

Excellent crash-safe file writing:

```python
def atomic_json_save(path: Path, data: Any, create_backup: bool = True):
    # 1. Create backup
    if create_backup and path.exists():
        backup_path = path.with_suffix(f".{timestamp}.bak.json")
        shutil.copy2(path, backup_path)

    # 2. Write to temp file
    temp_path = path.with_suffix(f"{path.suffix}.tmp")
    with open(temp_path, "w") as f:
        json.dump(data, f)

    # 3. Atomic rename (POSIX atomic, Windows replace)
    temp_path.replace(path)
```

**Strengths:**
- ✅ Atomic operations prevent corruption
- ✅ Automatic backups for recovery
- ✅ Temp file cleanup on failure
- ✅ Cross-platform compatibility

#### 2.2 Conflict Resolution Strategy
**File:** `src/phx_home_analysis/services/enrichment/merge_service.py`

Well-designed merge logic:

```python
class EnrichmentMergeService:
    PROTECTED_SOURCES = frozenset({"manual", "manual_research", "user"})

    def should_update_field(self, entry: dict, field_name: str, new_value: Any):
        existing_source = entry.get(f"{field_name}_source", "")

        # Never overwrite manual research
        if existing_source in self.PROTECTED_SOURCES:
            return False, "Preserving manual research"

        # Fill missing values
        if entry.get(field_name) is None:
            return True, "No existing value"

        # County data is authoritative
        return True, "Updating with county data"
```

**Strengths:**
- ✅ Manual data preservation (critical for research)
- ✅ Clear precedence rules (county > listing > default)
- ✅ Conflict logging for auditing

#### 2.3 Update-Only Mode
**File:** `src/phx_home_analysis/services/enrichment/merge_service.py`

```python
def merge_parcel(self, ..., update_only: bool = False):
    if update_only:
        # Only fill None/missing values
        if existing_value is None:
            entry[field_name] = value
    else:
        # Full conflict resolution
        should_update, reason = self.should_update_field(...)
```

**Strengths:**
- ✅ Safe incremental updates
- ✅ Idempotent operations (re-running won't break data)

### ❌ Critical Issues

#### Issue #4: No Extract-Transform-Load Separation
**Severity:** HIGH
**Location:** Multiple extraction scripts

**Problem:** ETL phases are **tightly coupled**, not separated into distinct stages.

**Current Pattern:**
```python
# extract_county_data.py - MIXED CONCERNS
async def extract_and_merge():
    # EXTRACT
    parcel = await client.extract_for_address(address)

    # TRANSFORM (implicit in ParcelData)
    transformed = parcel.to_dict()

    # LOAD (happens immediately in same function)
    merge_service.merge_parcel(enrichment, address, parcel)
    save_enrichment(enrichment)  # Immediate write
```

**Problems:**
- Cannot extract without loading
- Cannot re-transform without re-extracting
- No intermediate staging layer
- Difficult to replay transformations

**Best Practice Pattern:**
```python
# EXTRACT: Raw data landing zone
extract_to_staging(source, staging_path)

# TRANSFORM: Separate transformation layer
transform_staging_to_clean(staging_path, clean_path)

# LOAD: Final load to production
load_clean_to_production(clean_path, production_path)
```

**Recommendation:**
```python
# scripts/etl/extract_county.py
async def extract_county_data(output_path: Path):
    """Extract raw county data to staging."""
    results = await client.extract_batch(properties)
    atomic_json_save(output_path, results)

# scripts/etl/transform_county.py
def transform_county_data(input_path: Path, output_path: Path):
    """Transform staging data to clean schema."""
    raw = json.load(open(input_path))
    clean = [ParcelData.from_raw(r).to_dict() for r in raw]
    atomic_json_save(output_path, clean)

# scripts/etl/load_county.py
def load_county_data(input_path: Path, target_path: Path):
    """Load clean data to enrichment."""
    clean = json.load(open(input_path))
    enrichment = json.load(open(target_path))
    merge_service.merge_batch(enrichment, clean)
    atomic_json_save(target_path, enrichment)
```

#### Issue #5: No Orchestration Layer
**Severity:** HIGH

**Problem:** No workflow orchestration tool (Airflow, Prefect, Dagster).

**Current State:**
- Manual script execution order
- No dependency management
- No retry logic
- No monitoring/alerting

**Missing Capabilities:**
- ❌ DAG-based workflow definition
- ❌ Automatic retry on transient failures
- ❌ Task-level checkpointing
- ❌ Parallel task execution
- ❌ SLA monitoring
- ❌ Email/Slack alerting on failure

**Recommendation: Add Prefect 2.0**
```python
# workflows/county_enrichment.py
from prefect import flow, task
from prefect.tasks import exponential_backoff

@task(retries=3, retry_delay_seconds=exponential_backoff(10))
async def extract_county_data() -> Path:
    """Extract county data with auto-retry."""
    results = await client.extract_batch(properties)
    staging_path = Path("data/staging/county_raw.json")
    atomic_json_save(staging_path, results)
    return staging_path

@task
def transform_county_data(input_path: Path) -> Path:
    clean_path = Path("data/clean/county_clean.json")
    # Transform logic
    return clean_path

@task
def load_county_data(input_path: Path) -> dict:
    # Load logic
    return {"loaded_count": 35}

@flow(name="county-enrichment")
async def county_enrichment_flow():
    staging = await extract_county_data()
    clean = transform_county_data(staging)
    result = load_county_data(clean)
    return result

# Deploy and schedule
if __name__ == "__main__":
    county_enrichment_flow.serve(
        name="county-enrichment-daily",
        cron="0 2 * * *"  # Run at 2am daily
    )
```

#### Issue #6: Limited Idempotency Guarantees
**Severity:** MEDIUM

**Problem:** Scripts are not fully idempotent.

**Example:**
```python
# scripts/extract_county_data.py
# Running this twice on the same day:
# - Re-fetches from API (wasteful)
# - Overwrites existing data (may lose manual edits if merge fails)
# - No deduplication at extract stage
```

**Missing:**
- ❌ Checksum-based change detection
- ❌ Incremental extraction (only changed records)
- ❌ Upsert semantics (merge vs overwrite)

**Recommendation:**
```python
# Add change detection
def extract_county_data(properties: list[Property]):
    checksum_cache = load_checksums("data/.checksums.json")

    for prop in properties:
        current_hash = compute_hash(prop.address)

        # Skip if unchanged
        if checksum_cache.get(prop.address) == current_hash:
            continue

        # Extract only changed properties
        parcel = await client.extract(prop)
        yield parcel
        checksum_cache[prop.address] = current_hash

    save_checksums(checksum_cache)
```

#### Issue #7: No Transaction Boundaries
**Severity:** MEDIUM

**Problem:** No all-or-nothing transaction semantics for batch operations.

**Example:**
```python
# Current: If merge fails on property #20 of 35:
# - Properties 1-19 are already written
# - Property 20+ are not processed
# - Enrichment file is in inconsistent state
```

**Recommendation:**
```python
# Add transaction pattern
def merge_batch_transactional(enrichment_path: Path, parcels: list[ParcelData]):
    # Load current state
    original = json.load(open(enrichment_path))
    working_copy = original.copy()

    try:
        # Apply all merges to working copy
        for parcel in parcels:
            merge_service.merge_parcel(working_copy, parcel)

        # Atomic commit (all or nothing)
        atomic_json_save(enrichment_path, working_copy)
        return {"success": True, "count": len(parcels)}

    except Exception as e:
        # Rollback: original file unchanged
        logger.error(f"Merge failed, rolling back: {e}")
        return {"success": False, "error": str(e)}
```

---
