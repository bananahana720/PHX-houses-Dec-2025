# Appendices

### A. File Locations Quick Reference

**Configuration:**
- `config/scoring_weights.yaml` - Scoring system weights
- `config/buyer_criteria.yaml` - NEW: Kill-switch criteria
- `src/phx_home_analysis/config/arizona_context.py` - AZ-specific factors

**Schemas:**
- `src/phx_home_analysis/validation/schemas.py` - Pydantic validation
- `src/phx_home_analysis/domain/entities.py` - Domain models

**Services:**
- `src/phx_home_analysis/services/scoring/scorer.py` - 600-point scoring
- `src/phx_home_analysis/services/kill_switch/filter.py` - Kill-switch logic
- `src/phx_home_analysis/services/quality/lineage_tracker.py` - Data lineage

**Scripts:**
- `scripts/phx_home_analyzer.py` - Main pipeline
- `scripts/extract_county_data.py` - Maricopa County API
- `scripts/extract_images.py` - Listing extraction
- `scripts/deal_sheets/generator.py` - Report generation

**Data:**
- `data/phx_homes.csv` - Listing data
- `data/enrichment_data.json` - Research data
- `data/phx_homes_ranked.csv` - Scored output

### B. Testing Strategy

**Regression Tests (Run After Each Fix):**
1. **Pipeline Smoke Test:**
   ```bash
   python scripts/phx_home_analyzer.py  # Should complete without errors
   ```

2. **Scoring Accuracy Test:**
   ```python
   # Pick 3 known properties, verify scores unchanged
   assert property_123_score == 427  # Known good score
   ```

3. **Kill-Switch Logic Test:**
   ```python
   # Verify hard/soft criteria still work
   assert property_with_hoa.verdict == "FAIL"
   assert property_with_septic.severity >= 2.5
   ```

4. **Deal Sheet Rendering Test:**
   ```bash
   python -m scripts.deal_sheets
   # Verify all 75 sheets render, spot-check 5 random
   ```

**Unit Tests:**
```bash
python -m pytest tests/  # Should pass before AND after changes
```

### C. Rollback Plan

If any fix breaks the system:

1. **Immediate Rollback:**
   ```bash
   git revert HEAD  # Or specific commit
   python scripts/phx_home_analyzer.py  # Verify works
   ```

2. **Isolate Issue:**
   ```bash
   git bisect start
   git bisect bad HEAD
   git bisect good v1.0.0  # Last known good version
   # Follow bisect prompts
   ```

3. **Fix Forward or Revert:**
   - If quick fix (< 1 hour): Fix and commit
   - If complex: Revert and reschedule fix

### D. Success Metrics

**How to Know Fixes Worked:**

1. **Scoring Display Fix:**
   - All deal sheets show "/600 pts"
   - Section maxes correct: 230/180/190
   - User feedback: "Scores make sense now"

2. **2024 Hardcode Fix:**
   - Script runs successfully in Jan 2025
   - Properties built in 2024 correctly excluded
   - No manual code changes needed next year

3. **Data Quality Infrastructure:**
   - `field_lineage.json` exists and populated
   - Validation report shows >90% field coverage
   - Conflict report shows when county/manual differ
   - Zero data loss from overwrites

4. **Dead Code Removal:**
   - Codebase size reduced 15-25%
   - `rg "TODO|FIXME|XXX"` shows fewer orphaned comments
   - New developer onboarding time reduced

5. **Schema Consolidation:**
   - `rg "class SourceStats"` shows ONE definition
   - Import paths consistent across codebase
   - Schema validation catches errors earlier

6. **Configuration Cleanup:**
   - `config/buyer_criteria.yaml` exists
   - Can modify criteria without code changes
   - Documentation explains how to adapt for new buyers

---
