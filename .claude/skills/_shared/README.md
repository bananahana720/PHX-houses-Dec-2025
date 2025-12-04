# Shared Skills Directory

This directory contains shared resources used across multiple skills, preventing duplication and maintaining consistency.

---

## Available Shared Resources

### scoring-tables.md
**Purpose:** Canonical source for all scoring system information

**Contains:**
- Complete 605-point scoring system (Sections A, B, C)
- Tier classification thresholds (UNICORN/CONTENDER/PASS/FAILED)
- All scoring rubrics with 1-10 scales
- Kill-switch criteria (7 hard filters)
- Default value rules and decision tree
- Python calculation examples
- Validation protocols
- File relationship matrix

**Used By:**
- `.claude/skills/scoring/SKILL.md` - Scoring calculations
- `.claude/skills/image-assessment/SKILL.md` - Section C rubrics
- `.claude/skills/kill-switch/SKILL.md` - Kill-switch criteria
- `.claude/AGENT_BRIEFING.md` - Quick references

**How to Reference:**
```markdown
See `.claude/skills/_shared/scoring-tables.md` for complete scoring reference.

Quick ref:
- Section A: 250 pts (Location)
- Section B: 160 pts (Lot/Systems)
- Section C: 190 pts (Interior)
```

---

## Directory Structure

```
_shared/
├── README.md              (this file)
└── scoring-tables.md      (canonical scoring reference)
```

---

## Adding New Shared Resources

When creating new shared resources:

1. Place file in `.claude/skills/_shared/`
2. Start with clear documentation at the top
3. Include "allowed-tools" frontmatter
4. Reference from other files instead of duplicating
5. Update this README with description

Example frontmatter:
```yaml
---
name: _shared/resource-name
description: Clear, concise description of what this resource provides
allowed-tools: Read, [other tools if needed]
---
```

---

## Benefits of Shared Resources

- **Single Source of Truth**: Updates made once, apply everywhere
- **Token Efficiency**: Reference once, use many times
- **Consistency**: No conflicting information
- **Maintainability**: Clear ownership and dependencies
- **Clarity**: Easy to find canonical definitions

---

## Cross-References

| Resource | Referenced By | Location |
|----------|---|---|
| scoring-tables.md | 4 skills + agents | All scoring-related files |
| | AGENT_BRIEFING.md | Line 219+ |
| | scoring/SKILL.md | Line 11+ |
| | image-assessment/SKILL.md | Section headers |
| | kill-switch/SKILL.md | Criteria section |

---

**Last Updated:** 2025-12-01
**Maintainer:** Claude Code (AI Engineer)
**Status:** Active
