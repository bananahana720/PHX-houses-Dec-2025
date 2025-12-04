# CLI + Multi-Agent Data Pipeline Specific Requirements

### Project-Type Overview

PHX Houses Analysis Pipeline is a **command-line interface (CLI) tool** orchestrating a **multi-agent data pipeline** for property analysis. This project type has specific technical requirements around:

- CLI user experience and workflow patterns
- Multi-agent coordination and state management
- Data pipeline reliability and crash recovery
- Local-first data storage with optional cloud integrations
- Script-based extensibility and configuration management

### Technical Architecture Considerations

**CLI Interface Requirements:**

1. **Command Structure**
   - Primary command: `/analyze-property` with flags (--all, --test, --resume, --strict)
   - Manual script execution: `python scripts/phx_home_analyzer.py`
   - Phase-specific execution: `python scripts/extract_county_data.py --all`
   - Report generation: `python -m scripts.deal_sheets`

2. **Output & Logging**
   - Structured JSON output for pipeline state (work_items.json, enrichment_data.json)
   - Human-readable console logs with progress indicators
   - File-based artifacts (deal sheets, visualizations, risk checklists)
   - Error traces with actionable troubleshooting guidance

3. **Configuration Management**
   - YAML configuration files for scoring weights (config/scoring_weights.yaml)
   - CSV configuration for kill-switch criteria (config/kill_switch.csv)
   - Environment variables for secrets (.env file with MARICOPA_ASSESSOR_TOKEN)
   - Version-controlled defaults with local overrides

**Multi-Agent Architecture Requirements:**

1. **Agent Orchestration**
   - Slash command orchestrator: `/analyze-property` spawns phase-specific agents
   - Agent definitions in `.claude/agents/*.md` with model selection (Haiku vs Sonnet)
   - Skills library for domain expertise (`.claude/skills/*/SKILL.md`)
   - Agent briefing document (`.claude/AGENT_BRIEFING.md`) for shared context

2. **Phase Coordination**
   - Phase 0 (County Assessor): Synchronous data fetching, no agent needed
   - Phase 1 (Listings + Maps): Parallel agent execution (listing-browser + map-analyzer)
   - Phase 2 (Images): Sonnet agent for multi-modal visual assessment
   - Phase 3 (Synthesis): Main orchestrator aggregates and scores

3. **Agent Communication & State**
   - Shared state file: `data/work_items.json` (phase progress, retry metadata)
   - Property data file: `data/enrichment_data.json` (raw + derived data)
   - Pipeline state file: `data/extraction_state.json` (image pipeline checkpoints)
   - Agent-specific logs: `.claude/logs/agent_*.log`

**Data Pipeline Reliability:**

1. **Crash Recovery & Checkpointing**
   - Every phase writes checkpoint before spawning next agent
   - Resume capability: `--resume` flag continues from last successful checkpoint
   - State validation: `python scripts/validate_phase_prerequisites.py` before spawning
   - Rollback capability: Preserve previous state files with timestamps

2. **Prerequisite Validation**
   - Mandatory can_spawn checks before Phase 2 (images) and Phase 3 (synthesis)
   - Validation script returns JSON: `{"can_spawn": true/false, "missing_data": [...], "reasons": [...]}`
   - Blocking errors prevent agent spawn (exit code 1)
   - Warnings allow spawn with logged concerns

3. **Error Handling Strategies**
   - **Transient errors** (API rate limits, network issues): Retry with exponential backoff
   - **Recoverable errors** (anti-bot detection): Log error, preserve state, notify user to fix
   - **Fatal errors** (data corruption, schema mismatch): Stop pipeline, preserve state, require manual intervention

**Data Storage & Schema:**

1. **Local-First Storage**
   - Primary data store: `data/enrichment_data.json` (property data)
   - Pipeline state: `data/work_items.json` (phase tracking)
   - Image cache: `data/images/{address}/` (downloaded listing photos)
   - Generated artifacts: `docs/artifacts/deal_sheets/`, `data/visualizations/`

2. **Schema Management**
   - Pydantic schemas in `src/phx_home_analysis/validation/schemas.py`
   - Schema versioning in frontmatter (enrichment_data.json includes schema_version)
   - Migration scripts for schema updates (preserve backward compatibility)
   - Validation on load: All JSON files validated against Pydantic schemas

3. **Data Provenance & Quality**
   - Every field includes data_source and confidence_level metadata
   - Lineage tracking: Record which agent/phase populated each field
   - Quality gates: Minimum data thresholds before spawning next phase
   - Audit trail: Track when data was fetched and from which source

**Integration Architecture:**

1. **External API Integrations**
   - Maricopa County Assessor API (authoritative property data)
   - Google Maps API (geocoding, distances, orientation)
   - GreatSchools API (school ratings)
   - Planned: FEMA NFHL API (flood zones), WalkScore API (walkability)

2. **Browser Automation**
   - Primary: nodriver (stealth browsing for Zillow/Redfin)
   - Fallback: Playwright MCP (if stealth fails)
   - Proxy support: Residential proxy rotation for anti-bot bypass
   - Session management: Cookie persistence, User-Agent rotation

3. **Claude API Integration**
   - Agent spawning via Claude Code CLI
   - Model selection: Haiku (fast, cheap) for data tasks, Sonnet (capable) for vision
   - Cost optimization: ~$0.02/image for visual assessment
   - Token management: Context window tracking, compaction protocols

### Implementation Considerations

**Development Workflow:**

1. **CLI Development Patterns**
   - Use argparse for command-line argument parsing
   - Implement --dry-run mode for testing without side effects
   - Support --verbose flag for detailed logging
   - Provide --json flag for machine-readable output

2. **Agent Development Patterns**
   - Agent files in `.claude/agents/` with YAML frontmatter (model, skills, tools)
   - Shared context via `.claude/AGENT_BRIEFING.md` (required reading for all agents)
   - Skill composition: Agents load domain expertise via skills library
   - Testing: Manual agent testing via `.claude/commands/` slash commands

3. **Pipeline Development Patterns**
   - Each phase is independently executable (testability)
   - Phase outputs are idempotent (re-running produces same result)
   - State transitions are atomic (either complete or rolled back)
   - Logging is structured (JSON for parsing, human-readable for console)

**Operational Requirements:**

1. **Deployment & Execution**
   - Local execution on developer machine (no cloud deployment)
   - Python 3.12 virtual environment (uv package manager)
   - Git version control for code and configuration
   - Manual execution via CLI or scheduled cron jobs

2. **Maintenance & Monitoring**
   - Weekly scraping maintenance (anti-bot detection updates)
   - Monthly cost monitoring (Claude API, Google Maps API, proxies)
   - Quarterly Arizona context validation (HVAC lifespan, pool costs)
   - Annual kill-switch criteria review (buyer preferences may shift)

3. **Extensibility Points**
   - New scoring dimensions: Add to `config/scoring_weights.yaml`
   - New kill-switch criteria: Add to `config/kill_switch.csv`
   - New data sources: Implement in `scripts/extract_*.py`
   - New agents: Create in `.claude/agents/*.md` with skills
   - New skills: Add to `.claude/skills/*/SKILL.md`
