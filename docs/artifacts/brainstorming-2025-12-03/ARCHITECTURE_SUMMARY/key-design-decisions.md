# Key Design Decisions

### Why Redis + RQ (not Celery)?

| Aspect | RQ | Celery |
|--------|----|----|
| **Setup Complexity** | Simple (Redis only) | Complex (Broker + Workers + Config) |
| **Learning Curve** | Gentle (< 1 day) | Steep (2-3 days) |
| **Scaling Path** | Good (easy workers) | Excellent (high-performance) |
| **Ops Burden** | Low | High |
| **Recommendation** | **MVP (v1)** | Upgrade to (v2+) |

**Decision**: Start with RQ (faster MVP). Migrate to Celery later if needed (transparent to users).

### Why Atomic Writes?

Current code uses:
```python
fd, temp_path = tempfile.mkstemp()
with os.fdopen(fd, 'w') as f:
    json.dump(data, f)
os.replace(temp_path, original_path)  # Atomic on POSIX & Windows
```

**Benefits**:
- Prevents partial writes if crash mid-flush
- No lock contention (atomic rename)
- Works on all platforms (POSIX, Windows, NFS)
- Safe even with multiple workers writing same file

**Must preserve** in job model + state updates.

### Why Persistent Job Storage?

Jobs stored in two places:
1. **Redis** (primary, fast access): Job status, progress, expiry
2. **Disk** (`data/jobs/{id}.json`, backup): Audit trail, recovery after Redis restart

**Benefits**:
- Redis restart doesn't lose jobs (can resume)
- Audit trail for compliance
- Disaster recovery (can query disk if Redis corrupted)
- Simple (JSON file per job)

---
