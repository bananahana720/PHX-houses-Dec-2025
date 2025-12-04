# Quick Start: Job Queue Integration

### 1. Dependencies

```bash
# Add to requirements.txt
redis==5.0.0              # Redis client
rq==1.15.0                # Redis Queue
python-rq-dashboard==0.14.0  # Job monitoring UI
prometheus-client==0.19.0  # Metrics export
```

### 2. Redis Setup

**Development** (Docker):
```bash
# Start Redis container
docker run -d -p 6379:6379 --name redis-dev redis:7-alpine

# Test connection
redis-cli ping  # Should print PONG
```

**Production** (AWS ElastiCache):
```bash
# Create small cluster (cache.t3.micro)
# Configure security group to allow access from workers
# Set parameter group: maxmemory-policy=noevict
# Enable automatic backups (daily)
```

### 3. File Structure

```
phx-houses-dec-2025/
├── src/phx_home_analysis/
│   ├── jobs/                 # NEW: Job definitions
│   │   ├── __init__.py
│   │   ├── models.py         # Job dataclass
│   │   └── image_extraction.py  # extract_images_job function
│   ├── workers/              # NEW: Worker processes
│   │   ├── __init__.py
│   │   └── image_extraction.py  # ImageExtractionWorker class
│   ├── api/                  # NEW: REST endpoints (if using Flask/FastAPI)
│   │   ├── __init__.py
│   │   └── extraction_routes.py
│   └── config/
│       ├── settings.py       # MODIFY: Add Redis config
│       └── constants.py
├── scripts/
│   ├── extract_images.py    # MODIFY: Add --sync/--async flags
│   ├── worker_image_extraction.py  # NEW: Start worker process
│   └── api_server.py        # NEW: Start API server (optional)
├── tests/
│   ├── unit/
│   │   └── test_jobs.py    # NEW: Job tests
│   └── integration/
│       └── test_extraction_job.py  # NEW: E2E tests
├── docker/
│   ├── worker.Dockerfile   # NEW: Worker container
│   └── docker-compose.yml  # NEW: Local dev stack
└── docs/
    ├── BACKEND_ARCHITECTURE_ANALYSIS_BUCKETS_5_6.md  # Architecture doc
    └── BUCKET_5_6_IMPLEMENTATION_GUIDE.md  # THIS FILE
```

---
