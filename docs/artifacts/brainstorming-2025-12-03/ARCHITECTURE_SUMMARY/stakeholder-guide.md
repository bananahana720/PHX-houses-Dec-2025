# Stakeholder Guide

### For Product Managers

**What changes for users?**
- Users no longer blocked during image extraction (UX improvement)
- Can cancel extraction jobs mid-process
- Real-time progress visibility (via dashboard or API)
- Better error messages (job logs persist)

**When is it ready?**
- MVP (Phase 1): Q1 2025 (4-5 weeks)
- Production (Phase 1 + 2): Q2 2025 (8 weeks)
- Enterprise (All 3 phases): Q3 2025 (12 weeks)

### For Backend/DevOps Engineers

**What to implement first?**
1. Job model (simplest, lowest risk)
2. Redis + RQ setup (foundation)
3. Job function (core logic)
4. Worker process (handles execution)
5. API endpoints (user interface)

**How to test locally?**
```bash
# Start dev stack
docker-compose -f docker/docker-compose.yml up

# In another terminal, submit job
curl -X POST http://localhost:5000/api/extraction/jobs \
  -H "Content-Type: application/json" \
  -d '{"properties": [], "sources": ["zillow"]}'

# Check job status
curl http://localhost:5000/api/extraction/jobs/{job_id}

# View RQ Dashboard
# http://localhost:9181
```

### For QA/Testing

**Key test scenarios**:
1. Job submission returns UUID immediately
2. Worker picks up job and processes
3. Job status transitions: pending → in_progress → completed
4. Failed job marked with error message
5. Resume partially completed job
6. Parallel jobs don't interfere with each other
7. Job cancellation stops extraction and cleans up
8. Redis restart doesn't lose jobs

**Performance benchmarks**:
- Submission latency: < 100ms
- Status polling: < 50ms
- Extract 1 property: 12-18 min (unchanged)
- Extract 10 concurrent properties: 12-18 min (3x throughput vs. sequential)

---
