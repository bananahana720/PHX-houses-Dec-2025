---
name: block-god-entity-growth
enabled: true
event: file
conditions:
  - field: file_path
    operator: regex_match
    pattern: domain/entities\.py$
  - field: new_text
    operator: regex_match
    pattern: ^\s{4}[a-z_]+:\s*(str|int|float|bool|list|dict|Optional|Literal|\|)\s*[=|$]
action: block
---

## 🛑 God Entity Growth Blocked

**You are adding fields to EnrichmentDataSchema.**

### Current State (Antipattern Detected)
Per validation wave findings:
- **EnrichmentDataSchema** has 223 fields (detected antipattern)
- Schema v3.0.0 plan adds 63 MORE fields
- This creates a "God Entity" that knows too much

### Why This Is Blocked
Adding more than 10 fields at once to `entities.py` requires explicit approval because:
1. **Cognitive overload**: 200+ fields are hard to maintain
2. **Serialization risk**: Each field needs `_to_dict()` / `_from_dict()` mapping
3. **Schema migration**: Existing data files may become incompatible
4. **Test coverage**: Each field needs validation tests

### Correct Approach for Large Additions

**Step 1: Get approval**
Document the fields being added and get user confirmation.

**Step 2: Use nested structures (v3.0.0 pattern)**
```python
# Instead of flat fields:
osm_amenity_1: str | None = None
osm_amenity_2: str | None = None
osm_amenity_3: str | None = None

# Use nested value objects:
class OsmData(BaseModel):
    amenities: list[str] = []
    roads: list[OsmRoad] = []

class EnrichmentData(BaseModel):
    osm: OsmData | None = None
```

**Step 3: Follow schema evolution plan**
See `docs/architecture/schema-evolution-plan.md` for:
- v2.1.0: OSM fields (nested structure)
- v2.2.0: Places, Air Quality fields
- v3.0.0: Complete nested refactor

### If This Is Intentional
1. Confirm you are following the schema evolution plan
2. Verify nested structures are used where appropriate
3. Get explicit user approval: "I approve adding X fields to EnrichmentDataSchema"
4. Temporarily disable this rule if approved

**Document the reason and get approval before proceeding.**
