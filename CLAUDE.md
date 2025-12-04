---
last_updated: 2025-12-04
updated_by: agent
staleness_hours: 72
flags: []
---

# PHX Houses Analysis Pipeline

## Critical Behavior (Project-Level)

- Inherits the organizational Critical Behavior rules from `~/.claude/CLAUDE.md`; project rules may add, but must not relax, those hard rules without an explicit, approved exception.
- Maintain context headroom of 10–20%; if the next step would drop below this headroom, pause and use the `/compact` template before proceeding.
- Stop-the-line triggers (project additions):
  - [x] Data integrity risks: `enrichment_data.json` or `work_items.json` corruption
  - [x] Kill-switch criteria changes without scoring recalculation
  - [x] Phase 2 spawn without Phase 1 completion validation
- Always ask before (project additions):
  - [x] Modifying kill-switch thresholds or severity weights
  - [x] Adding new scoring dimensions or changing max points
  - [x] Schema changes to `enrichment_data.json` structure
- Never do:
  - [x] Placeholders, stubs, or TODOs in place of working code
  - [x] Bypassing failing checks or disabling lint/tests without approved ticket + timebox
  - [x] Destructive operations on `data/*.json` without explicit approval and backups

## INSTRUCTION PRIORITY (Highest to Lowest)

1. **TIER 0 Protocols** (protocols.md) - NEVER violate
2. **Tool Usage Rules** (below) - ALWAYS apply, override agent examples
3. **Data Structure Rules** - Match actual file formats
4. **Agent Instructions** - Follow unless conflicts with above
5. **Skill Guidance** - Supplementary domain knowledge

**Override Rule:** If an agent file shows `cat FILE | python`, you MUST use `Read` tool instead. Agent code examples are illustrative, not prescriptive for tool choice.

## TOOL USAGE RULES (MANDATORY - NO EXCEPTIONS)

These rules override ALL other instructions, including agent-specific code examples.

### ABSOLUTE PROHIBITIONS
| NEVER Use | ALWAYS Use Instead | Why |
|-----------|-------------------|-----|
| `bash cat FILE` | `Read` tool | Proper permissions, truncation |
| `bash head/tail FILE` | `Read` tool with offset/limit | Consistent interface |
| `bash grep PATTERN` | `Grep` tool | Better output modes |
| `bash rg PATTERN` | `Grep` tool | Native tool preferred |
| `bash find DIR` | `Glob` tool | Pattern matching |
| `bash ls DIR` | `Glob` tool | Structured results |
| `cat FILE \| python -c` | `Read` tool, then parse | Reliability |
| Playwright for Zillow/Redfin | `scripts/extract_images.py` | Stealth required |
| WebSearch without sources | Include Sources: section | Attribution |

---

## Stack

### Languages/Runtimes
- **Primary language:** Python 3.10+ (target 3.12)
- **Runtime version:** CPython 3.12.x
- **Secondary languages:** Bash (scripts), YAML (config)

### Frameworks/Libraries
- **Data processing:** pandas 2.3, Pydantic 2.12
- **Visualization:** plotly 6.5, folium 0.20
- **Browser automation:** nodriver 0.48 (stealth), playwright 1.56 (fallback)
- **HTTP client:** httpx 0.28, curl-cffi 0.13
- **Image processing:** Pillow 12, imagehash 4.3

### Package Manager/Build Tools
- **Package manager:** uv (fast Python package installer)
- **Build tool:** hatchling
- **Task runner:** Custom scripts in `scripts/`

## Code Style

### Formatter + Linter
- **Tool:** ruff 0.14.7 (both formatter and linter)
- **Config:** `pyproject.toml` [tool.ruff]
- **Line length:** 100
- **Rules:** E, W, F, I (isort), B (bugbear), C4, UP

### Type Checking
- **Tool:** mypy 1.19
- **Config:** `pyproject.toml` [tool.mypy]
- **Strictness:** `disallow_untyped_defs = true`

### Naming Conventions
- **Files:** snake_case (e.g., `extract_images.py`)
- **Classes:** PascalCase (e.g., `PropertyScorer`)
- **Functions:** snake_case (e.g., `calculate_kill_switch`)
- **Constants:** UPPER_SNAKE_CASE (e.g., `MAX_SEVERITY_THRESHOLD`)

## Testing

### Frameworks
- **Unit test:** pytest 9.0.1
- **Coverage:** pytest-cov 7.0
- **Async:** pytest-asyncio 1.3
- **HTTP mocking:** respx 0.22

### Coverage Targets
- **Line coverage:** 80% minimum
- **Critical paths:** kill-switch, scoring algorithms
- **Excluded:** `scripts/` CLI wrappers, `__pycache__`

### Test Structure
```
tests/
├── unit/           # Fast, isolated tests
├── integration/    # Multi-component tests
├── fixtures/       # Shared test data
└── conftest.py     # Pytest configuration
```

## CI/CD

### Required PR Checks
- [x] Lint/format: `ruff check . && ruff format --check .`
- [x] Type check: `mypy src/`
- [x] Unit tests: `pytest tests/unit/`
- [x] Security scan: `pip-audit`
- [ ] Integration tests (manual)

### Pre-commit Hooks
- ruff format
- ruff check --fix
- mypy (optional)

