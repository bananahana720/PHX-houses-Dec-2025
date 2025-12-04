# Summary of Recommendations

### Must Have (P0)

1. **Background job queuing** (Redis + RQ or Celery)
2. **Worker architecture** (decouple from CLI)
3. **Job model** with status tracking
4. **API endpoint** for job submission + status polling
5. **Atomic state updates** (preserve existing patterns)

### Should Have (P1)

1. **Monitoring dashboard** (queue depth, success rate, source status)
2. **Graceful job cancellation**
3. **Large batch alerts** (>100 new images console warning)
4. **Adaptive rate limiting** (response-based feedback)
5. **Job retry logic** (exponential backoff, max 3 retries)

### Nice to Have (P2)

1. **Distributed workers** (multi-machine)
2. **Proxy auto-rotation** (health checks)
3. **Storage archival** (old images → cold storage)
4. **User isolation** (per-user quotas, audit trail)
5. **Image categorization** metadata sidecar

---
