# Multi-Agent Development

### Creating a New Agent

1. **Create agent definition**
   ```markdown
   # .claude/agents/my-new-agent.md
   ---
   name: my-new-agent
   model: haiku
   skills: property-data, state-management
   ---

   # My New Agent

   ## Purpose
   Extract XYZ data from ABC source.

   ## Task
   You are responsible for...

   ## Skills
   - property-data: Load and update property data
   - state-management: Track progress

   ## Output Format
   Return structured JSON:
   ```json
   {
     "status": "success",
     "data": {...}
   }
   ```
   ```

2. **Create skill module (if needed)**
   ```markdown
   # .claude/skills/my-skill/SKILL.md
   # My Skill

   Provides capability to...

   ## Usage
   python scripts/my_script.py --address "..."
   ```

3. **Test agent**
   ```bash
   # Spawn agent with Task tool
   Task: Load my-new-agent and run on sample property
   ```

### Debugging Agents

1. **Check agent output**
   ```bash
   # Agent logs go to terminal
   # Look for errors, warnings
   ```

2. **Verify state files**
   ```bash
   # Check work_items.json for progress
   cat data/work_items.json | jq '.work_items[] | select(.address | contains("123"))'

   # Check enrichment_data.json for data
   cat data/enrichment_data.json | jq '.[] | select(.full_address | contains("123"))'
   ```

3. **Validate prerequisites**
   ```bash
   python scripts/validate_phase_prerequisites.py --address "123 Main St" --phase phase2_images --json
   ```

---