## Security/Compliance

### Secrets Handling
- **Tool:** python-dotenv
- **Location:** `.env` (gitignored)
- **Required:** `MARICOPA_ASSESSOR_TOKEN`

### Dependencies
- **Vulnerability scan:** pip-audit 2.7.3
- **License:** MIT (permissive)

---

## Project-Specific Instructions

### What This Project Does

Evaluates Phoenix residential properties against strict buyer criteria:
- **Kill-switches**: 8 HARD criteria (instant fail): HOA=$0, beds≥4, baths≥2, sqft>1800, lot>8k, garage≥1, sewer=city, year≤2024
- **Scoring**: 605 pts max across Location (250), Systems (175), Interior (180)
- **Tiers**: Unicorn (>480), Contender (360-480), Pass (<360)

### Where Things Live

| Purpose | Location |
|---------|----------|
| Property data | `data/enrichment_data.json`, `data/phx_homes.csv` |
| Pipeline state | `data/work_items.json` |
| Scoring config | `src/phx_home_analysis/config/constants.py` |
| Analysis scripts | `scripts/phx_home_analyzer.py`, `scripts/extract_*.py` |
| Agent definitions | `.claude/agents/*.md` |
| Skills library | `.claude/skills/*/SKILL.md` |
| Knowledge graphs | `.claude/knowledge/*.json` |

### Quick Commands

```bash
# Multi-agent analysis
/analyze-property --all           # All properties
/analyze-property "123 Main St"   # Single property

# Manual execution
python scripts/phx_home_analyzer.py              # Scoring
python scripts/extract_county_data.py --all      # County API
python scripts/extract_images.py --all           # Images (stealth)
python -m scripts.deal_sheets                    # Reports
```

### Pre-Spawn Validation (REQUIRED for Phase 2)

```bash
# Validate prerequisites (returns JSON)
python scripts/validate_phase_prerequisites.py --address "ADDRESS" --phase phase2_images --json

# Exit code 0 = can_spawn=true, proceed
# Exit code 1 = can_spawn=false, BLOCKED - do NOT spawn agent
```

### Multi-Agent Pipeline

```
Phase 0: County API → lot_sqft, year_built, garage_spaces
Phase 1: listing-browser (Haiku) → images, hoa_fee, price
         map-analyzer (Haiku) → schools, safety, orientation
Phase 2: image-assessor (Sonnet) → interior + exterior scores
Phase 3: Synthesis → total score, tier, kill-switch verdict
Phase 4: Reports → deal sheets, visualizations
```

### Kill-Switch Criteria

| Type | Criterion | Requirement | Effect |
|------|-----------|-------------|--------|
| HARD | HOA | Must be $0 | instant fail |
| HARD | Beds | ≥4 | instant fail |
| HARD | Baths | ≥2 | instant fail |
| HARD | Sqft | >1800 | instant fail |
| HARD | Lot | >8000 sqft | instant fail |
| HARD | Garage | ≥1 space | instant fail |
| HARD | Sewer | City | instant fail |
| HARD | Year | ≤2024 (no new builds) | instant fail |

**Verdict**: FAIL if any HARD criterion is not met

### Arizona Specifics

- **Orientation**: North=30pts (best), West=0pts (worst for cooling)
- **HVAC lifespan**: 10-15 years (not 20+ like elsewhere)
- **Pool costs**: $250-400/month total ownership
- **Solar leases**: Liability, not asset ($100-200/mo + transfer issues)

### Agents & Skills

| Agent | Model | Skills |
|-------|-------|--------|
| listing-browser | Haiku | property-data, state-management, listing-extraction, kill-switch |
| map-analyzer | Haiku | property-data, state-management, map-analysis, arizona-context, scoring |
| image-assessor | Sonnet | property-data, state-management, image-assessment, arizona-context-lite, scoring |

### State Files

| File | Purpose | Check When |
|------|---------|------------|
| `work_items.json` | Pipeline progress | Session start, agent spawn |
| `enrichment_data.json` | Property data | Before property ops |
| `extraction_state.json` | Image pipeline | Before image ops |

### Context Management

1. **Session start**: Read `.claude/AGENT_BRIEFING.md` + check `work_items.json`
2. **Directory entry**: Check for CLAUDE.md, create placeholder if missing
3. **Work complete**: Update pending_tasks, add key_learnings
4. **On errors**: Document in key_learnings with workaround
5. **Before Phase 2 spawn**: MANDATORY - validate prerequisites

### File Organization

- Scripts → `scripts/` | Tests → `tests/` | Docs → `docs/` | Data → `data/`
- **Never create files in project root**

---

## References

| Resource | Location |
|----------|----------|
| Kill-switch config | `src/phx_home_analysis/config/constants.py:1-50` |
| Scoring weights | `src/phx_home_analysis/config/scoring_weights.py:1-100` |
| Schemas | `src/phx_home_analysis/validation/schemas.py:1-200` |
| Agent briefing | `.claude/AGENT_BRIEFING.md` |
| Protocols | `.claude/protocols.md` |
| Tool schemas | `.claude/knowledge/toolkit.json` |
| Context management | `.claude/knowledge/context-management.json` |

---
*Knowledge graphs provide HOW. This file provides WHAT, WHERE, WHY.*
