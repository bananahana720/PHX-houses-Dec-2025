# Architecture Diagram

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
