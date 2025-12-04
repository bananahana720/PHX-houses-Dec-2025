# 4. NFR Testing Approach

### 4.1 Security Testing

| Requirement | Test Method | Tools | Priority |
|-------------|-------------|-------|----------|
| NFR25: Secrets in .env only | Git hook scanning | pre-commit + detect-secrets | P0 |
| NFR26: No PII in logs | Log audit tests | pytest + log capture | P0 |
| NFR27: No high/critical vulnerabilities | Dependency scanning | pip-audit | P0 (CI gate) |
| API token not exposed in errors | Error message audit | Unit tests | P1 |

**Test Cases:**
- `test_secrets_not_in_codebase`: grep for API key patterns in tracked files
- `test_logs_no_pii`: capture log output, assert no addresses/names
- `test_error_messages_sanitized`: verify 401 errors don't expose tokens

### 4.2 Performance Testing

| Requirement | Test Method | Tools | Priority |
|-------------|-------------|-------|----------|
| NFR1: 20 properties in <=30 min | Timing benchmark | pytest-benchmark | P1 |
| NFR2: Re-score 100 in <=5 min | Timing benchmark | pytest-benchmark | P1 |
| NFR4: Prerequisite validation <=5s | Unit test with timing | pytest | P2 |
| Memory usage reasonable | Profiling | memory_profiler (optional) | P3 |

**Test Cases:**
- `test_scoring_performance`: score 100 cached properties, assert <300s
- `test_kill_switch_performance`: evaluate 1000 properties, assert <10s
- `test_prerequisite_validation_speed`: run validation, assert <5s

### 4.3 Reliability Testing

| Requirement | Test Method | Tools | Priority |
|-------------|-------------|-------|----------|
| NFR5: 100% kill-switch accuracy | Exhaustive boundary tests | pytest | P0 |
| NFR6: Scoring consistency +/-5 pts | Deterministic re-run tests | pytest | P0 |
| NFR7: 95%+ resume success | Interrupt simulation | pytest + signal handling | P1 |
| NFR8: 100% schema validation | Pydantic enforcement | pytest | P0 |
| NFR9: Atomic checkpoint writes | Concurrent write tests | pytest | P1 |

**Test Cases:**
- `test_kill_switch_boundary_conditions`: HOA=0 vs HOA=1, beds=3 vs beds=4
- `test_scoring_deterministic`: same input produces identical output
- `test_resume_after_interrupt`: simulate SIGTERM, verify state integrity
- `test_schema_validation_rejects_invalid`: malformed JSON raises ValidationError

### 4.4 Maintainability Testing

| Requirement | Test Method | Tools | Priority |
|-------------|-------------|-------|----------|
| NFR10: Config externalized | Code audit | grep + pytest | P1 |
| NFR11: 80%+ docstring coverage | Documentation check | interrogate | P2 |
| NFR12: Actionable error messages | Error message audit | pytest | P1 |
| NFR13: Config schema validation | Unit tests | pytest | P1 |

**Test Cases:**
- `test_no_hardcoded_thresholds`: grep for magic numbers in scoring/kill-switch
- `test_config_validation_error_messages`: invalid config produces clear errors
- `test_docstring_coverage`: interrogate reports >=80%

---
