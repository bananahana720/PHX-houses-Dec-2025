# 4. AUTONOMY ANALYSIS

### Current State: Phase Orchestration Is Solid

#### 4.1 What Works?

**Good (8/10):**
- ✅ Phase validation gates (`validate_phase_prerequisites.py`) prevent bad spawns
- ✅ Phase dependencies tracked in `work_items.json` (phase0 → phase1 → phase2 → etc.)
- ✅ State recovery: If agent crashes, pipeline resumes from last checkpoint
- ✅ Retry logic exists for failed phases
- ✅ Phase-level timeouts and concurrency limits defined in config

**Weaknesses (3/10):**
- ❌ No cross-property orchestration (must process properties sequentially)
- ❌ No inter-phase communication (phase1 can't signal "skip phase2 for this property")
- ❌ Manual monitoring required (no automatic backoff/escalation)
- ❌ No cost awareness (processes can run forever without budget checks)
- ❌ No self-healing (if 10% of properties fail, entire batch doesn't auto-retry with backoff)

#### 4.2 Current Orchestration Architecture

```python
# /analyze-property command spawns agents sequentially:

def analyze_property(address: str):
    # Load work_items.json
    work_items = load_work_items()

    for work_item in work_items:
        # Phase 0: County data
        if work_item.phases.phase0_county.status == "pending":
            # Run python scripts/extract_county_data.py
            # Update work_items.json

        # Phase 1a: Listing images
        if work_item.phases.phase1_listing.status == "pending":
            # Spawn listing-browser agent
            # Check validate_phase_prerequisites
            # Update work_items.json

        # Phase 1b: Map analysis (parallel)
        if work_item.phases.phase1_map.status == "pending":
            # Spawn map-analyzer agent
            # Update work_items.json

        # Phase 2: Image assessment (blocked if phase1_listing incomplete)
        if (work_item.phases.phase1_listing.status == "completed" and
            work_item.phases.phase2_images.status == "pending"):
            # Validate prerequisites
            if validate_phase_prerequisites(...):
                # Spawn image-assessor agent
                # Update work_items.json
            else:
                # BLOCKED - log reason, continue to next property

        # Phase 3: Synthesis (run all properties at once after phases complete)
        if all_phases_ready():
            # python scripts/phx_home_analyzer.py

        # Phase 4: Reporting
        # python scripts/generate_all_reports.py

# Problem: Serial processing blocks progress
# If property A is blocked on phase 2, property B can't advance
# Better: Process in parallel with dependency awareness
```

#### 4.3 Autonomy Gaps

**Gap 1: No Parallel Property Processing**

```python
# Current: Sequential
for property in properties:
    phase0(property)  # Wait
    phase1(property)  # Wait
    phase2(property)  # Wait

# Takes: 3 hours for 8 properties

# Desired: Parallel with dependency awareness
ExecutionGraph(
    [
        phase0(prop_A), phase0(prop_B), phase0(prop_C),  # Parallel
    ],
    then=[
        phase1_listing(prop_A), phase1_listing(prop_B),  # Parallel
        phase1_map(prop_A), phase1_map(prop_B),          # Parallel
    ],
    then=[
        phase2_images(prop_A), phase2_images(prop_B),    # Parallel (if prerequisites met)
    ],
    then=[
        phase3_synthesis_all(),  # Wait for all
    ]
)

# Takes: 45 minutes (mostly network I/O)
```

**Gap 2: No Inter-Phase Communication**

```python
# Example: Phase 1 listing agent can't tell phase 2 to skip
# Scenario: Zillow/Redfin has no interior photos (rare)
# Current: Phase 2 image assessor tries to assess, fails silently

# Desired: Phase 1 signals to orchestrator
if no_interior_photos:
    work_item.phases.phase2_images.status = "skipped"
    work_item.phases.phase2_images.skip_reason = "No interior photos available"
    # Phase 3 synthesis handles skipped phases gracefully
```

**Gap 3: No Automatic Backoff/Escalation**

```python
# Example: County API times out for 20% of properties
# Current: Entire batch fails, requires manual retry

# Desired: Automatic exponential backoff
retry_count = 0
while retry_count < 3:
    try:
        phase0_county(property)
        break
    except TimeoutError:
        retry_count += 1
        wait_time = 2 ** retry_count  # 2s, 4s, 8s
        sleep(wait_time)

# If all retries fail:
work_item.status = "failed"
work_item.failure_reason = "County API timeout after 3 retries"
send_alert("County API degraded - manual intervention needed")
```

**Gap 4: No Cost Awareness**

```python
# Image extraction can cost $$$:
# - 500 properties × 20 images × Imgur upload = network costs
# - Claude Vision: $0.003 per image × 8000 images = $24

# Current: No budget tracking
# Desired: Cost awareness
cost_budget = {
    "image_extraction": 100.0,  # $100 for Imgur
    "vision_assessment": 50.0,  # $50 for Claude Vision
}

# During execution:
vision_cost = 0.003 * image_count
if vision_cost > cost_budget["vision_assessment"]:
    logger.warning(f"Vision cost would exceed budget: ${vision_cost:.2f} > ${cost_budget['vision_assessment']}")
    # Option 1: Skip remaining properties
    # Option 2: Use cheaper model (Haiku instead of Sonnet)
    # Option 3: Batch images (assess 3 per call instead of 1)
```

**Gap 5: No Degradation Handling**

```python
# Current: All-or-nothing scoring
# If interior assessment fails, entire property skipped

# Desired: Graceful degradation
property.score_breakdown = ScoreBreakdown(
    location=180,  # Successful
    systems=95,    # Successful
    interior=None  # Failed - skip this section
)

property.total_score = 275  # Location + Systems only
property.scoring_notes = "Interior assessment skipped (no photos available)"
property.tier = "PASS_INCOMPLETE"  # Flag as incomplete scoring

# Still provide value: Can rank by available data
```

#### 4.4 Current Strengths

**Phase State Management (8/10):**
```python
# work_items.json tracks progress per property
# Each phase has status: pending → in_progress → completed|failed|blocked
# Prevents double-processing (idempotency key = address + phase)

# Validation gates work well
validate_phase_prerequisites("123 Main St", "phase2_images")
# Returns: can_spawn=True/False, reason="...", context={...}
```

**Crash Recovery (7/10):**
```python
# If orchestrator crashes mid-batch:
# - work_items.json is saved state
# - Agents append to enrichment_data.json atomically
# - Re-running same command resumes from last checkpoint
# - No duplicate processing (phase status prevents re-runs)
```

**Timeout Handling (6/10):**
```python
# config/constants.py defines phase timeouts:
IMAGE_BROWSER_TIMEOUT = 30  # seconds
IMAGE_DOWNLOAD_TIMEOUT = 30

# But: Timeouts are applied, not enforced
# Agents must respect timeout, not automatic
```

### Recommendations

#### Short-term (1-2 weeks)
1. **Implement parallel property processing**:
   ```python
   # Use ThreadPoolExecutor for CPU-bound phases, AsyncIO for I/O
   with ThreadPoolExecutor(max_workers=3) as executor:
       futures = [
           executor.submit(phase0_county, prop)
           for prop in properties
       ]
       for future in as_completed(futures):
           result = future.result()
   ```

2. **Add inter-phase communication** to work_items:
   ```json
   {
     "phases": {
       "phase1_listing": {
         "status": "completed",
         "signals_to_downstream": {
           "no_interior_photos": true,
           "image_count": 12
         }
       }
     }
   }
   ```

3. **Implement automatic retry** logic:
   ```python
   @retry(max_attempts=3, backoff_factor=2)
   def extract_county_data(property):
       # Automatically retries on failure
       pass
   ```

#### Medium-term (3-4 weeks)
1. **Create execution DAG** orchestrator:
   ```python
   dag = ExecutionDAG()
   dag.add_task("phase0", properties, timeout=60)
   dag.add_dependency("phase1_listing", depends_on="phase0")
   dag.add_dependency("phase1_map", depends_on="phase0")
   dag.add_dependency("phase2_images", depends_on="phase1_listing")
   dag.run()  # Handles parallelization automatically
   ```

2. **Implement cost tracking**:
   ```python
   cost_tracker = CostTracker(budget={"vision": 50.0})
   for image in images:
       cost = estimate_vision_cost(image)
       if cost_tracker.remaining < cost:
           logger.warning("Cost budget exceeded")
           break
       result = assess_image_with_vision(image)
       cost_tracker.record(cost)
   ```

3. **Add graceful degradation**:
   ```python
   def score_property_with_fallback(property):
       try:
           interior_score = assess_interior(property)
       except Exception as e:
           logger.warning(f"Interior assessment failed: {e}")
           interior_score = None  # Skip this section

       return calculate_score(property, interior_score=interior_score)
   ```

#### Long-term (ongoing)
1. **Distributed orchestration**:
   - Use Temporal or Airflow for workflow management
   - Cross-agent communication
   - Automatic scaling

2. **Observability and alerting**:
   - Prometheus metrics for phase duration, success rate
   - Alerts for bottlenecks (e.g., "Phase 2 taking 10x longer than expected")
   - Cost monitoring dashboard

3. **Self-healing recovery**:
   - Automatic detection of stalled phases
   - Rollback to last good state
   - Notification to human operators

---
