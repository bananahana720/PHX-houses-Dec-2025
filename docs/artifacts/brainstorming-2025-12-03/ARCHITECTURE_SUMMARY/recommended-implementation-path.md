# Recommended Implementation Path

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
