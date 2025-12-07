---
name: require-cross-layer-tests
enabled: true
event: file
conditions:
  - field: file_path
    operator: regex_match
    pattern: src/phx_home_analysis/services/(image_extraction|scoring|kill_switch)/.*\.py$
  - field: new_text
    operator: regex_match
    pattern: (def\s+(extract|process|persist|save|update)|async\s+def)
action: warn
---

## ⚠️ Cross-Layer Validation Required

**Per E2 Retro Lesson L6: "Cross-layer resonance is critical"**

### What You're Changing
Service code that spans extraction → persistence → orchestration layers.

### E2 Bug Reference
ImageProcessor had:
- ✅ Unit tests passing in isolation
- ❌ String vs enum mismatch at integration boundary
- ❌ 0 extractors created in production

### Required Tests

**1. Extraction → Persistence Contract Test:**
```python
def test_extracted_data_persists_correctly():
    # Extract data
    extracted = extractor.extract(url)

    # Persist through repository
    repo.save(extracted)

    # Verify round-trip
    loaded = repo.get_by_address(extracted.address)
    assert loaded.field == extracted.field
```

**2. Type Contract at Boundary:**
```python
def test_orchestrator_receives_correct_types():
    result = orchestrator._create_extractors(sources)
    assert isinstance(result["PHOENIX_MLS"], PhoenixMLSExtractor)
    # NOT string keys!
```

**3. End-to-End Trace:**
```python
def test_full_pipeline_data_flow():
    # Phase 0 → 1 → 2 → 3
    pipeline.run(["123 Main St"])

    # Verify all layers connected
    assert repo.get_by_address("123 Main St").scoring.total > 0
```

### Before Proceeding
- [ ] Add contract test for this change
- [ ] Verify type consistency at boundaries
- [ ] Run live validation (not just mocks)
