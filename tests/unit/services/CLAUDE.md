---
last_updated: 2025-12-05
updated_by: agent
staleness_hours: 24
flags: []
---
# tests/unit/services

## Purpose
Unit tests for service layer components covering job queue lifecycle, image extraction validation, and data integration. Tests focus on concurrent job processing, retry logic, priority ordering, and Zillow extractor robustness.

## Contents
| Path | Purpose |
|------|---------|
| `test_job_queue.py` | Job queue service: lifecycle, CRUD, concurrency, retry logic (5 test classes, 40+ tests) |
| `test_zillow_extractor_validation.py` | Zillow extractor syntax, imports, functional validation (6 test classes, 30+ tests) |

## Tasks
- [x] Assess service layer test coverage `P:H`
- [x] Document job queue patterns and execution models `P:H`
- [ ] Add integration tests for multi-extractor scenarios `P:M`
- [ ] Add performance benchmarks for job queue throughput `P:L`

## Learnings

### Job Queue Testing (test_job_queue.py)
- **TestJob class**: Job model lifecycle and state transitions
  - Creation with defaults (ID generation, status=PENDING, priority=0, retry_count=0)
  - Field validation (address, job_type, sources, max_retries)
  - State transitions (PENDING → RUNNING → COMPLETED/FAILED/RETRYING)
  - Serialization/deserialization to JSON

- **TestJobQueue class**: Queue persistence and CRUD operations
  - Load/save from JSON with atomic writes
  - Job insertion with priority ordering (higher priority = front of queue)
  - Deduplication (prevents duplicate addresses in queue)
  - Status tracking (pending count, completed count, failed count)

- **TestJobExecutor class**: Concurrent execution and retry
  - Async execution of job tasks
  - Retry logic with exponential backoff (max_retries=3)
  - Error handling and state propagation
  - Progress tracking (total, completed, errors)

### Zillow Extractor Testing (test_zillow_extractor_validation.py)
- **TestZillowExtractorSyntax**: Code quality validation
  - Module imports successfully (no SyntaxError, ImportError)
  - Type hints are valid (mypy compatible)
  - Method signatures match interface contract

- **TestZillowExtractorFunctional**: Behavior validation
  - _click_first_search_result() implementation (87 lines)
  - Enhanced autocomplete selectors (8 selectors for robust element matching)
  - _navigate_to_property_via_search() recovery logic
  - Error handling for missing elements

### Design Patterns
- **Job queue pattern**: Persistent task queue with priority ordering and retry logic
- **Async execution**: JobExecutor uses asyncio for concurrent job processing
- **Service validation**: Zillow tests validate both syntax (importability) and behavior (method functionality)

### Test Quality Observations
- **Lifecycle testing**: Job state transitions tested systematically (PENDING → RUNNING → COMPLETED)
- **Concurrency simulation**: Tests use asyncio and mocking for async behavior
- **Error scenarios**: Retry logic and failure handling validated
- **Selector robustness**: Multiple CSS selectors tested to ensure element matching under various DOM structures

## Refs
- Job queue model: `test_job_queue.py:35-70` (TestJob)
- Job queue CRUD: `test_job_queue.py:140-180` (TestJobQueue)
- Job executor: `test_job_queue.py:230-280` (TestJobExecutor)
- Zillow syntax validation: `test_zillow_extractor_validation.py:22-60`
- Zillow functional tests: `test_zillow_extractor_validation.py:100-150`
- Service integration: Job queue used by image extraction orchestrator

## Deps
← Imports from:
  - `phx_home_analysis.services.job_queue` (Job, JobQueue, JobExecutor, JobStatus, JobType)
  - `src.phx_home_analysis.services.image_extraction.extractors.zillow` (ZillowExtractor)
  - Standard library: asyncio, json, tempfile, datetime, pathlib

→ Imported by:
  - pytest (test framework)
  - CI/CD pipeline (must pass before merge)
  - Image extraction orchestrator (job queue service)
