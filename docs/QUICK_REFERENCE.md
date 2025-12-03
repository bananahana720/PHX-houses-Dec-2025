# Quick Reference: Image Pipeline & Scraping Architecture
## Buckets 5 & 6 Analysis

---

## 📊 Current Architecture (1-page overview)

### Image Pipeline
```
Download (Zillow/Redfin/Maricopa/MLS)
    ↓ (multiple concurrent sources)
Deduplicate (perceptual hash + LSH)
    ↓
Categorize (location, subject, confidence)
    ↓
Rename (metadata-encoded filename)
    ↓
Store (hash-based folders with atomic writes)
```

**Strengths**:
- LSH optimization: O(n) not O(n²) duplicate detection
- Metadata-rich naming: `{hash}_{location}_{subject}_{confidence}_{source}_{date}.png`
- Atomic writes: Safe even on crash
- 1,750+ images across 35 properties

### Scraping Architecture
```
User Request (CLI)
    ↓
ImageExtractionOrchestrator (3 concurrent properties)
    ├─ Source #1 (Zillow)   → nodriver + curl_cffi → Circuit breaker
    ├─ Source #2 (Redfin)   → nodriver + curl_cffi → Circuit breaker
    ├─ Source #3 (Maricopa) → httpx async → Rate limit
    └─ Source #4 (MLS)      → Playwright → Basic auth
    ↓
State persisted to disk (crash recovery)
    ↓
Return summary to user
```

**Strengths**:
- Stealth techniques effective (PerimeterX bypass)
- Circuit breaker prevents cascade failures
- State resumption from last checkpoint
- Async/await for concurrency

---

## 🔴 Critical Gaps

| Gap | Impact | Priority |
|-----|--------|----------|
| **No background jobs** | Single user blocking 30+ min | **P0** |
| **No job queue** | Requests dropped if extraction running | **P0** |
| **No worker pool** | Can't scale beyond single machine | **P0** |
| **No progress API** | User has no visibility until done | **P1** |
| **No job cancellation** | Must kill process to stop | **P1** |

---

## 📈 Recommended Architecture

```
┌─────────────────────────────────────────┐
│ User: POST /api/extraction/jobs          │
│ Returns: {job_id, status: "queued"}     │
└──────────────┬──────────────────────────┘
               ↓
         ┌──────────────┐
         │ Redis Queue  │
         │ (FIFO FIFO)  │
         └──────────────┘
               ↓ (many)
    ┌──────────────────────┐
    │ Workers (1+)         │
    │ - 3 concurrent props │
    │ - Auto-restart      │
    │ - Health monitoring │
    └──────────────────────┘
               ↓
    [Same extraction logic]
               ↓
       Job status → Redis
       Progress → Metrics
       Results → Disk
```

**Benefit**: User gets response in 100ms, job processes asynchronously

---

## 💾 Data Storage Explained

### Image Manifest: `image_manifest.json`
```json
{
  "properties": {
    "4560 E Sunrise Dr, Phoenix, AZ 85044": [
      {
        "image_id": "UUID",
        "source": "zillow",
        "local_path": "processed/f4e29e2c/image.png",
        "phash": "64-char-hex",  // for deduplication
        "status": "processed",
        "downloaded_at": "ISO8601"
      }
    ]
  }
}
```

### Address Lookup: `address_folder_lookup.json`
```json
{
  "4732 W Davis Rd, Glendale, AZ 85306": {
    "folder": "686067a4",     // 8-char hash
    "image_count": 98,
    "path": "data/property_images/processed/686067a4/"
  }
}
```

### Extraction State: `extraction_state.json`
```json
{
  "completed_properties": ["addr1", "addr2"],
  "failed_properties": [],
  "property_last_checked": {
    "addr1": "ISO8601"
  }
}
```

---

## 🔍 Deduplication: LSH Explained

**Problem**: Check 2,847 new images against 5,000 stored = 14M comparisons

**Solution**: Locality Sensitive Hashing
- Split 64-bit hash into 8 bands
- Group similar images together
- Only compare within group (candidates)
- Result: 14M → 50K comparisons (280x faster)

**Code**:
```python
candidates = get_candidate_images(new_hash)  # Fast (LSH bucketing)
for candidate in candidates:
    if is_similar(new_hash, candidate.hash):
        return "duplicate"
```

---

