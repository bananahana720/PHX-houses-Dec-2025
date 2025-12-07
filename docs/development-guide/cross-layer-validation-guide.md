# Cross-Layer Validation Guide

## Purpose

Prevent integration bugs by validating data flows across extraction → persistence → orchestration layers. Based on lessons from Epic 2 remediation.

**From Epic 2 Retrospective:**
> "Code awareness and ensuring functional and software resonance is lacking. The different layers of the system (extraction, persistence, orchestration) weren't communicating properly. Extraction code worked perfectly in isolation, persistence code worked perfectly in isolation, but the connection between them had bugs that only surfaced in production."

**Metaphor:** "An orchestra where every musician plays perfectly, but they're not listening to each other."

## When to Use

Apply this checklist for ANY story that:
- Extracts data from external sources
- Persists data to storage (JSON, database)
- Wires components together in orchestration
- Modifies data schemas or field mappings

## Layer Definitions

| Layer | Responsibility | Key Files |
|-------|---------------|-----------|
| **Extraction** | Fetch data from sources | `services/image_extraction/`, extractors (PhoenixMLSSearchExtractor, ZillowExtractor, RedfintExtractor) |
| **Persistence** | Store/retrieve data | `enrichment_data.json`, repositories (EnrichmentRepository) |
| **Orchestration** | Wire components, coordinate flows | `pipeline.py`, `orchestrator.py`, ImageProcessor |

## Cross-Layer Validation Checklist

### 1. Extraction → Persistence

**Purpose:** Ensure data extracted from external sources matches the schema expected by persistence layer.

**Validation Checkpoints:**
- [ ] **Schema Match**: Extraction output fields match persistence input schema
- [ ] **Type Alignment**: Data types consistent (string vs enum, int vs float, datetime vs str)
- [ ] **Field Coverage**: All extracted fields have persistence mapping (no orphaned fields)
- [ ] **Null Handling**: Extraction nulls handled by persistence layer (Optional types, default values)
- [ ] **Enum Matching**: String values from extraction match enum definitions in persistence

**Verification Test:**
```python
def test_extraction_to_persistence_contract():
    """Validate extraction output matches persistence input schema."""
    extractor = PhoenixMLSSearchExtractor()
    extracted = extractor.extract(test_address)

    # Should not raise ValidationError
    enrichment_repo = EnrichmentRepository()
    persisted = enrichment_repo.save_extracted_data(extracted)

    assert persisted is not None
    assert persisted.address == test_address
```

**Epic 2 Bug Example:**
- **E2.R2 Field Mapping Gap**: 37 fields extracted from PhoenixMLS, only 10 mapped to enrichment_data.json
- **Root Cause**: MLS_FIELD_MAPPING incomplete
- **Fix**: Expanded mapping to 70+ fields in E2.R3

### 2. Persistence → Read-Back

**Purpose:** Ensure data survives save → load cycle without corruption or loss.

**Validation Checkpoints:**
- [ ] **Round-Trip**: Data survives save → load cycle unchanged
- [ ] **Field Preservation**: No fields lost in serialization/deserialization
- [ ] **Type Preservation**: Types maintained (dates, enums, decimals, lists)
- [ ] **Provenance Tracking**: `_field_provenance` metadata persisted correctly

**Verification Test:**
```python
def test_persistence_round_trip():
    """Validate data integrity through save/load cycle."""
    original = create_test_enrichment_data()

    repo = EnrichmentRepository()
    repo.save(original)

    loaded = repo.load_by_address(original.address)

    # Deep equality check
    assert loaded.address == original.address
    assert loaded.hoa_fee == original.hoa_fee
    assert loaded.num_bedrooms == original.num_bedrooms
    assert loaded._field_provenance == original._field_provenance
```

**Epic 2 Bug Example:**
- **E2.R1 Wave 3 Metadata Persistence Gap**: Kill-switch data extracted but not saved to enrichment_data.json
- **Root Cause**: Repository save method didn't include kill-switch fields
- **Fix**: Auto-persist kill-switch metadata on each extraction

### 3. Orchestration → Component Wiring

**Purpose:** Ensure orchestrator correctly instantiates and wires components with proper configuration.

**Validation Checkpoints:**
- [ ] **Instantiation**: Components created with correct parameters (no 0-length lists)
- [ ] **Type Matching**: Orchestrator passes correct types to components (enum vs string)
- [ ] **Configuration**: Components receive correct config (API keys, model tiers, timeouts)
- [ ] **Error Propagation**: Component errors surface to orchestrator (not swallowed)
- [ ] **State Updates**: Orchestrator updates state after component calls

**Verification Test:**
```python
def test_orchestrator_wiring():
    """Validate orchestrator creates and wires components correctly."""
    orchestrator = PipelineOrchestrator()

    # Should create all expected extractors
    assert len(orchestrator.extractors) > 0, "No extractors created"

    # Components should be correct type
    assert all(isinstance(e, BaseExtractor) for e in orchestrator.extractors)

    # Should have correct enum types, not strings
    assert all(hasattr(e, 'source_type') for e in orchestrator.extractors)
    assert all(isinstance(e.source_type, DataSourceType) for e in orchestrator.extractors)
```

**Epic 2 Bug Example:**
- **E2.R1 Wave 2 ImageProcessor Wiring**: 0 extractors created in production
- **Root Cause**: String "phoenixmls" passed to factory expecting `DataSourceType.PHOENIXMLS` enum
- **Fix**: Type contract enforcement in factory methods

