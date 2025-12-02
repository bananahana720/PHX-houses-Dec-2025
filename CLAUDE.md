# PHX Houses Analysis Pipeline

First-time home buyer analysis for Phoenix metro with kill-switch filtering and 600-point scoring.

## What This Project Does

Evaluates Phoenix residential properties against strict buyer criteria:
- **Kill-switches**: Hard fails (HOA, beds, baths) + soft severity threshold (≥3.0 = fail)
- **Scoring**: 600 pts max across Location (230), Systems (180), Interior (190)
- **Tiers**: Unicorn (>480), Contender (360-480), Pass (<360)

## Where Things Live

| Purpose | Location |
|---------|----------|
| Property data | `data/enrichment_data.json`, `data/phx_homes.csv` |
| Pipeline state | `data/work_items.json` |
| Scoring config | `src/phx_home_analysis/config/constants.py` |
| Analysis scripts | `scripts/phx_home_analyzer.py`, `scripts/extract_*.py` |
| Agent definitions | `.claude/agents/*.md` |
| Skills library | `.claude/skills/*/SKILL.md` |
| Knowledge graphs | `.claude/knowledge/*.json` |

## Quick Commands

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

## Key Principles

### Tool Usage (CRITICAL)
| ❌ Never | ✅ Always |
|----------|----------|
| `bash grep/rg` | `Grep` tool |
| `bash cat/head/tail` | `Read` tool |
| `bash find` | `Glob` tool |
| `bash sed` | `Edit` tool |
| Playwright for Zillow/Redfin | `scripts/extract_images.py` |
| WebSearch without sources | Include Sources: section |

### Context Management
1. **Session start**: Read `.claude/AGENT_BRIEFING.md` + check `work_items.json`
2. **Directory entry**: Check for CLAUDE.md, create placeholder if missing
3. **Work complete**: Update pending_tasks, add key_learnings
4. **On errors**: Document in key_learnings with workaround

### File Organization
- Scripts → `scripts/` | Tests → `tests/` | Docs → `docs/` | Data → `data/`
- **Never create files in project root**

## Multi-Agent Pipeline

```
Phase 0: County API → lot_sqft, year_built, garage_spaces
Phase 1: listing-browser (Haiku) → images, hoa_fee, price
         map-analyzer (Haiku) → schools, safety, orientation
Phase 2: image-assessor (Sonnet) → interior + exterior scores
Phase 3: Synthesis → total score, tier, kill-switch verdict
Phase 4: Reports → deal sheets, visualizations
```

## Kill-Switch Criteria

| Type | Criterion | Requirement | Severity |
|------|-----------|-------------|----------|
| HARD | HOA | Must be $0 | instant |
| HARD | Beds | ≥4 | instant |
| HARD | Baths | ≥2 | instant |
| SOFT | Sewer | City | 2.5 |
| SOFT | Year | <2024 | 2.0 |
| SOFT | Garage | ≥2 spaces | 1.5 |
| SOFT | Lot | 7k-15k sqft | 1.0 |

**Verdict**: FAIL if HARD fails OR severity ≥3.0 | WARNING if 1.5-3.0 | PASS if <1.5

## Arizona Specifics

- **Orientation**: North=30pts (best), West=0pts (worst for cooling)
- **HVAC lifespan**: 10-15 years (not 20+ like elsewhere)
- **Pool costs**: $250-400/month total ownership
- **Solar leases**: Liability, not asset ($100-200/mo + transfer issues)

## Agents & Skills

| Agent | Model | Skills |
|-------|-------|--------|
| listing-browser | Haiku | property-data, state-management, listing-extraction, kill-switch |
| map-analyzer | Haiku | property-data, state-management, map-analysis, arizona-context, scoring |
| image-assessor | Sonnet | property-data, state-management, image-assessment, exterior-assessment, inspection-standards |

## State Files

| File | Purpose | Check When |
|------|---------|------------|
| `work_items.json` | Pipeline progress | Session start, agent spawn |
| `enrichment_data.json` | Property data | Before property ops |
| `extraction_state.json` | Image pipeline | Before image ops |

## Knowledge Graphs

Detailed tool schemas, relationships, and protocols:
- @.claude/knowledge/toolkit.json - Tools, scripts, agents, skills
- @.claude/knowledge/context-management.json - State tracking, staleness, handoff

## References

- Kill-switch: `src/phx_home_analysis/config/constants.py:1-50`
- Scoring: `src/phx_home_analysis/config/scoring_weights.py:1-100`
- Schemas: `src/phx_home_analysis/validation/schemas.py:1-200`
- Agent briefing: `.claude/AGENT_BRIEFING.md`
- Protocols: `.claude/protocols.md`

## Environment Variables

- `MARICOPA_ASSESSOR_TOKEN` - County Assessor API

---
*Knowledge graphs provide HOW. This file provides WHAT, WHERE, WHY.*
*Lines: ~120 (target: <200)*
