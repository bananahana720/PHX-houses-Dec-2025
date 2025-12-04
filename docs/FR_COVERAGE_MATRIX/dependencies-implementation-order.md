# Dependencies & Implementation Order

### Phase 1: Foundation (E1)
**Estimated Duration:** 5-7 days
**Critical Path:** E1 enables all other epics

1. **E1.S1** - Configuration System (1 day)
   - YAML scoring weights config
   - CSV kill-switch criteria config
   - Pydantic validation

2. **E1.S2** - Property Data Storage (1 day)
   - JSON repository with atomic writes
   - Address normalization
   - Backup-before-modify pattern

3. **E1.S3** - Data Provenance (1 day)
   - ProvenanceMetadata dataclass
   - Confidence calibration
   - Lineage tracking

4. **E1.S4** - Pipeline Checkpointing (1 day)
   - work_items.json state management
   - Per-property phase tracking
   - Summary calculation

5. **E1.S5** - Resume Capability (1 day)
   - Stuck item detection
   - State validation
   - Merge without duplicates

6. **E1.S6** - Error Recovery (1 day)
   - Retry decorator with exponential backoff
   - Error categorization
   - Per-item failure tracking

### Phase 2: Data Acquisition (E2)
**Estimated Duration:** 7-10 days
**Dependencies:** E1

1. **E2.S1** - CLI Entry Point (1 day)
   - argparse CLI with flags
   - CSV validation
   - Progress display

2. **E2.S7** - API Infrastructure (1 day)
   - APIClient base class
   - Authentication handling
   - Rate limiting, caching

3. **E2.S2** - County Assessor (1 day)
   - API client implementation
   - Field mapping
   - Provenance attachment

4. **E2.S3** - Listing Extraction (2 days)
   - nodriver stealth browser
   - curl-cffi fallback
   - Playwright MCP fallback
   - Proxy/User-Agent rotation

5. **E2.S4** - Image Download (1 day)
   - Manifest tracking
   - Cache hit detection
   - Parallel downloads

6. **E2.S5** - Google Maps (1 day)
   - Geocoding, distances
   - Orientation determination
   - Response caching

7. **E2.S6** - GreatSchools (1 day)
   - School ratings retrieval
   - Assigned school determination
   - Fallback to Google Places

### Phase 3: Kill-Switch System (E3)
**Estimated Duration:** 3-4 days
**Dependencies:** E1, E2

1. **E3.S1** - HARD Criteria (1 day)
   - 7 HARD criteria implementation
   - Short-circuit evaluation

2. **E3.S2** - SOFT Severity (1 day)
   - Severity accumulation logic
   - Threshold-based verdicts

3. **E3.S3** - Verdict Evaluation (0.5 days)
   - KillSwitchResult dataclass
   - Multi-failure tracking

4. **E3.S4** - Failure Explanations (0.5 days)
   - Human-readable messages
   - Consequence mapping

5. **E3.S5** - Configuration (1 day)
   - CSV parsing
   - Hot-reload capability

### Phase 4: Scoring Engine (E4)
**Estimated Duration:** 5-7 days
**Dependencies:** E1, E2, E3

1. **E4.S1** - Three-Dimension Scoring (1 day)
   - Section calculation logic
   - Partial data handling

2. **E4.S2** - 22 Strategies (3 days)
   - Individual strategy classes
   - AZ context integration
   - Weights from config

3. **E4.S3** - Tier Classification (1 day)
   - Threshold logic
   - Badge formatting

4. **E4.S4** - Score Breakdown (1 day)
   - Impact-ordered display
   - Source data linkage

5. **E4.S5** - Re-Scoring (1 day)
   - Weight validation
   - Cached data usage

6. **E4.S6** - Delta Tracking (1 day)
   - Previous score preservation
   - Multi-level deltas

### Phase 5: Pipeline Orchestration (E5)
**Estimated Duration:** 4-5 days
**Dependencies:** E1, E2, E3, E4

1. **E5.S1** - Orchestrator CLI (1 day)
   - Main entry point
   - Phase management
   - Progress display

2. **E5.S2** - Phase Coordination (1 day)
   - Sequential execution
   - Failure handling

3. **E5.S3** - Agent Spawning (1 day)
   - Model selection (Haiku vs Sonnet)
   - Skill loading

4. **E5.S4** - Prerequisite Validation (1 day)
   - Validation script
   - JSON output
   - Blocking behavior

5. **E5.S5** - Parallel Execution (1 day)
   - Async spawning
   - Completion synchronization

6. **E5.S6** - Output Aggregation (1 day)
   - Data merging
   - Conflict resolution

### Phase 6: Risk Intelligence (E6)
**Estimated Duration:** 5-7 days
**Dependencies:** E2, E4, E5

1. **E6.S1** - Image Assessment (1 day)
   - Visual scoring prompts
   - 7-category assessment

2. **E6.S2** - Warning Generation (1 day)
   - 6 risk category detectors
   - Severity classification

3. **E6.S3** - Consequence Mapping (1 day)
   - Cost estimation
   - QoL/resale impacts

4. **E6.S4** - Confidence Levels (1 day)
   - Calibration logic
   - Age-based degradation

5. **E6.S5** - Foundation Analysis (1 day)
   - Crack detection
   - Pattern classification

6. **E6.S6** - HVAC Timeline (1 day)
   - Age-based categorization
   - AZ lifespan adjustment

### Phase 7: Reporting (E7)
**Estimated Duration:** 4-6 days
**Dependencies:** E1, E3, E4, E5, E6

1. **E7.S1** - HTML Generation (2 days)
   - Jinja2 templates
   - Mobile responsiveness
   - Offline capability

2. **E7.S2** - Content Structure (1 day)
   - Summary, scores, tier
   - Kill-switch verdict

3. **E7.S3** - Score Narratives (1 day)
   - Natural language explanations
   - Comparative analysis

4. **E7.S4** - Visual Comparisons (1 day)
   - Radar charts
   - Scatter plots

5. **E7.S5** - Tour Checklists (0.5 days)
   - Printable checklists

6. **E7.S6** - Regeneration (0.5 days)
   - Re-scoring pipeline

---
