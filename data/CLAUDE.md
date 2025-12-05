---
last_updated: 2025-12-04T00:00:00Z
updated_by: agent
staleness_hours: 12
type: data-directory
---

# data/

## Purpose
Central repository for property data, pipeline state, and extracted images. Houses critical state files that drive multi-phase property analysis pipeline. **CRITICAL: 12-hour staleness threshold.**

## Contents
| File | Purpose | Access Pattern |
|------|---------|-----------------|
| `enrichment_data.json` | Master property data (LIST, not dict) | Read/write all phases |
| `work_items.json` | Pipeline progress tracking | Orchestrator only |
| `phx_homes.csv` | Source listing data | Read-only reference |
| `field_lineage.json` | Data provenance by phase | Append-only |
| `quality_baseline.json` | Data quality metrics | Validation updates |
| `property_images/` | Extracted images + metadata | Phase 1/2 assessment |

## Key Patterns
- **enrichment_data.json is a LIST**: Use list comprehension, never dict indexing. Always atomic write (tempfile + os.replace()).
- **Phase dependencies**: Phase 2 requires Phase 1 complete. Validate with `validate_phase_prerequisites.py` before spawning.
- **Address lookup**: Use `property_images/metadata/address_folder_lookup.json` to map address → hash folder.

## Tasks
- [ ] Implement data retention policy for old extraction reports `P:M`
- [ ] Add hourly backup snapshots for enrichment_data.json `P:H`
- [ ] Create work_items ↔ enrichment_data reconciliation script `P:M`

## Learnings
- **Race conditions**: Only orchestrator updates work_items.json. Agents read-only unless updating phase status.
- **Image folder lookup**: Never hardcode folder names; always validate via metadata lookup.
- **Concurrent writes**: JSONDecodeError on enrichment_data.json means atomic pattern was skipped.

## Refs
- Schema: `src/phx_home_analysis/validation/schemas.py:1-200`
- State mgmt: `scripts/lib/state_management.py:1-150`
- Property data skill: `.claude/skills/property-data/SKILL.md`
- Validation: `scripts/validate_phase_prerequisites.py`

## Deps
← imports: (none - data files only)
→ used by: phx_home_analyzer.py, extract_county_data.py, extract_images.py, listing-browser.md, map-analyzer.md, image-assessor.md, analyze-property.md

## Quick Commands
```bash
jq '.[] | select(.full_address == "123 Main St")' data/enrichment_data.json
jq '.work_items[] | select(.status != "complete")' data/work_items.json
python scripts/validate_phase_prerequisites.py --address "123 Main St" --phase phase2_images
```
