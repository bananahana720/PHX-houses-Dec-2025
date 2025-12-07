# Architecture Plan: Pipeline Alignment (2025-12-06)

## Overview
This document outlines the architecture improvements and agent orchestration strategy for aligning the PHX Houses image extraction pipeline with data pipeline best practices.

---

## Data Pipeline Alignment

### Current State
```
Property List → [Orchestrator (1672 lines god object)] → Images + State
                     ↓
         ┌──────────┼──────────┐
         ↓          ↓          ↓
      Zillow    Redfin    PhoenixMLS
         ↓          ↓          ↓
         └──────────┴──────────┘
                     ↓
            [Scattered Logic]
            - Dedup in orchestrator
            - Transform in standardizer
            - Validate in validators
            - Store in orchestrator
```

### Target State (ETL Pattern)
```
Property List
     ↓
[INGESTION LAYER] ─────────────────────────────────┐
     ↓                                              │
┌─────────────────────────────────────────────────┐ │
│ ConcurrencyManager                              │ │
│  - Semaphore(max=15)                           │ │
│  - CircuitBreaker per source                   │ │
│  - ErrorAggregator                             │ │
└─────────────────────────────────────────────────┘ │
     ↓                                              │
┌─────────────────────────────────────────────────┐ │
│ Source Extractors (parallel)                    │ │
│  - ZillowExtractor                             │ │
│  - RedfinExtractor                             │ │
│  - PhoenixMLSSearchExtractor                   │ │
│  - MaricopaAssessorExtractor                   │ │
└─────────────────────────────────────────────────┘ │
     ↓                                              │
     │ Raw URLs + Metadata                         │
     ↓                                              │
[TRANSFORM LAYER] ─────────────────────────────────┤
     ↓                                              │
┌─────────────────────────────────────────────────┐ │
│ ImageProcessor (CONSOLIDATED)                   │ │
│  1. Download with retry                        │ │
│  2. Validate quality (min size, dimensions)    │ │
│  3. Compute perceptual hash (pHash + dHash)    │ │
│  4. Check deduplication (LSH index)            │ │
│  5. Standardize format (PNG, max 1024px)       │ │
│  6. Compute content hash (MD5)                 │ │
│  7. Return ProcessedImage or error             │ │
└─────────────────────────────────────────────────┘ │
     ↓                                              │
     │ ProcessedImage objects                      │
     ↓                                              │
[LOAD LAYER] ──────────────────────────────────────┤
     ↓                                              │
┌─────────────────────────────────────────────────┐ │
│ StateTracker (UNIFIED)                          │ │
│  - Atomic file writes                          │ │
│  - Checkpoint every 5 operations               │ │
│  - Schema versioned state files                │ │
│                                                 │ │
│  Outputs:                                       │ │
│  - extraction_state.json (v2.0.0)             │ │
│  - image_manifest.json (v2.0.0)               │ │
│  - url_tracker.json (v1.0.0)                  │ │
│  - hash_index.json (v1.0.0)                   │ │
│  - run_history/{run_id}.json                  │ │
└─────────────────────────────────────────────────┘ │
     ↓                                              │
[QUALITY LAYER] ───────────────────────────────────┘
     ↓
┌─────────────────────────────────────────────────┐
│ DataReconciler                                  │
│  - Orphan file detection                       │
│  - Ghost entry detection                       │
│  - Hash mismatch detection                     │
│  - Quality scores (accuracy, completeness)     │
└─────────────────────────────────────────────────┘
```

---

## Implementation Tasks

### Wave 1: Error Handling & Schema (AP-2, AP-3, AP-6)

**Task 1.1: Add retry decorator to extractors**
```python
# stealth_base.py - Add retry wrapper
from phx_home_analysis.errors import retry_with_backoff

@retry_with_backoff(max_retries=3, backoff_factor=2.0)
async def extract_image_urls(self, property: Property) -> list[str]:
    ...
```

**Task 1.2: Schema versioning for state files**
```python
# state_manager.py - Add version field
@dataclass
class ExtractionState:
    version: str = "2.0.0"  # NEW
    completed_properties: set[str] = field(default_factory=set)
    failed_properties: set[str] = field(default_factory=set)
    # Migration on load
    @classmethod
    def from_dict(cls, data: dict) -> "ExtractionState":
        version = data.get("version", "1.0.0")
        # Handle migration if needed
        ...
```

**Task 1.3: Error classification in orchestrator**
```python
# orchestrator.py - Classify errors
from phx_home_analysis.errors import is_transient_error

except Exception as e:
    if is_transient_error(e):
        # Retry later
        state.mark_retry(property_address)
    else:
        # Permanent failure
        state.mark_failed(property_address)
```

