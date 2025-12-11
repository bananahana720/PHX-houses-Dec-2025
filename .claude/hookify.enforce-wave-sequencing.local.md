---
name: enforce-wave-sequencing
enabled: true
event: all
conditions:
  - field: user_prompt
    operator: regex_match
    pattern: (?i)(Task\(|launch.*agent|spawn.*subagent|delegate.*to)
action: warn
---

## 🌊 Wave Sequencing Check Required

**Before launching agents, verify wave dependencies are satisfied.**

### Wave Sequencing Rules

#### Parallel Waves (Non-Destructive)
Agents that can run simultaneously:
- `listing-browser` + `map-analyzer` (both read-only)
- Multiple `image-assessor` instances (independent properties)

#### Sequential Waves (Destructive)
Must complete before next wave:
1. **Wave 1**: Data collection (listing-browser, county-assessor)
2. **Wave 2**: Analysis (map-analyzer, depends on Wave 1 data)
3. **Wave 3**: Assessment (image-assessor, depends on Wave 2)
4. **Wave 4**: Synthesis (scoring, depends on all previous)

### Pre-Launch Checklist

Before calling Task():

- [ ] **Dependencies met?** Previous wave's outputs exist
- [ ] **No conflicts?** Agents won't write to same files
- [ ] **Correct agent?** Match task type to agent specialty
- [ ] **Context provided?** Agent has required property address/data

### Agent Selection Guide

| Task Type | Agent | When |
|-----------|-------|------|
| Listing extraction | `listing-browser` | Need property photos, HOA, price |
| Location analysis | `map-analyzer` | Need schools, safety, orientation |
| Visual assessment | `image-assessor` | Have images, need condition scores |
| Implementation | `dev` | Code changes needed |

### File Access Patterns

Verify no write conflicts:
```
listing-browser → writes: data/images/, data/listings/
map-analyzer    → writes: data/enrichment_data.json (location fields)
image-assessor  → writes: data/enrichment_data.json (assessment fields)
```

**If uncertain about dependencies, check data/work_items.json for phase status.**
