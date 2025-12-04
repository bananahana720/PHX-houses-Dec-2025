# Known Issues & Limitations

### Data Structure Confusion
**Issue:** `enrichment_data.json` is a LIST, but commonly treated as dict.
**Impact:** `TypeError`, `AttributeError`.
**Solution:** Always iterate to find properties by address.

[See Troubleshooting in Development Guide →](./development-guide.md#troubleshooting)

### Browser Detection
**Issue:** PerimeterX detects Playwright on Zillow/Redfin.
**Impact:** 403 Forbidden, CAPTCHA challenges.
**Solution:** Use nodriver (stealth) instead of Playwright.

### Phase Dependency Validation
**Issue:** Phase 2 requires Phase 1 complete, but no automatic validation.
**Impact:** Agent failures, wasted API calls.
**Solution:** MANDATORY pre-spawn validation via `validate_phase_prerequisites.py`.

### Single-Threaded Scoring
**Issue:** Scoring is single-threaded.
**Impact:** Slow for large datasets (100+ properties).
**Solution:** Consider parallelizing scoring strategies.

### Arizona-Specific
**Issue:** System is tailored to Phoenix metro.
**Impact:** Not portable to other markets without recalibration.
**Solution:** Extract constants, create regional profiles.

---
