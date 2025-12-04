# Risk Mitigation

### Risk: Data Loss on Redis Restart

**Mitigation**:
- Jobs persisted to disk (`data/jobs/{id}.json`)
- Resume from last known state (property_last_checked)
- URL tracker prevents re-downloading

### Risk: Worker Crash During Extraction

**Mitigation**:
- State saved after each property completes
- Next worker picks up from last good state
- No data loss (only lost current property, will retry)

### Risk: Rate Limiting Causes Extraction Failure

**Mitigation**:
- Circuit breaker disables source temporarily
- Other sources continue
- Adaptive rate limiting adjusts on 429/503
- Retry logic with exponential backoff

### Risk: Disk Fills Up With Images

**Mitigation**:
- Image storage monitoring (quota alerts)
- Retention policy (archive > 90 days)
- Auto-cleanup on disk warning

---
