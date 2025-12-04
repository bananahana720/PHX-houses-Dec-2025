# Data Flow: Current vs. Recommended

### Current (Synchronous)

```
User Input → CLI Parse → ImageExtractionOrchestrator
                             ↓
                        Async Extract
                        (3 concurrent)
                             ↓
              Download & Deduplicate → Update JSON
                             ↓
                          Print Summary
                             ↓
                         Exit (Success/Fail)
```

**Problem**: User blocked for 30+ minutes, single point of failure

### Recommended (Async + Queue)

```
User Request → REST API → Job Queue (Redis)
                              ↓
                    [Job stored + assigned ID]
                              ↓
                        Return 202 Accepted
                      (user gets job_id immediately)
                              ↓
                    [Background Worker picks up]
                              ↓
             Async Extract (3 concurrent props)
                              ↓
         Download & Deduplicate (parallel images)
                              ↓
            Update JSON + Job Status + Metrics
                              ↓
                      [Job marked complete]
                              ↓
User polls /api/extraction/jobs/{id} for progress
    → Can cancel, check status, download results
```

**Benefits**:
- User not blocked
- Multiple requests queued (not dropped)
- Progress visibility in real-time
- Cancellation support
- Worker failures don't lose jobs
- Easy to scale (add more workers)

---
