# 5. Data Lifecycle Management (80/100)

### ✅ Strengths

#### 5.1 Staleness Detection
**File:** `src/phx_home_analysis/services/lifecycle/staleness.py`

Sophisticated freshness monitoring:

```python
class StalenessDetector:
    def analyze(self, reference_date: datetime | None = None) -> StalenessReport:
        # Load enrichment data
        raw_data = self._load_enrichment_data()

        # Extract last_updated timestamps
        lifecycles = [self._property_to_lifecycle(prop, reference_date)
                      for prop in raw_data]

        # Identify stale properties (> threshold days)
        stale = [lc for lc in lifecycles if lc.is_stale(self.threshold_days)]

        return StalenessReport(
            total_properties=len(lifecycles),
            stale_count=len(stale),
            stale_properties=stale,
        )
```

**Strengths:**
- ✅ Configurable staleness threshold (default: 30 days)
- ✅ Multiple timestamp field support
- ✅ Human-readable reports
- ✅ CLI tool (`scripts/check_data_freshness.py`)

#### 5.2 Property Archival
**File:** `src/phx_home_analysis/services/lifecycle/archiver.py`

```python
class PropertyArchiver:
    def archive_property(self, address: str) -> ArchiveResult:
        # Remove from enrichment_data.json
        property_data = self._remove_from_enrichment(address)

        # Save to archive directory
        archive_path = self.archive_dir / f"{prop_hash}_{timestamp}.json"
        atomic_json_save(archive_path, property_data)

        return ArchiveResult(success=True, archive_path=archive_path)

    def archive_stale_properties(self, threshold_days: int = 30):
        # Auto-archive based on staleness
        detector = StalenessDetector(threshold_days=threshold_days)
        stale = detector.get_stale_addresses()
        return [self.archive_property(addr) for addr in stale]
```

**Strengths:**
- ✅ Atomic archive operations
- ✅ Restore capability
- ✅ Batch archival of stale data
- ✅ CLI tool (`scripts/archive_properties.py`)

#### 5.3 Freshness Timestamps
**File:** `src/phx_home_analysis/services/enrichment/merge_service.py`

```python
def _add_freshness_timestamps(self, entry: dict, report: ConflictReport):
    now = datetime.now(timezone.utc).isoformat()

    # Track last sync with county
    entry["_last_county_sync"] = now

    # Track last modification
    if report.has_changes:
        entry["_last_updated"] = now
```

**Strengths:**
- ✅ Automatic timestamp management
- ✅ Distinguishes between sync vs actual update
- ✅ ISO 8601 format for portability

### ⚠️ Issues Identified

#### Issue #15: No Retention Policy Enforcement
**Severity:** MEDIUM

**Problem:** Staleness is detected but not automatically enforced.

**Current:**
- Script detects stale data
- Manual decision to archive
- No policy-driven automation

**Recommendation:**
```python
# Add retention policy configuration
@dataclass
class RetentionPolicy:
    warn_after_days: int = 30
    archive_after_days: int = 90
    delete_after_days: int = 365

class LifecycleManager:
    def enforce_retention_policy(self, policy: RetentionPolicy):
        detector = StalenessDetector()

        # Archive data > 90 days old
        archive_threshold = detector.analyze(
            reference_date=datetime.now() - timedelta(days=policy.archive_after_days)
        )
        for prop in archive_threshold.stale_properties:
            archiver.archive_property(prop.full_address)

        # Delete archives > 365 days old
        old_archives = archiver.find_archives_older_than(policy.delete_after_days)
        for archive in old_archives:
            archiver.delete_archive(archive)
```

#### Issue #16: No Automated Data Refresh
**Severity:** MEDIUM

**Problem:** No automatic re-extraction of stale data.

**Current:**
- Manual detection of stale data
- Manual re-run of extraction scripts
- No trigger-based refresh

**Recommendation:**
```python
# Add auto-refresh workflow
@flow(name="auto-refresh-stale-data")
async def refresh_stale_properties(threshold_days: int = 30):
    # Detect stale properties
    detector = StalenessDetector(threshold_days=threshold_days)
    stale_addresses = detector.get_stale_addresses()

    if not stale_addresses:
        return {"status": "no_stale_data"}

    # Extract updated data from county
    client = MaricopaAssessorClient()
    for address in stale_addresses:
        parcel = await client.extract_for_address(address)
        merge_service.merge_parcel(enrichment, address, parcel)

    # Save updated enrichment
    atomic_json_save("data/enrichment_data.json", enrichment)

    return {"status": "refreshed", "count": len(stale_addresses)}

# Schedule daily auto-refresh
if __name__ == "__main__":
    refresh_stale_properties.serve(
        name="auto-refresh-daily",
        cron="0 3 * * *",  # 3am daily
    )
```

#### Issue #17: No Data Expiry Metadata
**Severity:** LOW

**Problem:** No way to specify when data **should** be refreshed.

**Example:**
- County data: Refresh annually (changes rarely)
- Listing data: Refresh weekly (changes frequently)
- School ratings: Refresh quarterly

**Recommendation:**
```python
@dataclass
class FieldMetadata:
    field_name: str
    source: DataSource
    ttl_days: int  # Time-to-live in days
    last_updated: datetime

    @property
    def is_expired(self) -> bool:
        age_days = (datetime.now() - self.last_updated).days
        return age_days > self.ttl_days

# Configure TTLs per field
FIELD_TTL_CONFIG = {
    "lot_sqft": 365,        # County data: 1 year
    "year_built": 365,      # County data: 1 year
    "school_rating": 90,    # School ratings: quarterly
    "list_price": 7,        # Listing price: weekly
    "safety_score": 180,    # Crime data: semi-annually
}
```

---
