# 5. ARCHITECTURAL RISKS AND TECHNICAL DEBT

### Critical Risks (High Impact, High Probability)

#### Risk 1: Data Integrity on Concurrent Writes
**Status**: HIGH RISK
**Current**: `enrichment_data.json` is a LIST. Concurrent writes without atomic patterns will corrupt file.
**Likelihood**: MEDIUM (will happen if phases run in parallel)
**Impact**: Complete data loss for entire batch

**Mitigation**:
- Always use atomic writes (temp file + os.replace())
- Add file-level locking (fcntl on Unix, msvcrt on Windows)
- Validate JSON integrity before/after writes

#### Risk 2: Lost Images During Extraction
**Status**: HIGH RISK
**Current**: Image URLs tracked in URL tracking, but if extraction crashes mid-property, deduplication logic breaks
**Likelihood**: MEDIUM (network timeouts are common)
**Impact**: Duplicate image downloads, storage bloat

**Mitigation**:
- Checkpoint image extraction per image (not per property)
- Hash images before accepting (prevent duplicates upstream)
- Implement image cleanup/consolidation script

#### Risk 3: Stale Enrichment Data
**Status**: MEDIUM RISK
**Current**: `_last_updated` exists, but no staleness threshold enforcement
**Likelihood**: MEDIUM (humans forget to check)
**Impact**: Scoring based on stale data (old school ratings, moved utilities, etc.)

**Mitigation**:
- Add automatic staleness check at pipeline start
- Block scoring if data older than 30 days
- Implement refresh strategy

### Technical Debt (Medium Impact)

| Debt Item | Location | Effort to Fix | Impact |
|-----------|----------|---------------|--------|
| **Hard-coded phase names** | work_items, agents, orchestrator | 3 days | Blocks adding phases |
| **No scoring lineage** | PropertyScorer | 2 days | Can't explain scores |
| **No kill-switch audit** | KillSwitchFilter | 1 day | Opaque verdicts |
| **No field provenance** | enrichment_data.json schema | 3 days | Can't trace data source |
| **No confidence scoring** | Validation | 2 days | All data equally weighted |
| **Raw data not preserved** | Image assessment | 2 days | Can't re-score images |
| **No cost tracking** | Image extraction | 1 day | Budget overruns possible |
| **Serial property processing** | Orchestrator | 3 days | Slow execution |
| **No inter-phase communication** | work_items schema | 1 day | Blocks can't be signaled |
| **No automatic retry** | Phase execution | 1 day | Manual intervention needed |

### Architectural Smells

1. **Configuration in Code** (constants.py)
   - Kill-switch weights, tier thresholds, cost rates all hard-coded
   - Should be in JSON config files
   - Blocks evolution and A/B testing

2. **God Object** (Property entity)
   - 156 fields across all phases
   - No clear separation of concerns
   - Should split into phase-specific DTOs

3. **Magic Strings** (phase names)
   - "phase0_county", "phase1_listing", etc. in multiple places
   - String-based dependencies are fragile
   - Should use enums or config

4. **Implicit Ordering** (phase dependencies)
   - Phase sequence embedded in orchestrator logic
   - DAG should be explicit (declarative)
   - Would allow easier phase insertion/removal

5. **Lost Context** (scoring)
   - Strategies run independently
   - No shared context or communication
   - Difficult to implement inter-strategy rules

---
