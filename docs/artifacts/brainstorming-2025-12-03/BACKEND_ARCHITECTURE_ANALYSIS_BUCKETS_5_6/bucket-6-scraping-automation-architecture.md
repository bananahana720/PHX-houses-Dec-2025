# BUCKET 6: Scraping & Automation Architecture

### Current Implementation

#### 6.1 Stealth Extraction Pattern

**Multi-Source Approach**:

| Source | Technology | Auth | Anti-Bot | Status |
|--------|-----------|------|----------|--------|
| **Zillow** | nodriver + curl_cffi | None | PerimeterX bypass | Working |
| **Redfin** | nodriver + curl_cffi | None | CF Challenge bypass | Implemented |
| **Phoenix MLS** | Playwright MCP | API Key | Basic | Implemented |
| **Maricopa Assessor** | httpx async | API Token | Rate limiting | Working |

#### 6.2 Browser Automation: Non-Headless Stealth

**Architecture**: `src/phx_home_analysis/services/infrastructure/browser_pool.py`

**Stealth Techniques**:

1. **Non-Headless Operation**:
   - Headless browsers detectable via timing analysis and DOM differences
   - Running visible improves detection evasion significantly
   - Problem: UI overhead on CI/CD servers

2. **Isolation Modes** (to keep browser hidden):
   ```python
   # From extract_images.py --isolation option
   "virtual"     # Virtual Display Driver (xvfb on Linux, custom on Windows)
   "secondary"   # Secondary monitor (if available)
   "off_screen"  # Position window off visible screen bounds
   "minimize"    # Start minimized (fallback)
   "none"        # No isolation (for dev/testing)
   ```

   **Implementation Strategy**:
   - Virtual display preferred (totally hidden, realistic rendering)
   - Secondary monitor fallback (if multi-display available)
   - Off-screen positioning (window at negative coordinates)
   - Minimize as last resort (user may see minimize/restore)

3. **Browser Profile Rotation**:
   - User-Agent rotation via curl_cffi
   - JavaScript fingerprint spoofing
   - Cookie/session management per property
   - Proxy rotation (webshare integration)

4. **Timing Human-Like**:
   - Random delays between requests (0.5-3s)
   - Request queuing: max 3 concurrent properties
   - Rate limiting: 0.2-0.5s between API calls
   - Exponential backoff on 429/503 responses

#### 6.3 Circuit Breaker Pattern

**Implementation**: `src/phx_home_analysis/services/image_extraction/orchestrator.py` - `SourceCircuitBreaker`

**States**:
```
CLOSED (normal) --[3 failures]--> OPEN (disabled)
                                     |
                            [300s timeout]
                                     v
                              HALF-OPEN (testing)
                                     |
                        [2 successes or 1 failure]
                                     v
                              CLOSED or OPEN
```

**Configuration**:
- Failure threshold: 3 consecutive failures
- Reset timeout: 300s (5 minutes)
- Half-open success count: 2 (confirms recovery)
- Per-source tracking (Zillow, Redfin, etc. independently)

**Benefits**:
- Prevents cascade failures (e.g., rate-limit one source, kill all extraction)
- Graceful degradation (other sources continue)
- Automatic recovery testing (circuit self-heals)
- Detailed status logging for ops visibility

**Example Output**:
```
Circuit OPEN for redfin - disabled for 300s after 3 failures
Circuit HALF-OPEN for redfin - testing recovery
Circuit CLOSED for redfin - source recovered
```

#### 6.4 Async Concurrency Model

**Architecture**: `src/phx_home_analysis/services/image_extraction/orchestrator.py`

**Concurrency Levels**:

1. **Property Level** (outer loop):
   - Max 3 concurrent properties (default)
   - asyncio.Semaphore(3) to limit resource usage
   - Per property: sequentially extract all sources then process

2. **Source Level** (inner loop):
   - Per property, sources run sequentially (to avoid IP conflicts)
   - e.g., finish Zillow for prop A before starting Redfin for prop A

3. **Download Level**:
   - Image downloads within a source: parallel via asyncio.gather
   - 10-20 concurrent downloads per source
   - HTTP/2 connection pooling (curl_cffi enables multiplexing)

**Flow**:
```python
async def extract_all(properties):
    semaphore = asyncio.Semaphore(max_concurrent=3)

    async def extract_property(prop):
        async with semaphore:
            for source in enabled_sources:
                images = await source_extractor.extract(prop)  # sequential
                await download_and_process(images)              # parallel

    await asyncio.gather(*[extract_property(p) for p in properties])
```

**Rationale**:
- Property-level semaphore: resource constraint (CPU, disk I/O, bandwidth)
- Sequential sources per property: avoids rate-limit triggering from same IP
- Parallel downloads: maximizes throughput within one source

#### 6.5 State Persistence & Resumability

**State File**: `data/property_images/metadata/extraction_state.json`

```json
{
  "completed_properties": ["4732 W Davis Rd, Glendale, AZ 85306"],
  "failed_properties": [],
  "property_last_checked": {
    "4560 E Sunrise Dr, Phoenix, AZ 85044": "2025-12-03T09:59:32.294059-05:00"
  },
  "last_updated": "2025-12-03T09:59:32.298061-05:00"
}
```

**Run History**: `data/property_images/metadata/pipeline_runs.json`

```json
{
  "runs": [
    {
      "run_id": "test_2025-12-01T00:15",
      "mode": "--test",
      "started_at": "ISO8601",
      "completed_at": "ISO8601",
      "properties_requested": 5,
      "properties_completed": 5,
      "properties_failed": 0,
      "images_extracted": 89,
      "sources_used": ["zillow"],
      "sources_blocked": ["redfin"],
      "phase_results": {...},
      "properties": [
        {
          "address": "...",
          "hash": "...",
          "score": 375,
          "tier": "contender"
        }
      ],
      "notes": "..."
    }
  ]
}
```

**Crash Recovery**:
- State persisted after each property completes (not after each image)
- On resume: skips completed_properties, retries failed_properties
- URL tracker prevents re-downloading same URL
- Hash index ensures no duplicate processing

**Usage**:
```bash
# Interrupted run - resume from where stopped
python scripts/extract_images.py --all --resume

# Start fresh, ignore previous state
python scripts/extract_images.py --all --fresh

# Dry run - discover URLs without downloading
python scripts/extract_images.py --all --dry-run
```

#### 6.6 User Isolation & Session Management

**Current Model**: Synchronous CLI-driven

**Isolation Level**: **File-based** (not user-based)

**Issues**:
- Single user at a time (blocking others via file locks)
- No per-user job tracking
- No request isolation (one CLI run affects all users)
- No queuing mechanism for concurrent requests

**Example Problem**:
```
User A: python scripts/extract_images.py --all  # Takes 2 hours
User B: python scripts/extract_images.py --address "123 Main St"  # Blocks or corrupts state
```

---
