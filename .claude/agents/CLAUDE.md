---
last_updated: 2025-12-06T12:00:00Z
updated_by: agent
staleness_hours: 24
flags: []
---
# agents

## Purpose
Subagent definitions for multi-agent PHX pipeline. Each agent has model, skills, and phase assignment.

## Contents
| Agent | Model | Phase | Purpose |
|-------|-------|-------|---------|
| `listing-browser.md` | Haiku 4.5 | 1 | Zillow/Redfin extraction (stealth browser) |
| `map-analyzer.md` | Haiku 4.5 | 1 | Geographic analysis (schools, safety, orientation) |
| `image-assessor.md` | Opus 4.5 | 2 | Visual scoring (interior/exterior, 190 pts) |

## Agent Frontmatter
```yaml
---
name: agent-name
description: Brief purpose
model: haiku|opus          # haiku=4.5, opus=4.5
skills: skill1, skill2     # Comma-separated skill list
---
```

## Key Rules
- Agents inherit rules from parent CLAUDE.md
- Use `Read`/`Glob`/`Grep` tools, NOT bash equivalents
- Return data to orchestrator; do NOT modify state files directly

## Learnings
- Phase 1 agents run in parallel (listing-browser + map-analyzer)
- Phase 2 requires Phase 1 complete + images downloaded

## Refs
- Listing browser: `listing-browser.md`
- Map analyzer: `map-analyzer.md`
- Image assessor: `image-assessor.md`

## Deps
<- imports: skills (via frontmatter)
-> used by: /analyze-property command, orchestrator
