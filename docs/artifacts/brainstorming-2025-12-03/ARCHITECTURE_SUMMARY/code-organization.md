# Code Organization

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
