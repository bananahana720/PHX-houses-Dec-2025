# File Locations

**Input:**
- `data/phx_homes.csv` - Property list
- `data/enrichment_data.json` - Enrichment data
- `data/property_images/metadata/extraction_state.json` - Pipeline state
- `data/research_tasks.json` - Research queue

**Output:**
- `data/property_images/metadata/extraction_state.json` - Updated with phase_status
- `data/enrichment_data.json` - Updated with scores
- `data/property_images/processed/{hash}/` - Downloaded images
- `data/research_tasks.json` - Updated with new/completed tasks

---

*Implementation checklist for analyze-property orchestrator*
*Based on: .claude/commands/analyze-property.md (665 lines)*
*Date: 2025-11-30*
