# 4. Schema Evolution (60/100)

### ✅ Strengths

#### 4.1 Flexible Schema with `extra="allow"`
**File:** `src/phx_home_analysis/validation/schemas.py`

```python
class EnrichmentDataSchema(BaseModel):
    # Core fields defined
    full_address: str
    lot_sqft: int | None

    # Allow extra fields for metadata
    model_config = {
        "str_strip_whitespace": True,
        "extra": "allow",  # Accept _last_updated, _last_county_sync
    }
```

**Strengths:**
- ✅ Supports metadata fields (`_last_updated`, `_last_county_sync`)
- ✅ Won't break on unexpected fields

### ❌ Critical Issues

#### Issue #11: No Schema Versioning
**Severity:** CRITICAL

**Problem:** No schema version tracking or migration system.

**Current State:**
```json
// enrichment_data.json - NO version field
[
  {
    "full_address": "...",
    "lot_sqft": 8069,
    // What schema version is this? Unknown!
  }
]
```

**Impact:**
- Can't determine which schema a file uses
- Can't migrate old data to new schemas
- Breaking schema changes require manual data fixes

**Recommendation:**
```python
# Add schema versioning
CURRENT_SCHEMA_VERSION = "2.0.0"

class EnrichmentDataSchema(BaseModel):
    _schema_version: str = Field(default=CURRENT_SCHEMA_VERSION)
    full_address: str
    # ... fields

# Migration framework
class SchemaMigration:
    @staticmethod
    def migrate_1_0_to_2_0(data: dict) -> dict:
        """Migrate schema v1.0 to v2.0."""
        # Add new fields with defaults
        data.setdefault("flood_zone", None)
        data.setdefault("crime_risk_level", None)

        # Rename fields
        if "school_score" in data:
            data["school_rating"] = data.pop("school_score")

        # Update version
        data["_schema_version"] = "2.0.0"
        return data

# Auto-migration on load
def load_enrichment(path: Path) -> list[dict]:
    data = json.load(open(path))
    for entry in data:
        version = entry.get("_schema_version", "1.0.0")
        if version < CURRENT_SCHEMA_VERSION:
            entry = migrate_schema(entry, version, CURRENT_SCHEMA_VERSION)
    return data
```

#### Issue #12: No Migration Scripts
**Severity:** CRITICAL

**Problem:** No tooling for schema migrations.

**Missing:**
- ❌ Migration runner (`scripts/migrate_schema.py`)
- ❌ Migration history log
- ❌ Rollback capability
- ❌ Dry-run mode for migrations

**Recommendation:**
```python
# scripts/migrate_schema.py
import argparse
from pathlib import Path

def migrate_enrichment_schema(
    input_path: Path,
    target_version: str,
    dry_run: bool = False,
):
    """Migrate enrichment data to target schema version."""
    data = json.load(open(input_path))

    migrations_applied = []
    for entry in data:
        current_version = entry.get("_schema_version", "1.0.0")

        if current_version < target_version:
            # Apply migration chain
            migrated = apply_migrations(entry, current_version, target_version)
            migrations_applied.append({
                "address": entry["full_address"],
                "from": current_version,
                "to": target_version,
            })

            if not dry_run:
                entry.update(migrated)

    if not dry_run:
        # Atomic save with backup
        atomic_json_save(input_path, data, create_backup=True)

    # Log migration
    log_path = Path("data/migration_history.json")
    append_migration_log(log_path, migrations_applied)

    return migrations_applied

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-version", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    migrate_enrichment_schema(
        Path("data/enrichment_data.json"),
        args.target_version,
        dry_run=args.dry_run,
    )
```

#### Issue #13: Breaking Changes Without Deprecation
**Severity:** HIGH

**Problem:** No deprecation policy for field changes.

**Example:**
```python
# If we rename school_rating -> school_score:
# - Old code breaks immediately
# - No grace period for updates
# - No warning logs
```

**Recommendation:**
```python
# Add deprecation warnings
class EnrichmentDataSchema(BaseModel):
    school_rating: float | None = None

    @field_validator("school_rating", mode="before")
    def warn_deprecated_field(cls, v, info):
        if "school_score" in info.data:
            warnings.warn(
                "Field 'school_score' is deprecated, use 'school_rating' instead. "
                "Will be removed in v3.0.0",
                DeprecationWarning,
                stacklevel=2
            )
            return info.data["school_score"]
        return v
```

#### Issue #14: No Backward Compatibility Testing
**Severity:** MEDIUM

**Problem:** No tests ensure old schemas can be read by new code.

**Missing:**
```python
# tests/test_schema_compatibility.py
def test_v1_schema_loads_in_v2():
    """Ensure v1.0 enrichment files can be loaded by v2.0 code."""
    v1_data = load_fixture("enrichment_v1.0.json")

    # Should auto-migrate
    loaded = load_enrichment(v1_data)

    # Validate all entries are v2.0 compliant
    for entry in loaded:
        EnrichmentDataSchemaV2(**entry)  # Should not raise
```

---