### Wave 2: ImageProcessor Integration (AP-1)

**Task 2.1: Wire ImageProcessor into orchestrator**
- Replace inline transformation logic with ImageProcessor calls
- Consolidate dedup + standardize + store into single service

**Task 2.2: Update orchestrator to use new services**
```python
# orchestrator.py - Use decomposed services
async def _process_image(self, image_data: bytes, url: str, property: Property):
    result, error = await self.image_processor.process_image(
        image_data=image_data,
        source_url=url,
        property_hash=compute_property_hash(property.full_address),
        run_id=self.run_id,
    )
    if error:
        raise ImageProcessingError(error)
    return result
```

### Wave 3: PhoenixMLS Navigation Fix

**Task 3.1: Debug navigation blocker**
- Capture HTML after autocomplete click
- Determine if page is search results or detail page
- Identify correct navigation path

**Task 3.2: Implement fix based on findings**
- Option A: Click "View Details" button after autocomplete
- Option B: Construct direct URL from autocomplete text
- Option C: Use MLS# to build direct listing URL

---

## Agent Orchestration Strategy

### Recommended Approach: Parallel Swarm

```
┌──────────────────────────────────────────────────────────────┐
│                     MAIN AGENT (Orchestrator)                 │
│  - Owns the plan and todo list                               │
│  - Coordinates subagent work                                 │
│  - Validates deliverables                                    │
│  - Commits to git                                            │
└──────────────────────────────────────────────────────────────┘
                              │
           ┌──────────────────┼──────────────────┐
           ▼                  ▼                  ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  WAVE 1 AGENT   │  │  LIVE TEST     │  │  CODE REVIEW   │
│  Error Handling │  │  PhoenixMLS    │  │  Validation    │
│                 │  │                 │  │                 │
│  - Add retry    │  │  - Debug nav   │  │  - Check tests │
│  - Schema ver   │  │  - Capture HTML │  │  - Lint/mypy  │
│  - Error class  │  │  - Diagnose    │  │  - Coverage    │
└─────────────────┘  └─────────────────┘  └─────────────────┘
           │                  │                  │
           └──────────────────┼──────────────────┘
                              ▼
                    ┌─────────────────┐
                    │  INTEGRATION    │
                    │  - Merge changes│
                    │  - Run tests    │
                    │  - Commit       │
                    └─────────────────┘
```

### Agent Responsibilities

| Agent | Type | Purpose | Tools |
|-------|------|---------|-------|
| Main Agent | Coordinator | Plan, delegate, validate, commit | All |
| Wave 1 Agent | general-purpose | Error handling + schema | Read, Edit, Write, Bash |
| Live Test Agent | general-purpose | Debug PhoenixMLS (LAUNCHED) | Bash, Read |
| Code Review Agent | code-reviewer | Validate changes | Read, Grep, Glob |

### Current Status
- **Live Test Agent**: LAUNCHED (agentId: 17b11af7)
- **Wave 1 Agent**: PENDING (awaiting live test results)
- **Code Review Agent**: PENDING (after implementation)

---

## Success Criteria

### Functional
- [ ] PhoenixMLS Search extracts >0 images (navigation fixed)
- [ ] Error handling uses retry decorator for transient errors
- [ ] State files have version field for schema migration

### Technical
- [ ] All 119 existing tests pass
- [ ] No new linter violations (ruff check)
- [ ] Type checking passes (mypy src/)
- [ ] Schema migration is backward compatible

### Data Pipeline Alignment
- [ ] Transformation logic consolidated in ImageProcessor
- [ ] Error classification distinguishes transient vs permanent
- [ ] State persistence uses atomic writes with versioning
- [ ] Quality validation occurs at all 3 stages (pre/during/post)

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| PhoenixMLS site structure changed | Fallback to Zillow+Redfin (100% coverage) |
| Breaking changes to state files | Soft migration (add fields, ignore missing) |
| Test failures from refactoring | Run tests after each wave |
| Browser crashes during testing | Circuit breaker + retry logic |

---

## Timeline (Estimated)

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| Live Testing | 10-15 min | Debug report, navigation fix hypothesis |
| Wave 1: Error Handling | 30-45 min | Retry decorator, schema versioning |
| Wave 2: ImageProcessor | 45-60 min | Consolidated transformation |
| Wave 3: PhoenixMLS Fix | 30-45 min | Working navigation |
| Integration & Testing | 20-30 min | All tests pass, commit |

**Total**: 2-3 hours
