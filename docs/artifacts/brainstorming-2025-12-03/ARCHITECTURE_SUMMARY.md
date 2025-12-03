# Architecture Analysis Summary
## Buckets 5 & 6: Image Pipeline & Scraping/Automation

**Date**: 2025-12-03
**Status**: Comprehensive analysis complete
**Deliverables**: 3 documents (this summary + 2 detailed guides)

---

## Documents Generated

### 1. `BACKEND_ARCHITECTURE_ANALYSIS_BUCKETS_5_6.md` (20+ pages)

**Complete architectural analysis** covering:
- Current image pipeline implementation
- Stealth scraping patterns & anti-bot techniques
- Data flow from scrape → storage → processing
- Gap analysis (current vs. vision)
- Comprehensive recommendations for production readiness

**Key sections**:
- 5.1-5.5: Image pipeline (storage, naming, deduplication, linking, categorization)
- 6.1-6.6: Scraping architecture (stealth, circuit breakers, concurrency, state persistence)
- Gap Analysis (Buckets 5 & 6 gaps)
- Architectural Recommendations (Phase 1: Immediate)
- Implementation Roadmap (Q1-Q3 2025)
- Data Flow comparison (Current vs. Recommended)
- Critical Implementation Notes
- Cost & Resource Implications
- FAQ & Troubleshooting
- Conclusion & References

### 2. `BUCKET_5_6_IMPLEMENTATION_GUIDE.md` (15+ pages)

**Step-by-step implementation** for Phase 1:
- Quick start with dependencies
- Redis setup (dev & production)
- 6-step implementation plan (Days 1-5):
  1. Job Model (ImageExtractionJob dataclass)
  2. Redis Queue Setup (Config)
  3. Job Function (extract_images_job)
  4. Worker Process (ImageExtractionWorker)
  5. API Endpoints (REST for job submission)
  6. CLI Integration (--async, --job-id flags)
- Complete code examples for all components
- Unit & integration tests
- Docker Compose setup
- Prometheus metrics
- Troubleshooting guide

---

## Executive Summary

### Current State

**Strengths**:
✓ Sophisticated perceptual hashing with LSH optimization (O(n) vs O(n²))
✓ Robust stealth scraping with nodriver + curl_cffi
✓ Circuit breaker pattern for resilience (automatic recovery)
✓ Atomic state persistence (crash recovery)
✓ Metadata-rich image naming convention
✓ Clean service separation (extractors, deduplicators, orchestrators)

**Critical Gaps**:
✗ All work synchronous/CLI-driven (no background jobs)
✗ No job queue (single user at a time)
✗ No worker pool (single process bottleneck)
✗ No progress visibility (CLI blocks for 30+ minutes)
✗ No job cancellation (must kill process)
✗ No user isolation (file-based access only)
✗ Limited concurrency (3 properties max)

### Maturity Assessment

| Component | Current | Target | Gap |
|-----------|---------|--------|-----|
| **Image Storage** | Good | Good | Minimal |
| **Deduplication** | Excellent | Excellent | None |
| **Naming Convention** | Excellent | Excellent | None |
| **Stealth Scraping** | Very Good | Very Good | Minor (rate limiting) |
| **State Persistence** | Good | Good | Minimal |
| **Background Jobs** | **MISSING** | **P0** | **CRITICAL** |
| **Job Queue** | **NOT IMPLEMENTED** | **P0** | **CRITICAL** |
| **Worker Processes** | **NOT IMPLEMENTED** | **P0** | **CRITICAL** |
| **User Isolation** | None | **P1** | **HIGH** |
| **Monitoring** | Basic | **P1** | **MEDIUM** |

### Risk Assessment

**High Risk** (Blocks Production):
- No background job infrastructure (single user only)
- No job persistence (lost on crash)
- No progress tracking (black box)
- User requests blocked for 30+ minutes
- Limited scalability (3 concurrent properties max)

**Medium Risk** (Operational):
- No worker health monitoring
- Limited rate limiting (circuit breaker only)
- No job-level error recovery
- Difficult to debug hung processes

**Low Risk** (Data Quality):
- Image deduplication robust
- Metadata linking solid
- State persistence atomic
- Source isolation good (circuit breakers)

---

## Recommended Implementation Path

### Phase 1 (Q1 2025): Foundation - **CRITICAL**

**Effort**: 4-5 weeks
**Cost**: +$67/month infrastructure
**Impact**: Unblocks multi-user, improves UX, enables scaling

**Deliverables**:
1. Redis + RQ job queue setup
2. ImageExtractionJob model + persistence
3. extract_images_job function (worker-friendly)
4. ImageExtractionWorker process
5. REST API endpoints for job management
6. CLI integration (--async, --job-id, --wait flags)
7. Docker Compose for local dev
8. Prometheus metrics export

**Acceptance Criteria**:
- [ ] User can submit extraction job and get UUID immediately
- [ ] User can check job status without blocking
- [ ] Job resumable on Redis restart
- [ ] Worker can process 3+ concurrent jobs
- [ ] Metrics available in Prometheus
- [ ] RQ Dashboard shows queue, workers, job history
- [ ] Backward compatible CLI (--sync mode or default polling)

