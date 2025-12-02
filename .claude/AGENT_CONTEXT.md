# Agent Operational Context - PHX Houses Dec 2025

**REQUIRED READING**: All agents MUST read this file before executing their primary task.

## STEP 0: GET YOUR BEARINGS (MANDATORY)

**ALL agents MUST run these orientation steps before starting work.**

```bash
# 1. Confirm working directory
pwd

# 2. Understand project structure
ls -la
ls -la data/
ls -la data/property_images/metadata/

# 3. Load pipeline state
cat data/property_images/metadata/extraction_state.json | python -c "
import json,sys
state = json.load(sys.stdin)
print('=== PIPELINE STATE ===')
print(f'Completed: {len(state.get(\"completed_properties\", []))}')
print(f'In Progress: {len(state.get(\"in_progress_properties\", []))}')
print(f'Failed: {len(state.get(\"failed_properties\", []))}')
"

# 4. Count total properties
echo "=== PROPERTY COUNTS ==="
wc -l < data/phx_homes.csv
cat data/enrichment_data.json | python -c "import json,sys; print(f'Enriched: {len(json.load(sys.stdin))}')"

# 5. Check recent activity
git log --oneline -5 2>/dev/null || echo "Not a git repo"

# 6. Check for pending tasks
cat data/research_tasks.json 2>/dev/null | python -c "
import json,sys
try:
    tasks = json.load(sys.stdin)
    print(f'Pending research tasks: {len(tasks)}')
except: print('No pending research tasks')
"
```

**Understanding before action:**
- Know how many properties are done vs remaining
- Know current pipeline state
- Know if previous session had failures
- Know if there are pending research tasks

---

## Quick Reference

| Resource | Location | Purpose |
|----------|----------|---------|
| **Skills** | `.claude/skills/` | Domain expertise (load via `skills:` frontmatter) |
| **State Files** | `data/property_images/metadata/` | Pipeline state & checkpoints |
| **Property Data** | `data/enrichment_data.json` | Property enrichment data |
| **Scripts** | `scripts/` | CLI tools for data processing |

## Available Skills

Load skills in agent frontmatter for domain-specific knowledge:

| Skill | Purpose |
|-------|---------|
| **property-data** | Load/query/update property data (CSV, JSON) |
| **state-management** | Checkpointing, triage, crash recovery |
| **kill-switch** | Buyer criteria validation (7 kill switches) |
| **scoring** | 600-point scoring system & tier assignment |
| **county-assessor** | Maricopa County API data extraction |
| **arizona-context** | AZ-specific: solar, pool, orientation, HVAC |
| **listing-extraction** | Zillow/Redfin browser automation |
| **map-analysis** | Schools, safety, distances, orientation |
| **image-assessment** | Visual scoring rubrics (Section C) |
| **deal-sheets** | Report generation |
| **visualizations** | Charts and plots |

## State Files

| File | Purpose |
|------|---------|
| `extraction_state.json` | Pipeline state, completed/failed/in_progress arrays |
| `image_manifest.json` | Image registry with perceptual hashes |
| `address_folder_lookup.json` | **Address→folder mapping (USE THIS!)** |
| `pipeline_runs.json` | Run history |
| `research_tasks.json` | Pending research task queue |

## Standard Return Format

All agents MUST return:

```json
{
  "address": "full property address",
  "status": "success|partial|failed|skipped",
  "skip_reason": "already_completed|max_retries|null",
  "data": {},
  "errors": [{"source": "...", "error": "..."}],
  "files_updated": ["path1", "path2"],
  "next_steps": ["..."]
}
```

## Critical Rules

1. **Use address_folder_lookup.json** - Do NOT calculate hash manually
2. **Triage first** - Skip completed or max-retry properties
3. **Update state atomically** - Write to .tmp then rename
4. **Return partial data** - Partial > nothing
5. **Use existing scripts** - Don't reimplement (Axiom 10)
6. **Check skills for details** - This file is overview only

## Phase Status Values

| Status | Meaning |
|--------|---------|
| `pending` | Not started |
| `in_progress` | Currently executing |
| `complete` | Successfully finished |
| `failed` | Error occurred |
| `skipped` | Precondition not met |

## Error Handling

| Error | Action |
|-------|--------|
| CAPTCHA | Skip source, try next |
| 404 | Log, continue |
| Rate limit | Backoff, retry |
| Timeout | Retry once |
| Schema invalid | Refuse write, log |

## Confidence Scoring Standard

All agent outputs MUST include an overall confidence assessment.

### Confidence Levels

| Level | Criteria | Action |
|-------|----------|--------|
| **HIGH** | All required data present, verified from authoritative sources, consistent across sources | Proceed with scoring/tier assignment |
| **MEDIUM** | Most data present, some derived/estimated values, minor gaps | Flag uncertain fields, proceed with caveats |
| **LOW** | Significant data missing, heavy reliance on defaults, conflicting sources | Flag property for manual review, use default scores |

### When to Assign Each Level

**HIGH Confidence:**
- All kill-switch criteria have authoritative data (County API, listing)
- Location data from verified sources (GreatSchools, Google Maps)
- Photos available for 6+ of 7 interior categories
- No conflicting data between sources
- Year built known (enables era calibration)

