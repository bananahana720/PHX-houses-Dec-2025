# SECTION 10: VISUAL ARCHITECTURE SUMMARY

### Context Loading Flow

```
User Command: /analyze-property "123 Main St"
  ↓
1. Read: Root CLAUDE.md (project orientation)
2. Read: data/work_items.json (current progress)
3. Load: .claude/AGENT_BRIEFING.md (state shortcuts)
4. Determine: Phase 0, 1, 2, 3, or 4?
  ↓
Phase 0 (County Data):
  └─ Use: scripts/extract_county_data.py (Tier 2)
  └─ Update: enrichment_data.json
  └─ Check: protocols.md for no-deviation rule
  ↓
Phase 1 (Listing):
  └─ Spawn: listing-browser agent
  └─ Provide: AGENT_BRIEFING.md context
  └─ Skills: property-data, listing-extraction, kill-switch
  └─ Call: scripts/extract_images.py (Tier 2)
  ↓
Phase 2 (Images):
  ├─ Validate: python scripts/validate_phase_prerequisites.py
  ├─ If blocked: Return error, do NOT spawn agent
  ├─ If can_spawn=true: Spawn image-assessor agent
  └─ Skills: property-data, image-assessment, arizona-context-lite
  ↓
Phase 3 (Synthesis):
  └─ Use: scripts/phx_home_analyzer.py (Tier 2)
  └─ Calculate: total_score, tier, kill_switch_verdict
  ↓
Phase 4 (Reports):
  └─ Use: scripts/deal_sheets/, visualizations (Tier 2)
```

### Tool Hierarchy in Action

```
CORRECT SELECTION PROCESS:

Task: Find all properties with HOA > $0

Option A: Bash grep ❌
  grep '"hoa_fee"' data/enrichment_data.json

Option B: Grep tool ✓
  Grep tool (pattern='hoa_fee.*[1-9]', path='data/')

Option C: Skill invocation ✓
  Skill: property-data → query_by_criterion(hoa_fee > 0)

BEST CHOICE: Option C (Skill)
- Domain knowledge encapsulated
- Tool constraints enforced
- Reusable across agents
```

---
