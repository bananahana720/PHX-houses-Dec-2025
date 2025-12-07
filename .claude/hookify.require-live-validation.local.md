---
name: require-live-validation
enabled: true
event: stop
pattern: .*
action: warn
---

## ⚠️ Live Validation Reminder

**Per E2 Retro Lesson L1: "Mock tests create false confidence"**

### Before Declaring Complete

**Did you run LIVE validation?**
- [ ] Tested with 5+ real properties (not mocks)
- [ ] Verified data flows end-to-end
- [ ] Checked actual file outputs exist

### E2 Bug Context
ImageProcessor passed all unit tests but:
- String keys vs enum keys mismatch
- 0 extractors created in production
- 0 images saved to disk

**Mock tests hid the bug for 3 days.**

### Live Validation Commands
```bash
# Single property test
/analyze-property "4560 E Sunrise Dr, Phoenix, AZ 85044"

# Batch test (5 properties)
/analyze-property --test

# Verify outputs
ls data/property_images/processed/
cat data/enrichment_data.json | jq '.[-1]'
```

### What to Verify
| Layer | Check |
|-------|-------|
| Extraction | Images downloaded? `ls data/property_images/` |
| Persistence | Data in JSON? `enrichment_data.json` |
| Orchestration | State updated? `work_items.json` |
| Kill-switch | Verdict calculated? Check `kill_switch` field |

### If Skipping Live Validation
Document the reason and accept risk of integration bugs.
