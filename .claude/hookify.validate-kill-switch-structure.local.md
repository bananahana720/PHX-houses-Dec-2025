---
name: validate-kill-switch-structure
enabled: true
event: file
conditions:
  - field: new_text
    operator: regex_match
    pattern: (8\s*HARD|7\s*(HARD|criteria)|all.*HARD|only.*HARD)
action: warn
---

## ⚠️ Incorrect Kill-Switch Structure Referenced

**Canonical structure: 5 HARD + 4 SOFT (not 8 HARD!)**

### ❌ What You Wrote
References "8 HARD" or implies all criteria are HARD.

### ✅ Correct Structure (CLAUDE.md:38-50)

**5 HARD (instant fail):**
| Criterion | Threshold |
|-----------|-----------|
| HOA | = $0 |
| beds | >= 4 |
| baths | >= 2 |
| sqft | > 1800 |
| solar | != lease |

**4 SOFT (severity accumulation):**
| Criterion | Threshold | Severity |
|-----------|-----------|----------|
| Sewer | City only | 2.5 |
| Year Built | ≤2023 | 2.0 |
| Garage | ≥2 indoor | 1.5 |
| Lot Size | 7k-15k sqft | 1.0 |

**Verdict Logic:**
- Any HARD fail → FAIL
- SOFT severity >= 3.0 → FAIL
- SOFT severity 1.5-3.0 → WARNING
- Otherwise → PASS

### Why This Matters
- E2 Retro identified "8 HARD" as architecture drift
- Derived docs (retros, specs) had stale values
- Root CLAUDE.md is single source of truth