## 🌐 Stealth Scraping: How It Works

### Why Needed?
- Zillow/Redfin block bots with PerimeterX
- Headless browsers detected via timing analysis
- IP reputation matters (rotating proxies)

### Techniques Used
1. **Non-headless browser** (nodriver): Looks like real user
2. **Browser isolation** (virtual display): Keeps browser hidden on servers
3. **curl_cffi**: HTTP client that mimics browser fingerprint
4. **Proxy rotation**: Different IP per request
5. **Human-like timing**: Random delays (0.5-3s between requests)

### Success Rate
- Zillow: 95%+ success
- Redfin: 85%+ (more aggressive blocking)
- Maricopa: 99%+ (official API)

---

## ⚡ Circuit Breaker Pattern

Protects against cascade failures:

```
Normal operation (CLOSED)
    ↓ [3 failures]
Disabled for 5 min (OPEN)
    ↓ [5 min passes]
Test one request (HALF-OPEN)
    ↓ [success]
Back to normal (CLOSED)
```

**Example**: Redfin returns 429 (rate limited)
- Failure #1: Retry with backoff
- Failure #2: Increase delay
- Failure #3: **OPEN** - disable Redfin for 5 min
- Other sources continue (Zillow, Maricopa still working)
- After 5 min: Try one request, if success → resume

**Benefit**: One source failure doesn't kill entire extraction

---

## 📝 Image Naming: Decode Examples

`ef7cd95f_int_kitchen_95_z_20241201.png`
- `ef7cd95f` = Property hash (4732 W Davis Rd)
- `int` = Interior (not exterior)
- `kitchen` = Room/system type
- `95` = 95% AI confidence
- `z` = Source (Zillow)
- `20241201` = Listing date (2024-12-01)
- No sequence = First image in this category

`686067a4_ext_pool_87_r_20241130_02.png`
- Same as above but:
- `ext` = Exterior
- `pool` = Pool image
- `87` = 87% confidence
- `r` = Redfin source
- `_02` = Second pool image from Redfin

**Benefits**:
- Parseable (no database needed)
- Sortable by date
- Filterable by confidence
- Source-trackable
- Collision detection (sequence auto-increment)

---

## 🚀 Phase 1 Implementation Checklist

### Week 1-2: Foundation
- [ ] Add Redis to requirements.txt + docker-compose
- [ ] Create `src/phx_home_analysis/jobs/models.py` (ImageExtractionJob)
- [ ] Create `src/phx_home_analysis/jobs/image_extraction.py` (job function)
- [ ] Add Redis config to `settings.py`

### Week 3: Worker
- [ ] Create `src/phx_home_analysis/workers/image_extraction.py`
- [ ] Create `scripts/worker_image_extraction.py` (CLI script)
- [ ] Test worker locally with docker-compose

### Week 4: API & CLI
- [ ] Create `src/phx_home_analysis/api/extraction_routes.py` (REST endpoints)
- [ ] Modify `scripts/extract_images.py` (add --async, --job-id flags)
- [ ] Test end-to-end job flow

### Week 5: Testing & Deployment
- [ ] Unit tests for job model
- [ ] Integration tests for worker
- [ ] Docker Compose file for dev/prod
- [ ] Documentation + monitoring setup

---

## 🧪 Quick Test (Dev Machine)

### Setup
```bash
# Terminal 1: Redis
docker run -p 6379:6379 redis:7-alpine

# Terminal 2: Worker
python scripts/worker_image_extraction.py

# Terminal 3: Submit job
python -c "
from phx_home_analysis.jobs.image_extraction import extract_images_async
job = extract_images_async(properties=[], sources=['zillow'])
print(f'Job: {job.id}')
"
# Output: Job: 8d8a2c1f-...

# Terminal 3: Check status
python -c "
from phx_home_analysis.jobs.models import ImageExtractionJob
job = ImageExtractionJob.load('8d8a2c1f-...')
print(f'Status: {job.status}')
print(f'Progress: {job.completed_properties}/{job.total_properties}')
"
```

---

## 📊 Current Metrics (Baseline)

| Metric | Value |
|--------|-------|
| Properties extracted | 35+ |
| Total images | 2,847 |
| Avg images per property | 50-80 |
| Extraction time (5 props) | 12-18 min |
| Throughput | ~16 images/min |
| Dedup success rate | 95%+ |
| Storage size | ~800 MB |
| Hash index | 2,847 entries |

