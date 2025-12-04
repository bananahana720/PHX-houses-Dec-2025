---
last_updated: 2025-12-04
updated_by: agent
staleness_hours: 72
flags: []
---

# .claude/CLAUDE.md

See `../CLAUDE.md` for full project documentation (stack, testing, CI/CD, project-specific instructions).

This directory contains Claude Code configuration: agents, skills, commands, and protocols.

## Directory Structure

```
.claude/
├── CLAUDE.md              # This file
├── AGENT_BRIEFING.md       # Shared agent context (required reading)
├── protocols.md           # Operational protocols (TIER 0-3)
├── mcp-reference.md       # MCP tool documentation
├── agents/                # Subagent definitions
│   ├── listing-browser.md # Zillow/Redfin extraction (Haiku)
│   ├── map-analyzer.md    # Geographic analysis (Haiku)
│   └── image-assessor.md  # Visual scoring (Sonnet)
├── commands/              # Custom slash commands
│   ├── analyze-property.md# Multi-agent orchestrator
│   └── commit.md          # Git commit helper
└── skills/                # Domain expertise modules
    ├── property-data/     # Data access patterns
    ├── state-management/  # Checkpoints & recovery
    ├── kill-switch/       # Buyer criteria validation
    ├── scoring/           # 605-point scoring system
    ├── county-assessor/   # Maricopa County API
    ├── arizona-context/   # AZ-specific factors
    ├── listing-extraction/# Browser automation
    ├── map-analysis/      # Schools, safety, distances
    ├── image-assessment/  # Visual scoring rubrics
    ├── deal-sheets/       # Report generation
    └── visualizations/    # Charts & plots
```

## Skills System

Skills provide domain expertise that agents can load via the `skills:` frontmatter field.

### Using Skills

**In agent files:**
```yaml
---
name: my-agent
skills: property-data, state-management, kill-switch
---
```

**In slash commands:**
```yaml
---
allowed-tools: Task, Skill
---
Load skills as needed: property-data, scoring, deal-sheets
```

### Available Skills

| Skill | Purpose | Use When |
|-------|---------|----------|
| property-data | Load/query/update property data | Any property data access |
| state-management | Checkpointing & crash recovery | Multi-phase workflows |
| kill-switch | Buyer criteria validation | Filtering properties |
| scoring | 605-point scoring system | Calculating scores/tiers |
| county-assessor | Maricopa County API | Phase 0 data extraction |
| arizona-context | AZ-specific: solar, pool, HVAC | AZ property evaluation |
| listing-extraction | Zillow/Redfin automation | Phase 1 listing data |
| map-analysis | Schools, safety, distances | Phase 1 geographic data |
| image-assessment | Visual scoring (Section C) | Phase 2 image analysis |
| deal-sheets | Report generation | Phase 4 outputs |
| visualizations | Charts & plots | Analysis visualization |

## Quick Links

| Resource | Description |
|----------|-------------|
| `AGENT_BRIEFING.md` | Shared agent context |
| `protocols.md` | Operational protocols (TIER 0-3) |
| `mcp-reference.md` | MCP tool documentation |
| `commands/analyze-property.md` | Multi-agent orchestrator |

## Essential Files (Do Not Condense)

- `protocols.md` - Operational protocols
- `AGENT_BRIEFING.md` - Agent shared context
- `skills/*/SKILL.md` - Skill definitions

## Key Commands

```bash
# Property analysis pipeline
/analyze-property --test          # First 5 properties
/analyze-property --all           # Full batch
/analyze-property "123 Main St"   # Single property

# Manual script execution
python scripts/analyze.py         # Run scoring
python scripts/extract_county_data.py --all  # County data
python scripts/extract_images.py --all       # Image extraction
python -m scripts.deal_sheets     # Generate reports
```
