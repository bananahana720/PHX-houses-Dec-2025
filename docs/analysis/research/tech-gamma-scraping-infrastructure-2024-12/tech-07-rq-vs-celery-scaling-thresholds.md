# TECH-07: RQ vs Celery Scaling Thresholds

### Overview Comparison

| Feature | RQ (Redis Queue) | Celery |
|---------|------------------|--------|
| **Broker Support** | Redis only | Redis, RabbitMQ, SQS, etc. |
| **OS Support** | Unix only (fork required) | Cross-platform |
| **Language Support** | Python only | Multi-language |
| **Learning Curve** | Minimal | Substantial |
| **Installation Size** | ~200KB | ~2.5MB |
| **Built-in Scheduling** | No (requires rq-scheduler) | Yes (celery beat) |
| **Priority Queues** | Simple, effective | Requires multiple workers |

### Performance Benchmarks [High Confidence]

**Test Conditions:** 20,000 jobs, 10 workers, MacBook Pro M2 Pro 16GB, Redis broker

| Task Queue | Time to Complete | Tasks/Second |
|------------|------------------|--------------|
| Dramatiq | ~5s | ~4,000 |
| Taskiq | ~5s | ~4,000 |
| Huey | ~6s | ~3,333 |
| Celery (threads) | ~12s | ~1,667 |
| Celery (processes) | ~18s | ~1,111 |
| **RQ** | **~51s** | **~392** |

**Key Finding:** RQ is approximately 4x slower than Celery for high-throughput scenarios.

### Redis Throughput with Celery [High Confidence]

- Redis sustains **7,000+ tasks/second** with 100 parallel workers
- Message acknowledgment: <10ms (Redis) vs up to 40ms (RabbitMQ)
- Redis outperforms RabbitMQ for latency but lacks durability guarantees

### Memory Considerations

**RQ Limitation:** [High Confidence]
- All messages stored in Redis memory
- Redis can fill up and stop accepting writes under heavy load
- One team reported "consistently dealing with RQ breaking because Redis was full"

**Celery Solutions:**
- RabbitMQ broker offloads messages to disk
- `worker_max_tasks_per_child` - restart workers after N tasks
- `worker_max_memory_per_child` - restart workers at memory threshold
- **Issue:** Celery Flower monitoring has memory leak issues

### Operational Complexity

**RQ:** [High Confidence]
```
Simple setup:
1. Install RQ
2. Start Redis
3. Define tasks as functions
4. Start workers
```

**Celery:** [High Confidence]
```
Complex setup:
1. Install Celery + dependencies
2. Configure broker (Redis/RabbitMQ)
3. Configure result backend
4. Define Celery app with settings
5. Define tasks with decorators
6. Configure task routing
7. Start workers with proper concurrency
8. (Optional) Start beat scheduler
9. (Optional) Start Flower monitoring
```

### When to Migrate from RQ to Celery

**Remain on RQ when:** [High Confidence]
- Processing <1,000 tasks/hour
- Tasks are independent (no complex workflows)
- Already using Redis for caching
- Team prefers simplicity over features
- Unix-only deployment acceptable

**Migrate to Celery when:** [High Confidence]
- Processing >10,000 tasks/minute consistently
- Experiencing queue backups / increasing latency
- Need message durability guarantees
- Require periodic task scheduling
- Complex task workflows (chains, groups, chords)
- Multi-language task producers
- Need Windows support

### Scaling Guidelines

| Scale | Recommendation | Notes |
|-------|---------------|-------|
| <100 tasks/hour | RQ | Minimal overhead |
| 100-1,000/hour | RQ | Add workers as needed |
| 1,000-10,000/hour | RQ or Celery | Monitor queue latency |
| >10,000/hour | Celery | RQ will struggle |
| >100,000/hour | Celery + RabbitMQ | Redis memory limits |

### Autoscaling Approaches

**RQ:** Manual horizontal scaling (add more workers)

**Celery Built-in:**
```bash
celery -A app worker --autoscale=10,3  # Scale 3-10 processes
```
*Note: Built-in autoscaling reported as unreliable by some users* [Medium Confidence]

**Kubernetes + KEDA:** [High Confidence]
- Event-driven autoscaling based on queue metrics
- Scale based on `(active_tasks + queue_length) / available_workers`
- Proactive scaling before queue buildup

### Recommendation for PHX Houses

**Current Recommendation: RQ** [High Confidence]

Rationale:
- PHX Houses processes ~50-100 properties at a time
- Each property = ~5-10 tasks (county, listing, map, images, synthesis)
- Total: ~500-1,000 tasks per analysis run
- This is well within RQ's comfortable range

**Migration Trigger Points:**
1. Queue latency consistently >30 seconds
2. Redis memory consistently >80% utilized
3. Need for scheduled recurring analysis
4. Multi-region deployment requirements

---