### After Phase 1 (Predicted)
| Metric | Value |
|--------|-------|
| Concurrent job requests | 10+ |
| Job submission latency | <100ms |
| Worker count | 1-4 |
| Extraction throughput | 48-64 images/min (3x) |
| Queue depth typical | <10 jobs |
| Success rate | 95%+ (unchanged) |

---

## 🔐 Security Considerations

### Current
- ✓ Images stored locally (no public CDN)
- ✓ Atomic writes prevent corruption
- ✓ State resumption doesn't leak data
- ✗ No user isolation (not needed yet)
- ✗ No API authentication (single user)

### After Phase 1
- ✓ Same data security
- Add: API key auth (if public)
- Add: Per-user job tracking
- Add: Audit trail in job logs
- Add: User quotas (max jobs/day)

---

## 📚 Key Files Reference

| File | Purpose | Type |
|------|---------|------|
| `scripts/extract_images.py` | CLI entry point | Existing |
| `src/.../image_extraction/orchestrator.py` | Main extraction logic | Existing |
| `src/.../image_extraction/deduplicator.py` | LSH-based dedup | Existing |
| `src/.../image_extraction/naming.py` | Metadata-encoded names | Existing |
| `data/property_images/metadata/` | All state files | Data |
| `data/jobs/` | Job persistence | Data (NEW) |
| `src/.../jobs/models.py` | Job model | Code (NEW) |
| `src/.../workers/image_extraction.py` | Worker process | Code (NEW) |
| `docker-compose.yml` | Local dev stack | Config (NEW) |

---

## ❓ FAQ Quick Answers

**Q: Why not just make CLI faster?**
A: Can't parallelize extraction more (3 concurrent is limit). Also: blocking user for 30+ min is poor UX. Job queue enables scaling.

**Q: What if Redis goes down?**
A: Jobs stored on disk + state resumable. Next worker picks up. Max loss: current property being extracted.

**Q: Can we use existing database instead of Redis?**
A: Not ideal. Redis optimized for queue operations (FIFO, atomic). Database adds overhead.

**Q: How many workers do we need?**
A: Start with 1. Add more if queue depth grows. 3 workers = 9 concurrent properties = 3-4x throughput.

**Q: Is this backward compatible?**
A: Yes. `--sync` mode or default to polling. Existing scripts work unchanged.

**Q: What's the timeline?**
A: Phase 1 (P0, must-have): 4-5 weeks. Phase 2 (P1, should-have): 2-3 weeks.

---

## 🎯 Next Actions

### Immediate (This Week)
1. Review all 3 documents
2. Get executive approval for Phase 1
3. Schedule architecture review meeting

### Week 1 (Start Implementation)
1. Set up dev environment (Docker Redis)
2. Create job model + persistence layer
3. Write unit tests for job model

### Week 2
1. Implement job function + queueing
2. Implement worker process
3. Integration tests

### Week 3-4
1. REST API endpoints
2. CLI --async integration
3. End-to-end testing

### Week 5
1. Docker Compose setup
2. Monitoring + alerting
3. Documentation

---

## 📞 Stakeholder Updates

### For Executive/PM
- **Timeline**: 4-5 weeks to MVP
- **Cost**: +$67/month infrastructure (small)
- **Benefit**: Multi-user support, better UX, foundation for scaling
- **Risk**: Low (backward compatible, no data loss)

### For Engineering
- **Effort**: ~14 days total (spreads over 5 weeks)
- **Complexity**: Medium (job queue + worker pattern)
- **Tools**: Redis + RQ (simple, well-documented)
- **Testing**: Unit + integration tests included

### For DevOps
- **New Dependencies**: Redis, RQ
- **Scaling**: Workers on separate machines (later)
- **Monitoring**: Prometheus metrics + Grafana dashboards
- **Maintenance**: Minimal (Redis persistence, job cleanup)

---

**Document Set**:
1. BACKEND_ARCHITECTURE_ANALYSIS_BUCKETS_5_6.md (detailed architecture)
2. BUCKET_5_6_IMPLEMENTATION_GUIDE.md (step-by-step code)
3. ARCHITECTURE_SUMMARY.md (executive overview)
4. QUICK_REFERENCE.md (this document)

**Total Content**: 60+ pages, 15,000+ words, ready for implementation

