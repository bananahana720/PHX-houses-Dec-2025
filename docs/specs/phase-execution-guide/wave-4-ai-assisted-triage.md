# Wave 4: AI-Assisted Triage

### Session 4.1: Field Inferencer (4-5 hours)

**Entry Criteria:**
- Wave 3 complete
- Claude API key configured
- Understanding of field inference requirements

**Tasks:**
1. Create `src/phx_home_analysis/services/ai_enrichment/field_inferencer.py`
2. Implement triage tagging system
3. Create prompt templates for common field types
4. Add confidence scoring

**Commands:**
```bash
# Create directory
mkdir -p src/phx_home_analysis/services/ai_enrichment

# Create field_inferencer.py
# Implement FieldInferencer class

# Test on sample missing field
python -c "
from src.phx_home_analysis.services.ai_enrichment.field_inferencer import FieldInferencer

inferencer = FieldInferencer()
result = inferencer.infer_field(
    address='123 Main St, Phoenix, AZ',
    field_name='orientation',
    context={'has_street_view': True}
)
print(f'Inferred: {result.inferred_value}, Confidence: {result.confidence}')
"
```

**Exit Criteria:**
- [ ] FieldInferencer class created
- [ ] Triage tagging works
- [ ] Prompt templates defined
- [ ] Confidence scoring implemented
- [ ] Claude Haiku integration tested

**Verification:**
- Run inference on 3-5 properties with missing fields
- Verify confidence scores reasonable (high/medium/low)
- Check cost (<$0.01 per inference with Haiku)

**Rollback:** Delete `ai_enrichment/` directory

---

### Session 4.2: Integration & Testing (2-3 hours)

**Entry Criteria:**
- Session 4.1 complete
- Field inferencer working

**Tasks:**
1. Integrate with validation pipeline
2. Create workflow: validation fail → triage tag → AI inference
3. Test on properties with missing critical fields
4. Document inference results

**Commands:**
```bash
# Run enrichment with AI triage
python scripts/enrich_properties.py --ai-triage --limit 10

# Review inference results
cat data/ai_inferences.json

# Verify quality improvement
python scripts/quality_check.py
```

**Exit Criteria:**
- [ ] AI triage integrated into pipeline
- [ ] Inference results saved to data file
- [ ] Quality metrics improved (measure vs baseline)
- [ ] Cost tracking functional

**Verification:**
```bash
# Compare quality before/after
python scripts/quality_baseline.py  # Re-run to see improvement
```

**Rollback:**
```bash
git checkout src/phx_home_analysis/services/
rm data/ai_inferences.json
```

---

### Wave 4 Summary

**Total Sessions:** 2 (6-8 hours)
**Pause Points:** NONE (complete Wave 4 atomically)
**Critical Path:** 4.1 → 4.2 (sequential)

**Prerequisites for Wave 5:**
- [ ] Field inferencer working
- [ ] AI triage integrated
- [ ] Quality improvement measurable

---
