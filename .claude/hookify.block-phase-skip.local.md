---
name: block-phase-skip
enabled: true
event: bash
pattern: analyze-property.*--skip-phase[= ]*[01]|phase.*[2-4].*(?!phase.*[01])
action: warn
---

## ⚠️ Phase Dependency Warning

**Stop-the-line per CLAUDE.md:16**

### Pipeline Phase Dependencies
```
Phase 0 (County API) → Phase 1 (Listing + Map) → Phase 2 (Images) → Phase 3 (Synthesis)
```

### Critical Dependencies
| Phase | Requires | Provides |
|-------|----------|----------|
| Phase 0 | - | lot_sqft, year_built, garage_spaces |
| Phase 1 | Phase 0 | images, HOA, schools, orientation |
| Phase 2 | Phase 1 | interior/exterior scores (Section C) |
| Phase 3 | All | total score, tier, deal sheet |

### ⚠️ Skipping Phase 0 or 1
If you skip early phases:
- Kill-switch evaluation will be incomplete
- Scoring will have missing data (scored as 0)
- Phase 2 image assessment CANNOT proceed without images

### Correct Usage
```bash
# Full pipeline (recommended)
/analyze-property --all

# Resume from failure
/analyze-property --resume

# Test mode (first 5)
/analyze-property --test
```

### If You Must Skip
Document the reason and accept:
- Incomplete kill-switch evaluation
- Lower scores due to missing data
- Potential Phase 2 failures
