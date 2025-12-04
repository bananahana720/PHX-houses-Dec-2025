# FAQ & Troubleshooting

### Q: What if worker crashes mid-extraction?

**A**: Job stays in Redis queue. Next worker picks it up. State resumption via `property_last_checked` skips already-processed properties.

### Q: Can I keep synchronous CLI behavior?

**A**: Yes. Option 1: CLI polls job status until done (transparent async). Option 2: Add `--sync` flag for blocking behavior.

### Q: How do I monitor queue depth?

**A**: Prometheus export via `/metrics` endpoint. Key metric: `rq_job_queue_depth{queue="image_extraction"}`.

### Q: What if Redis goes down?

**A**: Jobs in Redis are lost. Mitigation: Use Redis persistence (RDB snapshots). Or fallback to local queue file (less ideal).

### Q: How do I scale to multiple machines?

**A**: All workers point to same Redis instance. Add workers on new machines. Load automatically distributed.

---
