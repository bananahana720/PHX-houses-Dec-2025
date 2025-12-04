# Wave 5: Quality Metrics & Lineage

### Session 5.1: Lineage Tracking (3-4 hours)

**Entry Criteria:**
- Waves 3, 4 complete
- Understanding of data sources

**Tasks:**
1. Create `data/field_lineage.json` structure
2. Update repositories to track lineage on write
3. Add FieldLineage dataclass to domain
4. Implement lineage display in deal sheets

**Commands:**
```bash
# Create lineage tracking module
# Update repositories to populate lineage

# Run pipeline to generate lineage data
python scripts/phx_home_analyzer.py

# Inspect lineage
cat data/field_lineage.json | jq '.[] | select(.address == "123 Main St")'
```

**Exit Criteria:**
- [ ] Lineage tracked for all fields
- [ ] Source attribution correct (csv/api/manual/ai_inference)
- [ ] Confidence levels assigned
- [ ] Timestamps recorded

**Verification:**
```python
# Verify lineage structure
import json
lineage = json.load(open('data/field_lineage.json'))
sample = lineage[0]
assert 'address' in sample
assert 'lot_sqft' in sample
assert sample['lot_sqft']['source'] in ['csv', 'api', 'manual', 'ai_inference', 'default']
```

**Rollback:** Delete `data/field_lineage.json`, restore repositories

---

### Session 5.2: Quality Calculator & CI Gate (2-3 hours)

**Entry Criteria:**
- Session 5.1 complete
- Lineage data populated

**Tasks:**
1. Create `scripts/quality_check.py`
2. Implement quality score calculator
3. Add CI/CD quality gate (fail if <95%)
4. Generate quality dashboard

**Commands:**
```bash
# Create quality_check.py
# Calculate: (Completeness × 0.6) + (High Conf % × 0.4)

# Run quality check
python scripts/quality_check.py --report

# Test CI gate
python scripts/quality_check.py --ci-gate
# Should exit 0 if >=95%, exit 1 if <95%
```

**Exit Criteria:**
- [ ] Quality score calculated correctly
- [ ] CI gate functional (exit codes correct)
- [ ] Quality dashboard generated
- [ ] Target 95% achieved (or gap documented)

**Verification:**
```bash
# Compare to baseline
diff data/quality_baseline.json data/quality_current.json

# Should show improvement in completeness and confidence
```

**Rollback:** Delete `scripts/quality_check.py`

---

### Wave 5 Summary

**Total Sessions:** 2 (5-7 hours)
**Pause Points:** After session 5.1
**Critical Path:** 5.1 → 5.2

**Prerequisites for Wave 6:**
- [ ] Lineage tracking operational
- [ ] Quality metrics at or near 95%
- [ ] CI gate functional

---
