# Kill-Switch Documentation Consistency Cleanup

**Created:** 2025-12-07
**Priority:** MEDIUM (Non-blocking for E3, but should be done during E3)
**Estimated Effort:** 2-4 hours

## Background

Epic 2 refactored kill-switch architecture from "all HARD" to "5 HARD + 4 SOFT" with severity accumulation. Primary architecture documents were updated, but validation audit found 18+ secondary files with outdated references.

## Correct Values

```
Kill-Switch Classification: 5 HARD + 4 SOFT (9 total)

HARD Criteria (instant fail):
1. HOA = $0
2. Solar ≠ lease
3. Beds >= 4
4. Baths >= 2
5. Sqft > 1800

SOFT Criteria (severity weighted):
1. Sewer = city (2.5)
2. Year Built ≤ 2023 (2.0)
3. Garage ≥ 2 indoor (1.5)
4. Lot Size 7k-15k (1.0)

Thresholds:
- FAIL: severity >= 3.0
- WARNING: severity >= 1.5

Scoring: 605 pts max
Tiers: Unicorn >=484, Contender 363-483, Pass <363
```

## Files Requiring Updates

### Scripts (3 files)
- [ ] `scripts/lib/kill_switch.py` - Lines 483, 491, 765, 812: "7 HARD criteria"
- [ ] `scripts/phx_home_analyzer.py` - Unicorn threshold ">480" → ">=484"

### Source Code Comments (4 files)
- [ ] `src/phx_home_analysis/CLAUDE.md:71` - "8 HARD criteria"
- [ ] `src/phx_home_analysis/services/image_extraction/metadata_persister.py:23` - "8 HARD"
- [ ] `src/phx_home_analysis/config/constants.py` - Comments say "all HARD"

### Test Files (5 files)
- [ ] `tests/unit/test_lib_kill_switch.py` - Lines 292, 423, 515, 663
- [ ] `tests/unit/test_config_schemas.py:165` - "8 HARD fields"
- [ ] `tests/unit/test_config_loader.py` - Lines 115, 170, 197, 466
- [ ] `tests/unit/services/image_extraction/test_phoenix_mls_metadata.py:84`
- [ ] `tests/unit/.session_summary.txt` - Lines 37, 45

### Local Hook Files (2 files)
- [ ] `.claude/hookify.require-claude-md-update.local.md:27`
- [ ] `.claude/hookify.adr-awareness-session.local.md:82`

### Documentation (3 files)
- [ ] `docs/schemas/work_items_schema.md` - Lines 308, 314-315: "600-point"

## Approach

1. **Search Pattern:** `rg -i "(7|8)\s*(HARD|hard)|all\s*HARD" --type md --type py`
2. **Replace With:** "5 HARD + 4 SOFT" or specific correct value
3. **Verify:** Run `python .claude/hooks/architecture-consistency-check.py`

## Acceptance Criteria

- [ ] All files in checklist updated
- [ ] No matches for `(7|8)\s*HARD` in codebase
- [ ] Architecture consistency hook passes
- [ ] Tests still pass after comment updates

## Notes

- Test file comments are low risk (don't affect behavior)
- Source code comments should be updated for accuracy
- Scripts may need logic review (not just comment updates)

---
*Generated from Epic 2 validation audit*
