# Rollback Plan

If Phase 2 implementation causes problems:

1. Revert `_navigate_with_stealth()` to original simple navigation
2. Keep Phase 1 page type validation (safe)
3. Return to empty list behavior (better than wrong images)
4. File bug for future Phase 2 implementation

```bash
git revert <commit-hash>  # Revert to Phase 1 only
```

---
