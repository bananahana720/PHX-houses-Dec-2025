# TRASH-FILES.md

This document tracks files and directories that have been moved to the `/TRASH` directory as part of consolidation, refactoring, or deprecation efforts.

## Consolidated/Deprecated Items

| Item | Location | Reason | Date |
|------|----------|--------|------|
| `arizona-context-lite/` | `TRASH/skills/arizona-context-lite/` | Consolidated into arizona-context skill - arizona-context/SKILL.md now contains both Quick Ref (lite content) and Full Context sections. image-assessor.md agent updated to use arizona-context instead. | 2025-12-04 |

## Recovery Instructions

To recover any item:

```bash
# Move back from TRASH
mv TRASH/skills/arizona-context-lite/ .claude/skills/

# Then verify references in agent files are updated
grep -r "arizona-context-lite" .claude/agents/
```

## Notes

- The arizona-context skill consolidation eliminates the need for a separate lite version
- All agents have been updated to reference the consolidated skill
- The Quick Ref section in arizona-context/SKILL.md provides the lightweight context when needed
