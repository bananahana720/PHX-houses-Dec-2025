# Integration Pain Points (User Reported)

The user has mentioned "integration issues" - the system has several known integration challenges:

### 1. Data Structure Confusion
**Problem:** `enrichment_data.json` is a LIST, but developers often treat it as a dict keyed by address.
**Impact:** `TypeError` and `AttributeError` when trying dict operations.
**Solution:** Always iterate to find properties by address.

### 2. Phase Dependency Validation
**Problem:** Phase 2 (image-assessor) requires Phase 1 complete, but no automatic validation.
**Impact:** Spawning agents prematurely causes failures.
**Solution:** MANDATORY pre-spawn validation via `validate_phase_prerequisites.py`.

### 3. State File Staleness
**Problem:** Multiple agents writing to shared state files can cause race conditions.
**Impact:** Lost updates, stale in_progress status.
**Solution:** Read-modify-write with atomic operations, staleness checks.

### 4. Browser Detection
**Problem:** PerimeterX detects Playwright on Zillow/Redfin.
**Impact:** 403 Forbidden, CAPTCHA challenges.
**Solution:** Use stealth browsers (nodriver + curl_cffi) instead of Playwright.

### 5. Missing Prerequisites Errors
**Problem:** Phase 2 agents fail if images not downloaded.
**Impact:** Agent failures, wasted Claude API calls.
**Solution:** Check image manifest before spawning agents.
