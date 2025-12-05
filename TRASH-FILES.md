# TRASH-FILES.md

This document tracks files and directories that have been moved to the `/TRASH` directory as part of consolidation, refactoring, or deprecation efforts.

## Consolidated/Deprecated Items

| Item | Location | Reason | Date |
|------|----------|--------|------|
| `arizona-context-lite/` | `TRASH/skills/arizona-context-lite/` | Consolidated into arizona-context skill - arizona-context/SKILL.md now contains both Quick Ref (lite content) and Full Context sections. image-assessor.md agent updated to use arizona-context instead. | 2025-12-04 |
| `property_images/processed/16e902e2/` | `TRASH/property_images_backup_*/` | Fresh extract requested - clearing cached images for 7233 W Corrine Dr, Peoria | 2025-12-04 |
| `property_images/processed/b18bdfc7/` | `TRASH/property_images_backup_*/` | Fresh extract requested - clearing cached images for 5219 W El Caminito Dr, Glendale | 2025-12-04 |
| `property_images/processed/f4e29e2c/` | `TRASH/property_images_backup_*/` | Fresh extract requested - clearing cached images for 4560 E Sunrise Dr, Phoenix | 2025-12-04 |

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

## 2025-12-04 - Contaminated Image Data Cleanup

| Folder | Original Location | Reason |
|--------|------------------|--------|
| 84528a14/ | data/property_images/processed/TRASH/ | Search result contamination - multiple properties mixed |
| f4e29e2c/ | data/property_images/processed/TRASH/ | Search result contamination - 6-8 different properties |
| ed34c433/ | data/property_images/processed/TRASH/ | Search result contamination - multiple properties mixed |

**Context:** Wave 2 image assessment found contaminated data from search results page scraping instead of property gallery.
