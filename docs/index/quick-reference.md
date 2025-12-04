# Quick Reference

### Key Commands
```bash
# Run main analysis
python scripts/phx_home_analyzer.py

# Extract county data
python scripts/extract_county_data.py --all

# Extract images
python scripts/extract_images.py --all

# Validate prerequisites
python scripts/validate_phase_prerequisites.py --address "..." --phase phase2_images --json

# Generate deal sheets
python -m scripts.deal_sheets

# Multi-agent analysis
/analyze-property --all
```

### Key Files
```
CLAUDE.md                          # Primary reference
.claude/AGENT_BRIEFING.md          # Agent orientation
.claude/protocols.md               # Operational protocols
src/phx_home_analysis/config/constants.py  # All magic numbers
data/enrichment_data.json          # Property data (LIST!)
data/work_items.json               # Pipeline state
```

### Key Concepts
- **Kill-Switch:** Hard criteria (instant fail) + Soft criteria (severity accumulation)
- **Scoring:** 600 points across Location (250), Systems (170), Interior (180)
- **Tiers:** Unicorn (>480), Contender (360-480), Pass (<360)
- **Multi-Agent:** listing-browser + map-analyzer (parallel) → image-assessor (sequential)
- **Data Structure:** enrichment_data.json is a LIST, not dict!

---