### 4. End-to-End Trace

**Purpose:** Validate complete data flow from input → extraction → persistence → output with full traceability.

**Validation Checkpoints:**
- [ ] **Data Flow**: Input → Extraction → Persistence → Output traceable
- [ ] **No Silent Failures**: Errors logged, not swallowed
- [ ] **Provenance**: Field sources tracked in `_field_provenance`
- [ ] **State Consistency**: work_items.json state matches actual pipeline progress
- [ ] **Idempotency**: Re-running same input produces same output

**Verification Test:**
```python
def test_end_to_end_trace():
    """Validate full pipeline data flow with traceability."""
    test_address = "123 Main St, Phoenix, AZ 85001"

    result = pipeline.process(test_address)

    # Data should flow through all layers
    assert result.extraction_complete
    assert result.persistence_complete

    # Check enrichment_data.json updated
    repo = EnrichmentRepository()
    enrichment = repo.load_by_address(test_address)
    assert enrichment is not None

    # Provenance should track field sources
    assert enrichment._field_provenance.get('hoa_fee') in ['phoenixmls', 'zillow']

    # work_items.json should reflect completion
    state = WorkItemRepository()
    item = state.load(test_address)
    assert item.phase >= 1
```

**Epic 2 Bug Example:**
- **E2.R1 Wave 1 State Versioning**: extraction_state.json schema drift caused crashes
- **Root Cause**: No version tracking in state files
- **Fix**: Schema v2.0 with version field, migration logic

## Common Failure Patterns

| Pattern | Symptom | Prevention |
|---------|---------|------------|
| **String vs Enum** | 0 components created | Type contract tests at boundaries |
| **Field Mapping Gap** | Data extracted but not saved | Coverage tests for all fields |
| **Silent Failure** | No errors, but wrong results | Explicit error propagation tests |
| **Mock Blindness** | Tests pass, production fails | Live validation with real data |
| **Type Coercion** | int/float mismatch causes validation error | Explicit type conversions in contracts |
| **Null Propagation** | None values cause crashes downstream | Optional types + default value tests |

## Integration into Story Workflow

Add to story acceptance criteria:
```markdown
## Cross-Layer Validation
- [ ] Extraction → Persistence contract test added
- [ ] Round-trip persistence test added
- [ ] Orchestration wiring test added
- [ ] End-to-end trace test passes
- [ ] Live validation with real data (minimum 5 properties)
```

## Live Validation Protocol

From Epic 2 Retrospective Team Agreement TA3:
> "Live testing validates architecture, not just logic. Mocks hide integration bugs."

**Live Validation Steps:**
1. Select 5 diverse properties (different sources, edge cases)
2. Run full pipeline with real API calls
3. Inspect enrichment_data.json for field coverage
4. Check logs for silent errors
5. Validate provenance tracking
6. Verify state consistency in work_items.json

**Example:**
```bash
# Run live validation
/analyze-property --test --skip-phase=2

# Check results
cat data/enrichment_data.json | jq '.properties[0] | keys'

# Verify provenance
cat data/enrichment_data.json | jq '.properties[0]._field_provenance'
```

## Debugging Cross-Layer Issues

### Symptoms of Cross-Layer Bugs
- Unit tests pass, integration tests fail
- Works in isolation, fails in pipeline
- Correct data extracted, wrong data persisted
- Components created but not functional
- Silent failures with no errors

### Debugging Checklist
1. **Check Type Contracts**: Print types at layer boundaries
   ```python
   print(f"Extractor output type: {type(extracted_data)}")
   print(f"Repository expects: {EnrichmentData.__annotations__}")
   ```

2. **Validate Field Coverage**: Compare extraction fields to persistence schema
   ```python
   extracted_fields = set(extracted_data.keys())
   schema_fields = set(EnrichmentData.model_fields.keys())
   orphaned = extracted_fields - schema_fields
   print(f"Orphaned fields: {orphaned}")
   ```

3. **Trace Data Flow**: Log at each layer boundary
   ```python
   logger.info(f"Extraction: {extracted_data}")
   logger.info(f"Pre-persist: {enrichment_data}")
   logger.info(f"Post-persist: {loaded_data}")
   ```

4. **Check Enum Matching**: Verify string → enum conversions
   ```python
   assert isinstance(source_type, DataSourceType), f"Expected enum, got {type(source_type)}"
   ```

## References

- Epic 2 Retrospective: `docs/sprint-artifacts/epic-2-retro-supplemental-2025-12-07.md`
- Kill-Switch Filter: `src/phx_home_analysis/services/kill_switch/filter.py`
- Image Extraction: `src/phx_home_analysis/services/image_extraction/`
- Enrichment Repository: `src/phx_home_analysis/repositories/enrichment_repository.py`
- Pipeline Orchestrator: `src/phx_home_analysis/pipeline.py`

## Related Documents

- [Testing Guide](testing.md) - Unit and integration test patterns
- [Development Workflow](development-workflow.md) - Story execution workflow
- [Architecture](../architecture/core-architectural-decisions.md) - Layer boundaries

---
*Created: 2025-12-07 | Source: Epic 2 Lessons Learned*
*Action Item: A8 from Epic 2 Supplemental Retrospective*
