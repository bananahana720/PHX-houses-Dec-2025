# Wave 6: Documentation & Integration

### Session 6.1: Update Skill Files (2-3 hours)

**Entry Criteria:**
- All prior waves complete
- System functional end-to-end

**Tasks:**
1. Update `.claude/skills/kill-switch/SKILL.md`
2. Update `.claude/skills/scoring/SKILL.md`
3. Create `.claude/skills/cost-efficiency/SKILL.md`
4. Update `CLAUDE.md` with new weights

**Commands:**
```bash
# Update kill-switch skill
# Replace "all must pass" with weighted threshold documentation

# Update scoring skill
# Add CostEfficiencyScorer (40 pts)
# Update Section B total (180 pts)

# Create new cost-efficiency skill
touch .claude/skills/cost-efficiency/SKILL.md
# Document cost estimation module usage

# Update project CLAUDE.md
# Update scoring system table
```

**Exit Criteria:**
- [ ] All skill files updated
- [ ] New cost-efficiency skill created
- [ ] CLAUDE.md reflects new weights
- [ ] Examples updated with new logic

**Verification:**
```bash
# Verify skill files parse correctly
rg "Section B.*180" .claude/skills/scoring/SKILL.md
rg "weighted threshold" .claude/skills/kill-switch/SKILL.md
```

**Rollback:**
```bash
git checkout .claude/
```

---

### Session 6.2: Integration Tests (3-4 hours)

**Entry Criteria:**
- Session 6.1 complete
- Documentation updated

**Tasks:**
1. Create `tests/integration/test_kill_switch_pipeline.py`
2. Create `tests/integration/test_cost_scoring_integration.py`
3. Create `tests/integration/test_quality_validation.py`
4. Run full integration suite

**Commands:**
```bash
# Create integration tests
mkdir -p tests/integration

# Test kill-switch pipeline
pytest tests/integration/test_kill_switch_pipeline.py -v

# Test cost scoring integration
pytest tests/integration/test_cost_scoring_integration.py -v

# Test quality validation
pytest tests/integration/test_quality_validation.py -v

# Run full suite
pytest tests/ -v --tb=short
```

**Exit Criteria:**
- [ ] All integration tests pass
- [ ] End-to-end workflow verified
- [ ] No regressions detected

**Verification:**
```bash
# Compare to regression baseline
pytest tests/regression/test_baseline.py -v

# Should show intentional changes only (tier assignments due to new weights)
```

**Rollback:** Delete `tests/integration/` directory

---

### Session 6.3: End-to-End Verification (2-3 hours)

**Entry Criteria:**
- Sessions 6.1, 6.2 complete
- All tests passing

**Tasks:**
1. Run full pipeline on all properties
2. Generate all deal sheets
3. Compare before/after metrics
4. Document improvements
5. Final commit

**Commands:**
```bash
# Run full analysis
python scripts/phx_home_analyzer.py --all

# Generate all deal sheets
python -m scripts.deal_sheets --all

# Generate comparison report
python scripts/compare_before_after.py

# Review improvements
cat reports/improvement_summary.txt
```

**Exit Criteria:**
- [ ] All 25 properties processed successfully
- [ ] Deal sheets generated for all
- [ ] Quality score >=95% (or documented gap)
- [ ] Tier assignments validated
- [ ] No critical bugs

**Final Verification Checklist:**
- [ ] Kill-switch verdicts correct (PASS/WARNING/FAIL)
- [ ] [H]/[S] markers displaying
- [ ] Severity scores accurate
- [ ] Monthly costs displayed
- [ ] $4k warnings showing when applicable
- [ ] Cost efficiency scores in breakdown
- [ ] Section B totals 180 pts (not 160)
- [ ] Data quality improved vs baseline
- [ ] Field lineage tracked
- [ ] All tests passing

**Final Commit:**
```bash
# Stage all changes
git add .

# Commit with detailed message
git commit -m "Complete scoring system improvements (Waves 0-6)

- Implement weighted threshold kill-switch (3 HARD, 4 SOFT)
- Add cost estimation module (40-pt scoring criterion)
- Establish data quality validation (>95% target)
- Integrate AI-assisted triage for missing fields
- Add field lineage tracking
- Update documentation and skills

Closes #[issue-number]"

# Push to remote
git push origin main
```

**Rollback (Complete):**
```bash
# Nuclear option: revert all commits
git log --oneline  # Find commit before Wave 0
git revert --no-commit <commit-hash>..HEAD
git commit -m "Revert scoring improvements"
```

---

### Wave 6 Summary

**Total Sessions:** 3 (7-10 hours)
**Pause Points:** After sessions 6.1, 6.2
**Critical Path:** 6.1 → 6.2 → 6.3

**Final Deliverables:**
- [ ] All code changes committed
- [ ] Documentation updated
- [ ] Tests passing (unit + integration + regression)
- [ ] Quality metrics at or near 95%
- [ ] System functional end-to-end

---
