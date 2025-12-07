---
name: block-killswitch-change
enabled: true
event: file
conditions:
  - field: file_path
    operator: regex_match
    pattern: (config/kill_switch|services/kill_switch/.*criteria|CLAUDE\.md)
  - field: new_text
    operator: regex_match
    pattern: (HOA|beds|baths|sqft|lot|garage|sewer|solar|HARD|SOFT|severity|threshold)
action: block
---

## 🛑 Kill-Switch Configuration Change Detected

**Stop-the-line per CLAUDE.md:16**

### What You're Changing
You're modifying kill-switch criteria or thresholds. This requires:

1. **Full recalculation** of ALL properties
2. **Architecture doc updates** across multiple files
3. **Test updates** for new thresholds

### Current Canonical Values (CLAUDE.md)
**5 HARD (instant fail):**
- HOA = $0
- beds >= 4
- baths >= 2
- sqft > 1800
- solar != lease

**4 SOFT (severity accumulation, fail >= 3.0):**
| Criterion | Threshold | Severity |
|-----------|-----------|----------|
| Sewer | City only | 2.5 |
| Year Built | ≤2023 | 2.0 |
| Garage | ≥2 indoor | 1.5 |
| Lot Size | 7k-15k sqft | 1.0 |

### Before Proceeding
1. ⏸️ **STOP** - Get user approval for this change
2. 📝 **Document** - Create ADR for threshold change rationale
3. 🔄 **Recalculate** - Run full pipeline on ALL properties
4. 📊 **Verify** - Check verdict changes across batch
5. 📚 **Update** - All architecture docs referencing kill-switches

### Files That Must Be Updated Together
- `CLAUDE.md` (canonical)
- `config/kill_switch.csv`
- `docs/architecture/kill-switch-architecture.md`
- `src/phx_home_analysis/services/kill_switch/criteria.py`
