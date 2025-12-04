# Section 5: Quick Wins (Low Effort, High Impact)

| Gap ID | Gap | Effort | Impact | Why Quick Win |
|--------|-----|--------|--------|----------------|
| CA-03 | Tool violation linter | 2d | HIGH | Pre-commit hook; prevents Bash grep | Simple regex scan |
| CA-04 | Skill discovery CLI | 1d | MEDIUM | UX improvement | Just enumerate files + format |
| XT-04 | Index extraction logs | 1d | MEDIUM | Query runs without grepping files | Add JSON index to run_history/ |
| XT-08 | Move constants to env vars | 2d | HIGH | Config without redeploy | Use python-dotenv for missing vars |
| XT-12 | Add "next tier" guidance | 2d | MEDIUM | UX improvement | Simple math: score delta to next tier |
| VB-08 | Flood insurance cost | 2d | LOW | Completeness | FEMA zone → $X/month lookup table |
| CA-02 | Runtime staleness check | 2d | MEDIUM | Data quality gate | Add check_freshness() before agent spawn |

**Recommended Quick Win Order** (7 days total):
```
Day 1: CA-03 (linter) + CA-04 (skill CLI) + XT-04 (log indexing)
Day 2-3: XT-08 (env config) + XT-12 (next tier guidance)
Day 4: CA-02 (runtime staleness)
Day 5: VB-08 (flood insurance)
```

**Expected Wins**: +3 UX improvements, -1 data quality risk, +1 operational capability

---