### Phase 2 (Q2 2025): Observability & Scale

**Effort**: 2-3 weeks
**Cost**: +$20/month (Grafana, alerting)
**Impact**: Production-ready monitoring, auto-recovery

**Deliverables**:
1. Grafana dashboard (queue depth, success rate, source status)
2. Alerting rules (stuck jobs, worker down, rate limit)
3. Adaptive rate limiting (response-based feedback)
4. Multi-worker support (horizontal scaling)
5. Job cancellation (graceful cleanup)
6. Run history API endpoint

**Acceptance Criteria**:
- [ ] Dashboard shows queue depth, worker health, source status
- [ ] Alerts fire for stuck jobs (>1h)
- [ ] Rate limiting adjusts based on 429/503 responses
- [ ] 2+ workers can run independently
- [ ] Job cancellation gracefully stops extraction

### Phase 3 (Q3 2025): Advanced Features

**Effort**: 2-3 weeks
**Cost**: Variable (proxy services, S3)
**Impact**: Distributed scraping, enterprise-ready

**Deliverables**:
1. Distributed worker pool (multi-machine)
2. Automatic proxy rotation + health checks
3. Storage archival (old images → cold storage)
4. Image categorization sidecar metadata
5. User-based quotas & audit trail

**Acceptance Criteria**:
- [ ] Workers on 3+ machines can pull from same queue
- [ ] Proxies rotate automatically with health checks
- [ ] Images > 90 days archived to S3 Glacier
- [ ] Image categorization stored separately from filename
- [ ] Audit log tracks all extractions by user

---

