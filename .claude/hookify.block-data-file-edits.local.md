---
name: block-data-file-edits
enabled: true
event: file
conditions:
  - field: file_path
    operator: regex_match
    pattern: data/(enrichment_data|work_items|field_lineage|extraction_state|quality_metrics|quality_audit|cache_stats)\.json$
action: block
---

## 🛑 Direct Data File Edit Blocked

**You attempted to directly edit a critical data file.**

### Protected Files (ADR-09: Repository Pattern)
| File | Purpose | Use Instead |
|------|---------|-------------|
| `enrichment_data.json` | Property enrichment data | `JsonEnrichmentRepository` |
| `work_items.json` | Pipeline state and job queue | `WorkItemsRepository` |
| `field_lineage.json` | Field provenance tracking | `LineageRepository` |
| `extraction_state.json` | Extraction session state | `StateManager` |
| `quality_metrics.json` | Data quality scoring | `QualityMetricsService` |
| `quality_audit.json` | Audit trail | `AuditRepository` |
| `cache_stats.json` | Cache performance metrics | `ResponseCache` |

### Why This Is Blocked (Per ADR-09)
Per `docs/architecture/core-architectural-decisions.md` ADR-09:
- **Repository Pattern**: All data access through abstract interfaces
- **Atomic writes**: Services ensure crash safety with `_safe_write()`
- **Provenance tracking**: Direct edits bypass `FieldProvenance` audit
- **Schema validation**: Repositories validate against Pydantic schemas

### Correct Approach

**For enrichment data:**
```python
from phx_home_analysis.repositories import JsonEnrichmentRepository
repo = JsonEnrichmentRepository(Path("data/enrichment_data.json"))
# Use repo.save(), repo.update() methods
```

**For work items:**
```python
from phx_home_analysis.repositories import WorkItemsRepository
repo = WorkItemsRepository(Path("data/work_items.json"))
# Use repo methods with proper state transitions
```

**For testing:** Use `tmp_path` fixture to create isolated test data files.

### Exception Process
If you absolutely need direct access:
1. Document the reason
2. Get user approval
3. Temporarily disable this rule: `enabled: false`
4. Re-enable immediately after
