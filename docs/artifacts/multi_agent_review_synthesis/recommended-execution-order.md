# Recommended Execution Order

### Week 1: Critical Fixes (P0)

**Day 1-2: Scoring Display + 2024 Hardcode**
1. Fix scoring display (500→600) - HIGH IMPACT, LOW EFFORT
2. Replace hardcoded 2024 with `datetime.now().year` - TIME BOMB
3. Regenerate all deal sheets
4. Test on 5 random properties

**Day 3-4: County Data Overwrite Protection**
1. Add conflict detection when county data differs from manual research
2. Log warnings but don't overwrite manual data
3. Generate conflict report
4. Quick win: Prevents data loss immediately (full merge strategy comes later)

**Day 5: Testing + Deployment**
1. Full pipeline test: extract → score → report
2. Verify all 75 properties render correctly
3. Document changes in CHANGELOG.md
4. Git tag: `v1.1.0-critical-fixes`

### Week 2-3: Important Fixes (P1)

**Days 6-7: Dead Code Removal (High-Confidence)**
1. Remove 10 high-confidence dead code items
2. Verify zero imports/references
3. Run full test suite
4. Commit with detailed message

**Days 8-9: Schema Consolidation**
1. Merge 3 duplicate model definitions
2. Update all imports
3. Verify tests pass
4. Document canonical schema locations in README

**Days 10-12: Wire Up LineageTracker**
1. Add tracking calls to extract_county_data.py
2. Add tracking calls to extract_images.py (listing portions)
3. Generate field_lineage.json after pipeline
4. Create validation report showing field coverage

**Days 13-14: Field Mapping Layer**
1. Build canonical field mapping (county ↔ enrichment)
2. Implement merge strategy (manual > county > listing)
3. Update extract_county_data.py to use mapper
4. Test on 5 properties with known conflicts

**Days 15-16: Externalize Buyer Criteria**
1. Create buyer_criteria.yaml
2. Update KillSwitchFilter to load from config
3. Test kill-switch logic unchanged (regression test)
4. Document how to modify criteria for new buyers

**Days 17-18: Configuration Cleanup**
1. Delete MapConfig class
2. Audit and remove unused ArizonaContext fields
3. Consolidate duplicate config values
4. Externalize value zone thresholds

**Day 19-20: Testing + Documentation**
1. Full pipeline regression test
2. Update README with new config system
3. Create "How to Adapt for New Buyers" guide
4. Git tag: `v1.2.0-quality-infrastructure`

### Month 2: Nice-to-Have Fixes (P2)

**Week 1: Cross-Stage Validation**
1. Add validation checkpoints after each phase
2. Generate validation reports
3. Block scoring if critical fields missing

**Week 2: Schema Naming Consistency**
1. Choose canonical naming patterns
2. Create migration script
3. Update enrichment_data.json
4. Update all schemas

**Week 3: Orphaned Metadata Fields**
1. Audit *_source and *_confidence fields
2. Add to schemas if retaining
3. Or delete if LineageTracker replaces them

**Week 4: Dead Code Removal (Medium-Confidence)**
1. Investigate 11 medium-confidence items
2. Delete confirmed dead code
3. Document purpose of code that's alive

---
