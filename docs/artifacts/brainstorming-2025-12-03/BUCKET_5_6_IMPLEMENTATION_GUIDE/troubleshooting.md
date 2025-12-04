# Troubleshooting

### Q: Worker not processing jobs?

**A**: Check:
1. Redis connection: `redis-cli ping`
2. Queue name matches: "image_extraction" in both job and worker
3. Worker logs: `docker logs <worker_container>`
4. RQ Dashboard: http://localhost:9181 (if using docker-compose)

### Q: Job stuck in pending?

**A**:
1. Start worker: `python scripts/worker_image_extraction.py`
2. Check Redis: `redis-cli llen rq:queue:image_extraction`
3. Check job: `redis-cli get rq:job:<job_id>:status`

### Q: Large batch alerts not showing?

**A**: Add to orchestrator summary printing:
```python
if result.unique_images > 100:
    print("\n" + "=" * 70)
    print("WARNING: Large batch of new images")
    # ... detailed output ...
```

---
