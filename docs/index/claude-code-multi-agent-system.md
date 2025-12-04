# Claude Code Multi-Agent System

### Agent Definitions
**Location:** `.claude/agents/`

1. **listing-browser.md** (Claude Haiku)
   - Extracts listing data from Zillow/Redfin
   - Uses stealth browsers (nodriver)
   - Outputs: price, beds, baths, HOA, images
   - Duration: ~30-60s per property

2. **map-analyzer.md** (Claude Haiku)
   - Geographic analysis (schools, crime, orientation)
   - Uses Google Maps, GreatSchools, crime APIs
   - Outputs: school_rating, safety_score, orientation, distances
   - Duration: ~45-90s per property

3. **image-assessor.md** (Claude Sonnet 4.5)
   - Visual scoring of interior quality (Section C: 190 pts)
   - Uses Claude Vision for image analysis
   - Outputs: kitchen, master, light, ceilings, fireplace, laundry, aesthetics scores
   - Duration: ~2-5 min per property
   - Prerequisites: Phase 1 complete, images downloaded

### Skill Modules
**Location:** `.claude/skills/`

- `property-data/` - Load, query, update property data
- `state-management/` - Checkpointing & crash recovery
- `kill-switch/` - Buyer criteria validation
- `scoring/` - 600-point scoring system
- `county-assessor/` - Maricopa County API
- `arizona-context/` - AZ-specific factors
- `arizona-context-lite/` - Lightweight AZ context for image assessment
- `listing-extraction/` - Browser automation
- `map-analysis/` - Schools, safety, distances
- `image-assessment/` - Visual scoring rubrics
- `exterior-assessment/` - Exterior visual scoring
- `deal-sheets/` - Report generation
- `visualizations/` - Charts & plots
- `quality-metrics/` - Data quality tracking
- `file-organization/` - File placement standards

### Slash Commands
**Location:** `.claude/commands/`

- `/analyze-property` - Multi-agent orchestrated analysis
- `/commit` - Git commit helper

---