**MEDIUM Confidence:**
- Kill-switch criteria present but some from secondary sources
- 1-2 location fields estimated or missing
- Photos available for 4-5 categories
- Minor data conflicts resolved with reasonable assumptions
- Some scores use derived values (e.g., roof_age from year_built)

**LOW Confidence:**
- Kill-switch criteria have gaps requiring assumptions
- 3+ location fields missing or estimated
- Photos available for <4 categories
- Major data conflicts unresolved
- Critical fields defaulted to 5.0

### Confidence Impact on Processing

| Confidence | Tier Assignment | Deal Sheet | Action Required |
|------------|-----------------|------------|-----------------|
| HIGH | Final | Publish | None |
| MEDIUM | Provisional | Publish with caveats | Flag for review |
| LOW | Held | Draft only | Manual research required |

### Confidence in Return Format

Add to ALL agent returns:

```json
{
  "address": "123 Main St, Phoenix, AZ 85001",
  "status": "success|partial|failed",
  "confidence": {
    "level": "high|medium|low",
    "reasoning": "Clear explanation of confidence basis",
    "uncertain_fields": ["field1", "field2"],
    "data_quality": 0.85
  },
  "data": {}
}
```

### Data Quality Score

Calculate as: (authoritative_fields / total_fields)

```python
def calculate_data_quality(data: dict, authoritative_sources: list[str]) -> float:
    """Calculate data quality score (0.0 - 1.0)."""
    total_fields = len(REQUIRED_FIELDS)
    authoritative_count = sum(
        1 for field in REQUIRED_FIELDS
        if data.get(f"{field}_source") in authoritative_sources
    )
    return authoritative_count / total_fields
```

## Output Length Constraints

To prevent context overflow and ensure consistent outputs, all agents MUST respect these limits:

### Field-Level Limits

| Field | Max Length | Purpose |
|-------|------------|---------|
| `overall_assessment` | 500 chars | Property summary |
| `condition_notes` | 300 chars | Per-category notes |
| `reasoning` | 200 chars | Confidence/scoring reasoning |
| `error_message` | 150 chars | Error descriptions |
| `next_steps` (each) | 100 chars | Individual action items |

### Section-Level Limits

| Section | Max Items | Max Total |
|---------|-----------|-----------|
| `errors` array | 10 items | - |
| `warnings` array | 10 items | - |
| `strengths` array | 5 items | 500 chars total |
| `concerns` array | 5 items | 500 chars total |
| `condition_issues` array | 10 items | - |
| `positive_features` array | 10 items | - |

### Truncation Rules

When content exceeds limits:
1. Prioritize most important/severe items
2. Truncate with ellipsis: "Text exceeds limit..."
3. Log truncation in warnings array
4. Never truncate: address, status, scores, tier

### Example Compliant Output

```json
{
  "address": "123 Main St, Phoenix, AZ 85001",
  "status": "success",
  "confidence": {
    "level": "high",
    "reasoning": "All Section C categories visible in photos",
    "data_quality": 0.92
  },
  "scores": {"kitchen_layout": 7, "master_suite": 8},
  "overall_assessment": "Well-maintained 1995 ranch with updated kitchen featuring granite counters and stainless appliances. Master suite adequate with en-suite bath. Some dated elements but move-in ready.",
  "condition_issues": [
    {"severity": "medium", "issue": "Carpet shows wear in traffic areas"}
  ]
}
```

Note: `overall_assessment` above is 220 chars (within 500 limit).

## Scoring Reference

See `.claude/skills/_shared/scoring-tables.md` for the canonical scoring reference including:
- Complete Section A, B, C tables
- Tier classification thresholds
- All rubrics and scoring formulas
- Kill-switch criteria
- Default value rules

**Quick Reference:**

| Section | Max Pts | Categories |
|---------|---------|------------|
| A: Location | 230 | School(50), Quietness(40), Safety(50), Grocery(30), Parks(30), Sun(30) |
| B: Lot/Systems | 180 | Roof(50), Backyard(40), Plumbing(40), Pool(20), CostEfficiency(30) |
| C: Interior | 190 | Kitchen(40), Master(40), Light(30), Ceilings(30), Fireplace(20), Laundry(20), Aesthetics(10) |
| **Total** | **600** | |

| Tier | Score | Percentage |
|------|-------|------------|
| UNICORN | >480 | >80% |
| CONTENDER | 360-480 | 60-80% |
| PASS | <360 | <60% |
| FAILED | - | Kill-switch fail |

## Kill-Switch Quick Reference

See `.claude/skills/_shared/scoring-tables.md` for complete kill-switch table and evaluation logic.

**HARD (Instant Fail):** HOA > $0, Beds < 4, Baths < 2

**SOFT (Severity Weights):**
- Septic: 2.5 pts
- New Build (>=2024): 2.0 pts
- Garage < 2: 1.5 pts
- Lot outside 7k-15k: 1.0 pts

**Thresholds:** FAIL >= 3.0 | WARNING >= 1.5 | PASS < 1.5

---

**For detailed instructions, load the appropriate skill.**
