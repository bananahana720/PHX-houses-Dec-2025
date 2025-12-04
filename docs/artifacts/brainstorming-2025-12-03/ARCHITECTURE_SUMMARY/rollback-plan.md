# Rollback Plan

If Phase 1 implementation causes issues:

1. **Keep existing CLI working**: `--sync` mode that blocks (original behavior)
2. **Fallback to Redis in-memory**: Use local RQ setup, no external Redis
3. **Disable background jobs**: Set `ENABLE_ASYNC_JOBS=false` to use sync mode
4. **Downtime**: < 5 minutes (restart workers, no data loss)

**No data loss** because:
- Job state persists to disk
- Image metadata unchanged
- State resumption compatible

---