## Key Design Decisions

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

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                              │
│  CLI (--async)  │  REST API  │  RQ Dashboard  │  Monitoring (Grafana) │
└────────┬────────┴──────┬─────┴────────┬───────┴────────────┬────────┘
         │               │              │                    │
         v               v              v                    v
    ┌──────────────────────────────────────────────────────────────┐
    │                    Job Queue (Redis)                         │
    │   FIFO queue: pending → in_progress → completed|failed      │
    │   Metrics: queue depth, job TTL, worker list               │
    └──────────┬─────────────────────────────────────────────────┘
               │
    ┌──────────┴──────────────────────────────────────────────────┐
    │            Image Extraction Worker Pool                     │
    │   Worker #1    │   Worker #2    │   Worker #3   │ ...       │
    │  (3 concurrent │   (3 concurrent│  (3 concurrent │          │
    │   properties)  │    properties) │   properties)  │          │
    └──────────┬──────────────────────────────────────────────────┘
               │
    ┌──────────┴──────────────────────────────────────────────────┐
    │          Image Extraction Orchestrator                      │
    │  - Stealth browser pool (nodriver + curl_cffi)             │
    │  - Source extractors (Zillow, Redfin, Maricopa, MLS)       │
    │  - Circuit breaker per source                              │
    │  - URL tracker (avoid re-download)                         │
    └──────────┬──────────────────────────────────────────────────┘
               │
    ┌──────────┴──────────────────────────────────────────────────┐
    │          Image Processing Pipeline                          │
    │  - Download (curl_cffi, parallel)                          │
    │  - Standardize (EXIF strip, resize)                        │
    │  - Deduplicate (perceptual hash + LSH)                     │
    │  - Categorize (AI vision, metadata tagging)                │
    │  - Store (hash-based folders, atomic writes)               │
    └──────────┬──────────────────────────────────────────────────┘
               │
    ┌──────────┴──────────────────────────────────────────────────┐
    │               Persistent Storage                            │
    │  data/property_images/                                      │
    │  ├── processed/{hash}/*.png (categorized)                  │
    │  └── metadata/                                             │
    │      ├── extraction_state.json (progress)                 │
    │      ├── image_manifest.json (inventory)                  │
    │      ├── hash_index.json (perceptual hashes)              │
    │      ├── address_folder_lookup.json (address → hash)      │
    │      ├── url_tracker.json (URL dedup)                     │
    │      ├── pipeline_runs.json (audit trail)                 │
    │      └── job_status.json (job persistence)                │
    └──────────────────────────────────────────────────────────────┘
```

---

## Code Organization

### Files to Create (Phase 1)

```
src/phx_home_analysis/
├── jobs/
│   ├── __init__.py
│   ├── models.py                      # ImageExtractionJob dataclass
│   └── image_extraction.py            # extract_images_job + enqueue function
├── workers/
│   ├── __init__.py
│   └── image_extraction.py            # ImageExtractionWorker class
├── api/                               # (Optional, if REST endpoint desired)
│   ├── __init__.py
│   └── extraction_routes.py           # Flask/FastAPI routes
├── metrics/                           # (Optional, for Prometheus)
│   ├── __init__.py
│   └── extraction.py                  # Counter, Gauge, Histogram definitions
└── config/
    └── settings.py                    # (MODIFY) Add RedisConfig, JobQueueConfig

scripts/
├── extract_images.py                  # (MODIFY) Add --async, --job-id args
└── worker_image_extraction.py         # (NEW) Start worker process

tests/
├── unit/
│   └── test_jobs.py                   # (NEW) Job model tests
└── integration/
    └── test_extraction_job.py         # (NEW) E2E job tests

docker/
├── worker.Dockerfile                  # (NEW) Worker container
└── docker-compose.yml                 # (NEW) Dev stack

data/
└── jobs/                              # (NEW) Job persistence dir
    ├── {job_id}.json
    └── ...
```

### Files to Modify (Phase 1)

```
scripts/extract_images.py
├── ADD: --async flag (enqueue and return)
├── ADD: --job-id flag (check status)
├── ADD: --wait flag (backward compatible)
└── MODIFY: main() to handle both sync and async modes

src/phx_home_analysis/config/settings.py
├── ADD: RedisConfig dataclass
└── ADD: JobQueueConfig dataclass
```

### No Changes Needed

```
✓ scripts/extract_county_data.py       (County API extraction)
✓ src/phx_home_analysis/services/image_extraction/
  ├── orchestrator.py                   (Core logic stays same)
  ├── deduplicator.py                   (Excellent as-is)
  ├── naming.py                         (Excellent as-is)
  ├── extractors/                       (Stealth patterns solid)
  └── state_manager.py                  (Already atomic)
✓ data/property_images/                 (Storage format unchanged)
```

---

## Effort Estimate

### Phase 1 (Weeks 1-5)

| Week | Task | Effort | Owner | Status |
|------|------|--------|-------|--------|
| 1 | Job model + Redis setup | 2d | Backend | |
| 1-2 | Job function implementation | 2d | Backend | |
| 2 | Worker process + tests | 2d | Backend | |
| 3 | API endpoints | 2d | Backend | |
| 3-4 | CLI integration + backward compat | 2d | Backend | |
| 4 | Docker + docker-compose | 1d | DevOps | |
| 4-5 | Testing (unit + integration) | 2d | QA | |
| 5 | Documentation + training | 1d | Tech Writer | |
| **Total** | | **14 days** | | |

### Phase 2 (Weeks 1-3)

| Task | Effort |
|------|--------|
| Grafana dashboard setup | 2d |
| Prometheus alerting rules | 1d |
| Adaptive rate limiting | 2d |
| Job cancellation | 1d |
| Multi-worker tests | 1d |
| **Total** | **7 days** |

### Total Program

- **Phase 1**: 14 days (Q1 2025, must-have)
- **Phase 2**: 7 days (Q2 2025, should-have)
- **Phase 3**: 10 days (Q3 2025, nice-to-have)
- **Total**: ~31 days engineering effort

---

## Success Metrics

### Phase 1 Completion

- [ ] Job submission returns UUID in <100ms
- [ ] User can poll job status without blocking
- [ ] Worker processes 3+ concurrent jobs
- [ ] Failed jobs resumable (state preserved)
- [ ] Queue depth < 50 jobs (typical)
- [ ] Success rate > 95%
- [ ] Backward compatible CLI (existing scripts work)

### Phase 2 Completion

- [ ] Dashboard updated in real-time
- [ ] Alerts fire for stuck jobs
- [ ] Rate limiting prevents source blocks
- [ ] 2+ workers running independently
- [ ] Job cancellation works within 5 seconds

### Phase 3 Completion

- [ ] 3+ machines running workers
- [ ] Proxy rotation transparent
- [ ] Old images archived automatically
- [ ] Image metadata categorized separately
- [ ] Audit trail complete and queryable

---

## Risk Mitigation

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

## Rollback Plan

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

## Stakeholder Guide

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

## Conclusion

The PHX Houses project has **excellent foundations** for image extraction and stealth scraping. The critical missing piece is **background job infrastructure** to decouple extraction from user sessions.

**Phase 1 (Q1 2025)** implementation adds Redis + RQ + Worker pattern in **2-3 weeks of focused engineering**, enabling:
- Multi-user concurrent requests
- Real-time progress visibility
- Job cancellation & recovery
- Horizontal scaling
- Production-ready monitoring

**Phase 2-3** add observability, resilience, and enterprise features.

**No breaking changes** to existing code. Backward compatible. Low risk of data loss (atomic writes + state persistence).

**Next step**: Review recommendations, greenlight Phase 1, start implementation planning.

---

## Document References

1. **BACKEND_ARCHITECTURE_ANALYSIS_BUCKETS_5_6.md** (20+ pages)
   - Detailed architecture analysis
   - Gap analysis and recommendations
   - Implementation roadmap
   - Cost & resource implications

2. **BUCKET_5_6_IMPLEMENTATION_GUIDE.md** (15+ pages)
   - Step-by-step implementation
   - Complete code examples
   - Docker setup
   - Testing strategy

3. **ARCHITECTURE_SUMMARY.md** (this document)
   - Executive summary
   - Key design decisions
   - Effort estimate
   - Risk mitigation

---

**Generated**: 2025-12-03
**Analyst**: Backend Architect
**Distribution**: Architecture Review Board, Engineering Team, Product Management

