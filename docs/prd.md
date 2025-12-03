---
stepsCompleted: [1, 2, 3, 4, 6, 7, 8, 9, 10]
inputDocuments:
  # Brainstorming Session
  - docs/analysis/brainstorming-session-2025-12-03.md
  # Project Documentation
  - docs/index.md
  # Research Reports (12 files)
  - docs/analysis/research/EXECUTIVE_SUMMARY_2024-12.md
  - docs/analysis/research/ACTION_ITEMS_MATRIX_2024-12.md
  - docs/analysis/research/SCORING_SYSTEM_UPDATE_SPEC_2024-12.md
  - docs/analysis/research/market-alpha-financial-baseline-2024-12.md
  - docs/analysis/research/market-beta-pool-solar-economics-2024-12.md
  - docs/analysis/research/market-gamma-demographics-appreciation-2024-12.md
  - docs/analysis/research/domain-alpha-building-systems-2024-12.md
  - docs/analysis/research/domain-beta-regulations-2024-12.md
  - docs/analysis/research/domain-gamma-land-infrastructure-2024-12.md
  - docs/analysis/research/tech-alpha-government-apis-2024-12.md
  - docs/analysis/research/tech-beta-data-apis-2024-12.md
  - docs/analysis/research/tech-gamma-scraping-infrastructure-2024-12.md
  # Gap Analysis Artifacts (17 files)
  - docs/artifacts/brainstorming-2025-12-03/GAP_ANALYSIS_SYNTHESIS.md
  - docs/artifacts/brainstorming-2025-12-03/GAP_ANALYSIS_EXECUTIVE_SUMMARY.md
  - docs/artifacts/brainstorming-2025-12-03/ARCHITECTURE_SUMMARY.md
workflowType: 'prd'
lastStep: 10
project_name: 'PHX-houses-Dec-2025'
user_name: 'Andrew'
date: '2025-12-03'
---

# Product Requirements Document - PHX-houses-Dec-2025

**Author:** Andrew
**Date:** 2025-12-03

## Executive Summary

**PHX Houses Analysis Pipeline** is a personal decision support system that evaluates Phoenix-area residential properties against strict first-time homebuyer criteria. The system transforms raw listing data into actionable intelligence through multi-agent analysis, risk detection, and comprehensive deal sheets.

### Vision

Enable confident, data-driven home purchase decisions by systematically surfacing both obvious deal-breakers and hidden risks that could impact long-term ownership satisfaction — while reducing the decision anxiety that makes home buying one of life's most stressful experiences.

### Problem Statement

First-time homebuyers face **asymmetric risk exposure** — they bear 100% of the financial consequences while having access to maybe 20% of the relevant decision factors.

1. **Arizona-specific factors are invisible** — HVAC units fail 20-40% faster than national averages, solar leases create hidden liabilities, pool ownership costs $300-400/month
2. **Generic tools miss local context** — National real estate platforms don't account for desert climate impacts, groundwater restrictions, or Phoenix market dynamics
3. **Risk discovery is reactive** — Buyers typically learn about septic failures, flood zones, or HOA restrictions after emotional investment in a property
4. **Decision fatigue is real** — Manually evaluating dozens of properties across 20+ criteria is exhausting and error-prone
5. **Emotional cost compounds** — The stress of uncertainty leads to decision paralysis or buyer's remorse

### Solution

A personal decision support system that:
- **Filters aggressively** via kill-switch criteria (HOA, beds, baths, solar leases, flood zones)
- **Scores comprehensively** across 600 points (Location 230, Systems 180, Interior 190)
- **Explains transparently** why each property scored as it did
- **Warns proactively** about hidden concerns with confidence levels
- **Adapts flexibly** — raw data preserved for re-scoring when priorities shift

### What Makes This Special

**Proactive Risk Intelligence** — The system doesn't just filter and rank; it surfaces unknown unknowns and connects them to consequences you actually care about:

| Consequence | Risk Sources | Why It Matters | Confidence |
|-------------|--------------|----------------|------------|
| **Surprise $10K+ expense** | HVAC age, roof underlayment, foundation, pool equipment | Cash reserve wipeout | Medium |
| **Resale value hit** | Flood zone, flight path, solar lease, water security | Equity erosion | High |
| **Daily quality of life** | Noise, crime, wildlife corridors, HOA disputes | Regret accumulation | Medium |
| **Time sink** | Septic maintenance, long commute, poor walkability | Opportunity cost | Medium |

**The "Aha" Moments:**

| Moment | What Happens | Emotional Payoff |
|--------|--------------|------------------|
| **"NOW I understand"** | Score breakdown shows exactly why a property felt wrong | Clarity replaces gut unease |
| **"This is THE one"** | Property passes all kill-switches, scores 500+, deal sheet confirms | Confidence to act decisively |
| **"Bullet dodged"** | Warning surfaces hidden risk (solar lease, flood zone, septic age) | Relief — avoided a $50K mistake |
| **"My priorities shifted"** | Re-score with different weights when commute matters more than yard | System adapts, data preserved |

## Project Classification

**Technical Type:** Personal Decision Support System (CLI + Multi-Agent Data Pipeline)

**Domain:** PropTech / Real Estate Analysis (Personal Use)

**Complexity:** Medium-High
- Multiple API integrations (County Assessor, FEMA, GreatSchools, Google Maps)
- Multi-agent architecture (3 specialized Claude agents)
- 4-phase pipeline with state management and crash recovery
- Multi-modal analysis (text, images, geographic data)
- No regulatory compliance requirements (personal tool)

**Primary Deliverable:** Deal sheets and risk reports — comprehensive property analysis documents that support confident go/no-go decisions and reduce buyer's remorse risk.

## Implementation Status

| Capability | Status | Gap ID | Notes |
|------------|--------|--------|-------|
| Kill-switch filtering | Production | — | 7 criteria, hard + soft severity |
| 600-point scoring | Production | — | 18 scoring strategies |
| Multi-agent pipeline | Production | IP-01-04 | Works, but blocks 30+ min (no background jobs) |
| Score explanations | Partial | XT-09 | Returns breakdown, not human reasoning |
| Proactive warnings | Partial | VB-01, VB-03 | Kill-switch warns, but no foundation/risk narrative |
| Consequence mapping | Planned | — | Risk → outcome mapping not implemented |

**MVP Gaps to Address:**
- **XT-09:** Scoring explainability (3-5 days)
- **IP-01:** Background job infrastructure (5 days)
- **VB-03:** Foundation assessment service (5 days)

## Data Input Costs

### Monthly Operating Cost (100 properties): $35-90

| Category | Estimate | Notes |
|----------|----------|-------|
| Proxy costs (scraping) | $10-30 | Residential proxies for Zillow/Redfin |
| Google Maps API | $5-10 | Geocoding, distances |
| Claude API (scoring + vision) | $20-50 | ~$0.02/image for visual assessment |
| **Total** | **$35-90** | |

**Time Investment:** 2-4 hours/month for scraping maintenance when anti-bot systems update.

### Integration Backlog

| Integration | Effort | Status | Value |
|-------------|--------|--------|-------|
| FEMA flood zone | 4 hours | Planned | High — kill-switch data |
| WalkScore | 4 hours | Planned | Medium — location scoring |
| Phoenix crime data | 8 hours | Planned | Medium — safety scoring |
| Septic detection | 8 hours | Planned | Medium — risk warning |

## Risk Intelligence Confidence Levels

| Data Point | Source | Confidence | Caveat |
|------------|--------|------------|--------|
| Flood zone | FEMA NFHL | High | Authoritative federal data (once integrated) |
| Lot size, year built | County Assessor | High | Official records |
| School ratings | GreatSchools | High | Established methodology |
| HVAC/roof age | Listing data | Medium | Often missing, requires inference |
| Solar ownership | Seller disclosure | Medium | Depends on disclosure compliance |
| Foundation condition | Visual assessment | Medium | Interpretive, not diagnostic |
| Noise/crime | Public data | Medium | Data quality varies by area |
| Neighborhood trajectory | Market analysis | Low | Speculative, trend-based |

## Success Criteria

### User Success

**Primary Success Scenario:** Confidently rule out bad properties through systematic elimination.

Success is NOT "find the perfect house" — it's "never accidentally pursue a bad one." The system wins when:

1. **Every property I consider has passed rigorous filtering** — no time wasted on deal-breakers
2. **I understand WHERE my points came from** — transparent score breakdowns by dimension with key contributing factors, not black-box numbers
3. **Hidden risks are surfaced BEFORE emotional investment** — bullets dodged, not discovered at inspection
4. **Decision fatigue is minimized** — batch analysis replaces manual Zillow research

**The Win Condition:** Go under contract on a property that:
- Scores 450+ with high confidence
- Passes ALL non-negotiable criteria
- Has no surprises discovered during due diligence that the system should have caught

### Business Success

| Milestone | Target Date | Success Criteria |
|-----------|-------------|------------------|
| **System Operational** | Dec 2025 | Kill-switches + scoring + deal sheets working |
| **Property Pipeline Active** | Jan 2026 | 50+ properties evaluated, shortlist of 5-10 |
| **Under Contract** | Jan-Feb 2026 | Offer accepted on 450+ score property |
| **Close of Escrow** | Mar-Apr 2026 | Purchase complete, no post-close surprises |

**Post-Purchase Validation:** 6 months after move-in, no major issues surface that the system should have predicted.

### Technical Success

| Metric | Target | Rationale |
|--------|--------|-----------|
| Kill-switch accuracy | 100% | Zero false passes on non-negotiables |
| Scoring consistency | ±5 points on re-run | Deterministic, reproducible results |
| Batch processing time | <30 min for 20 properties | Usable in a single session |
| Data freshness | <7 days for listing data | Market moves fast |
| Explanation clarity | Self-service understanding | Don't need to debug the system to trust it |

### Measurable Outcomes

**By End of December 2025:**
- [ ] 100+ Phoenix properties evaluated
- [ ] Kill-switch criteria updated to match non-negotiables
- [ ] At least 1 "Unicorn" (500+) or 5+ "Contenders" (450-500) identified
- [ ] Deal sheets generated for all Contender+ properties

**By End of January 2026:**
- [ ] Top 5 properties toured in person
- [ ] At least 1 offer submitted on 450+ property
- [ ] Zero "should have caught that" surprises during inspections

**By End of February 2026:**
- [ ] Under contract on qualifying property
- [ ] Inspection completed with no system-predictable surprises

### Non-Negotiable Kill-Switch Criteria

| Criterion | Requirement | Type |
|-----------|-------------|------|
| Bedrooms | 4+ | HARD |
| Bathrooms | 2+ | HARD |
| House SQFT | >1800 | HARD (NEW) |
| Lot Size | >8000 sqft | HARD (upgraded) |
| Garage | Indoor garage | HARD (clarified) |
| HOA | $0 | HARD |
| Sewer | City only | HARD (upgraded) |

## Product Scope

### MVP - Minimum Viable Product (NOW)

**What must work to start evaluating properties:**

| Capability | Status | Priority |
|------------|--------|----------|
| Kill-switch filtering (updated criteria) | Needs update | P0 |
| 600-point scoring | Done | — |
| Deal sheet generation | Done | — |
| Multi-agent image analysis | Done | — |
| Basic score breakdown | Done | — |

**Kill-Switch Updates Required for MVP:**

| Criterion | Change | Type |
|-----------|--------|------|
| House SQFT | ADD: >1800 sqft required | HARD |
| Lot Size | CHANGE: >8000 sqft (was 7k-15k) | HARD |
| Sewer | UPGRADE: City only (was SOFT 2.5) | HARD |
| Garage | CLARIFY: Indoor garage required | HARD |

### Growth Features (Post-MVP)

| Feature | Gap ID | Value |
|---------|--------|-------|
| Score explanations in natural language | XT-09 | Understand WHY |
| Background job processing | IP-01 | No 30-min blocking |
| FEMA flood zone integration | — | Kill-switch data |
| Foundation assessment | VB-03 | Risk detection |

### Vision (Future)

- Real-time listing monitoring with alerts
- Automated offer generation for 500+ properties
- Portfolio comparison across multiple buyers
- Market trend integration (appreciation prediction)
- Mobile-friendly deal sheet viewer

## User Journeys

### Journey 1: Andrew - First-Time Buyer Seeking Confidence Through Systematic Elimination

Andrew is a first-time homebuyer with savings ready and a clear timeline: under contract by Jan-Feb 2026. He's scrolling through Zillow on yet another evening, frustrated by the endless stream of properties and the nagging anxiety that he'll miss a hidden red flag. A gorgeous house catches his eye - 4 bed, 2.5 bath, pool, perfect - but then he notices the HOA fee of $150/month. He adds it to his "maybe" list, but the doubt creeps in. What else is he missing?

Instead of continuing his Zillow doom-scrolling, Andrew runs his batch analysis pipeline on 50 new Phoenix listings. The system instantly filters out 35 properties including his "maybe" - not just for the HOA, but because it's also on septic (soft kill-switch severity 2.5), bringing total severity to 2.5, dangerously close to the 3.0 failure threshold. The system flags this with a WARNING: "Close to fail threshold."

The breakthrough comes when he reviews his deal sheets the next morning. Five "Contender" properties (450-500 points) remain, each with detailed breakdowns explaining exactly WHY they scored as they did. One property in North Phoenix scores 487 points - excellent school ratings (High School: 9/10), perfect north-facing orientation (30 points), city sewer, 2-car indoor garage, 9,200 sqft lot. The deal sheet surfaces no warnings, only a note about HVAC age (12 years - expect replacement in 3-5 years, budget $7-10K). Andrew schedules a tour with confidence, not anxiety. He knows exactly what he's evaluating and what questions to ask.

**Key Requirements Revealed:**
- Kill-switch filtering (HARD criteria: HOA, beds, baths, sqft, lot, garage, sewer)
- Kill-switch severity scoring (SOFT criteria accumulation with threshold)
- 600-point scoring system with transparent breakdowns
- Deal sheet generation with warnings and hidden risk detection
- Batch processing for 20-50 properties
- Score breakdown clarity (point allocation per dimension with key data points)

### Journey 2: Andrew - Discovering the Unicorn Through Proactive Risk Intelligence

Three weeks into his search, Andrew has toured 8 "Contender" properties. None felt quite right - small lots, west-facing orientations, aging HVAC systems, or concerning foundation cracks. He's starting to worry his standards are too high. But then the system identifies a new listing: 16814 N 31st Ave, Phoenix.

He opens the deal sheet and his eyes widen: **522 points - UNICORN TIER**. The score breakdown reveals the point allocation:
- **Location (189/230):** Top-rated schools (Elementary 10/10, Middle 9/10, High 9/10), low crime, excellent walkability, quiet neighborhood, 15-minute commute to work
- **Systems (154/180):** 2023 construction year (NEW), city sewer, 2-car indoor garage, no solar lease liability, no pool maintenance costs
- **Interior (179/190):** 4 bed, 2.5 bath, 2,100 sqft, 9,800 sqft lot, excellent condition per image analysis

**But most importantly:** The system proactively surfaces insights he wouldn't have known to ask about:
- "Foundation: Excellent condition (2023 construction, no settling yet)" - dodged a hidden risk
- "HVAC: New system, 15+ year expected life in AZ climate" - no near-term expense
- "Orientation: North-facing backyard - optimal for cooling costs" - $100-200/month savings
- "Water: City utilities, no groundwater restrictions" - long-term security

Andrew submits an offer within 48 hours of the listing going live. During inspection, zero surprises emerge that the system should have caught. He goes under contract with confidence, not buyer's remorse anxiety.

**Key Requirements Revealed:**
- Tier classification (Unicorn >480, Contender 360-480, Pass <360)
- Proactive warning system (foundation, HVAC, orientation, utilities)
- Consequence mapping (hidden risks → $ impact or quality of life)
- Image-based condition assessment (Phase 2 visual analysis)
- Multi-agent pipeline (county data, listing extraction, map analysis, image assessment)
- Confidence levels for data points (High/Medium/Low)

### Journey 3: Andrew - Re-Scoring When Priorities Shift

After two months of searching, Andrew's job situation changes - his employer announces a permanent remote work policy. Suddenly, his 15-minute commute requirement becomes irrelevant, and he realizes he'd trade proximity to work for a larger lot and better outdoor space. Properties he previously ruled out in Surprise or Peoria might now be viable.

Instead of starting his research from scratch, Andrew adjusts his scoring weights in the configuration:
- **Proximity to Work:** Reduce from 20 points → 5 points
- **Lot Size:** Increase from 15 points → 25 points
- **Outdoor Space Quality:** Increase from 10 points → 20 points

He re-runs the scoring pipeline on his existing enrichment_data.json file containing 100+ properties. The system recalculates scores in under 5 minutes. Properties that were previously "Pass" tier (350-370 points) now jump to "Contender" tier (420-450 points) because of their larger lots and better outdoor spaces. The raw data was preserved - he didn't need to re-scrape or re-analyze everything.

A property in Surprise that previously scored 368 now scores 438. The deal sheet regenerates with updated scoring breakdown, showing exactly which dimensions changed and by how much. Andrew schedules tours for 3 properties in Surprise and Peoria that he had previously dismissed.

**Key Requirements Revealed:**
- Configurable scoring weights (user-adjustable priorities)
- Data preservation (raw data separate from scores)
- Re-scoring pipeline (calculate new scores from existing data)
- Score delta tracking (show what changed and why)
- Configuration management (externalized weights in config files)
- Fast re-processing (< 10 minutes for 100 properties)

### Journey 4: System Administrator - Pipeline Maintenance and Debugging

Andrew is running his weekly batch analysis when the Zillow extraction agent fails with an "Anti-bot detection" error. The scraping infrastructure (nodriver stealth browser) worked last week but now Zillow has updated their bot detection. He needs to diagnose and fix the issue without losing his pipeline progress.

He checks `data/work_items.json` (pipeline state tracking) and sees that Phase 0 (County Assessor data) completed successfully for all 20 properties, but Phase 1 (listing extraction) failed at property 7 of 20. The state management system preserved the successful Phase 0 data and marked Phase 1 as "in_progress" with retry metadata.

Andrew reviews the extraction logs and sees the specific anti-bot signature that's failing. He updates the stealth browser configuration with a new User-Agent rotation strategy and adds a randomized delay pattern. He runs the Phase 1 prerequisite validator script, which confirms the fix is working in a test environment.

He restarts the Phase 1 extraction with `--resume` flag, and the system picks up from property 7, using the preserved Phase 0 data for properties 1-6. All 20 properties complete extraction successfully. Phase 2 (image assessment) spawns automatically because the prerequisite validation passes.

**Key Requirements Revealed:**
- State management and crash recovery (work_items.json checkpointing)
- Phase prerequisite validation (can_spawn checks before agent spawns)
- Resume capability (--resume flag to continue from checkpoint)
- Logging and debugging tools (extraction logs, error traces)
- Anti-bot maintenance (stealth browser configuration updates)
- Test harness (validate fixes before production runs)

### Journey Requirements Summary

The user journeys reveal the following capability areas needed for PHX Houses Analysis Pipeline:

**1. Property Filtering & Scoring**
- Kill-switch criteria enforcement (HARD + SOFT with severity accumulation)
- 600-point scoring system (Location 230, Systems 180, Interior 190)
- Tier classification (Unicorn/Contender/Pass thresholds)
- Configurable scoring weights (user-adjustable priorities)
- Re-scoring pipeline (fast recalculation from preserved data)

**2. Data Acquisition & Enrichment**
- Multi-phase pipeline (Phase 0: County, Phase 1: Listings/Maps, Phase 2: Images, Phase 3: Synthesis)
- Multi-agent architecture (listing-browser, map-analyzer, image-assessor)
- Stealth browser automation (anti-bot bypass for Zillow/Redfin)
- County Assessor API integration (authoritative property data)
- Geographic analysis (schools, crime, distances, orientation)
- Visual assessment (image-based condition scoring)

**3. Risk Intelligence & Warnings**
- Proactive warning system (foundation, HVAC, orientation, utilities)
- Consequence mapping (risk → $ impact or quality of life impact)
- Confidence levels (High/Medium/Low for data provenance)
- Hidden risk detection (solar leases, flood zones, septic age)
- Arizona-specific factors (HVAC lifespan, pool costs, orientation impact)

**4. Analysis Outputs & Reports**
- Deal sheet generation (comprehensive property reports)
- Score breakdown explanations (transparency into WHY)
- Tier-based recommendations (actionable go/no-go guidance)
- Visual comparisons (radar charts, value spotter plots)
- Batch processing (20-50 properties per session)

**5. System Reliability & Operations**
- State management (crash recovery, checkpointing)
- Phase prerequisite validation (safety gates before agent spawns)
- Resume capability (continue from checkpoint after failures)
- Data preservation (raw data separate from derived scores)
- Configuration management (externalized weights and thresholds)
- Logging and debugging (extraction logs, error traces)

## Innovation & Novel Patterns

### Detected Innovation Areas

While the core concept of automated property analysis exists in various forms, PHX Houses Analysis Pipeline introduces several novel patterns:

**1. Consequence-First Risk Intelligence**

Traditional property analysis tools filter and rank. This system goes further by mapping risks to tangible consequences that buyers actually care about:

- **Not**: "This property has a solar lease"
- **Instead**: "Solar lease creates $15K-25K liability at resale + limits financing options for 60% of buyers"

This shifts from data points to decision intelligence - helping users understand not just WHAT the risks are, but WHY they matter for long-term ownership satisfaction.

**2. Multi-Agent Specialist Architecture**

Most property analysis tools use monolithic processing or simple pipelines. This system employs a **multi-agent architecture with model optimization**:

- **Haiku agents** (listing-browser, map-analyzer): Fast, efficient for data extraction and structured analysis
- **Sonnet agent** (image-assessor): Multi-modal analysis for visual condition assessment

This is novel in PropTech personal tools - typically reserved for enterprise systems. The architecture enables:
- Parallel processing within phases
- Model-to-task optimization (cost and capability matching)
- Graceful degradation (if one agent fails, others can continue)

**3. Arizona-Specific Contextual Intelligence**

National real estate platforms (Zillow, Redfin, Realtor.com) provide generic analysis. This system embeds **hyperlocal domain expertise**:

- HVAC lifespan: 10-15 years in Phoenix vs 20+ years nationally
- Pool economics: $250-400/month total ownership cost (often hidden)
- Orientation impact: North-facing yards save $100-200/month in cooling costs
- Solar lease liability: Transfer challenges unique to AZ market dynamics

This localization isn't just data - it's consequence calibration. A 12-year-old HVAC unit triggers different warnings in Phoenix (expect replacement soon) than in Seattle (half its life remaining).

**4. Adaptive Prioritization Through Re-Scoring**

Most analysis tools require re-running expensive scraping and analysis pipelines when user priorities change. This system separates:

- **Raw data layer** (preserved, immutable)
- **Derived scoring layer** (fast recalculation from weights)

Users can adjust scoring weights (e.g., commute vs lot size) and re-score 100+ properties in minutes, not hours. The system tracks deltas and explains what changed and why.

### Market Context & Competitive Landscape

**Existing Solutions:**
- **Zillow/Redfin/Realtor.com**: Generic national tools, no hyperlocal intelligence, no consequence mapping
- **HomeLight/Opendoor**: Focus on transaction facilitation, not deep analysis
- **PropertyShark/Reonomy**: Enterprise tools ($thousands/year), not personal-use focused

**PHX Houses Differentiation:**
- Personal tool economics ($35-90/month, not $3K+/year)
- Hyperlocal Arizona intelligence
- Consequence-driven risk communication
- Adaptive scoring without re-analysis
- Multi-agent architecture with model optimization

### Validation Approach

**Technical Validation:**
- Multi-agent pipeline operational in production
- 600-point scoring system validated against 100+ properties
- Kill-switch criteria tuned through real-world property evaluation
- Image assessment accuracy validated through property tours (zero should-have-caught surprises)

**Market Validation:**
- Primary user (Andrew) testing through actual home search Jan-Feb 2026
- Success metric: Under contract on 450+ property with no post-close surprises
- Post-6-months validation: No major issues surface that system should have predicted

**Innovation Risk:**
- Multi-agent architecture complexity → Mitigated by phase prerequisite validation and crash recovery
- Hyperlocal intelligence maintenance → Validated through 12+ months Arizona market observation
- Consequence mapping accuracy → Validated through property inspection outcomes

### Risk Mitigation

**Key Innovation Risks:**

1. **Multi-Agent Reliability**
   - Risk: Agent spawning failures, coordination issues
   - Mitigation: Phase prerequisite validation (mandatory can_spawn checks), state management with crash recovery
   - Fallback: Manual phase execution scripts

2. **Arizona Context Accuracy**
   - Risk: Hyperlocal intelligence becomes outdated or inaccurate
   - Mitigation: Annual review of AZ-specific factors (HVAC lifespan, pool costs, solar market)
   - Fallback: Generic scoring available if AZ factors removed

3. **Consequence Mapping Calibration**
   - Risk: Risk → consequence mappings don't match real-world outcomes
   - Mitigation: Post-purchase validation (6-month check), continuous calibration
   - Fallback: Conservative warnings (over-warn rather than under-warn)

## CLI + Multi-Agent Data Pipeline Specific Requirements

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

## Project Scoping & Phased Development

### MVP Strategy & Philosophy

**MVP Approach:** Problem-Solving MVP with Experience Focus

The MVP philosophy is **systematic elimination** - help Andrew confidently rule out bad properties through rigorous, automated filtering and risk intelligence. Success is NOT finding the perfect house; it's never accidentally pursuing a bad one.

**Key MVP Principles:**

1. **Filter Aggressively First** - Kill-switch criteria eliminate 60-70% of properties instantly
2. **Score Comprehensively Second** - 600-point system ranks the survivors
3. **Warn Proactively Third** - Surface hidden risks BEFORE emotional investment
4. **Explain Transparently Always** - Score breakdowns show WHY, not just WHAT

**Resource Requirements:**

- **Team size:** 1 (Andrew as developer + primary user)
- **Skills needed:** Python, CLI development, multi-agent orchestration, web scraping
- **External dependencies:** Claude API ($20-50/month), Google Maps API ($5-10/month), proxies ($10-30/month)
- **Time investment:** 2-4 hours/month maintenance (anti-bot updates), ad-hoc development for enhancements

### MVP Feature Set (Phase 1) - DECEMBER 2025

**Timeline:** Operational by end of December 2025 for January 2026 home search

**Core User Journeys Supported:**

1. **Journey 1:** Systematic elimination through kill-switch filtering and scoring
2. **Journey 2:** Unicorn discovery through comprehensive analysis and proactive warnings
3. **Journey 4:** Pipeline maintenance and crash recovery (operational reliability)

**Must-Have Capabilities:**

**Kill-Switch Filtering (P0 - UPDATED):**
- [x] HARD criteria: 4 bed, 2 bath, >1800 sqft, >8000 lot, indoor garage, $0 HOA, city sewer
- [ ] Update: House SQFT from implicit to explicit HARD (>1800)
- [ ] Update: Lot Size from 7k-15k range to >8000 minimum HARD
- [ ] Update: Sewer from SOFT (2.5 severity) to HARD (city only)
- [ ] Update: Garage from implicit to explicit HARD (indoor garage required)

**Scoring System (P0 - PRODUCTION):**
- [x] 600-point system (Location 230, Systems 180, Interior 190)
- [x] 18 scoring strategies operational
- [x] Tier classification (Unicorn >480, Contender 360-480, Pass <360)
- [ ] Update: Threshold adjustment if needed based on initial batch (currently 450+ target)

**Multi-Agent Pipeline (P0 - PRODUCTION WITH GAPS):**
- [x] Phase 0: County Assessor data extraction
- [x] Phase 1: Listing extraction (Zillow/Redfin) + Map analysis (schools, crime, orientation)
- [x] Phase 2: Image assessment (visual condition scoring)
- [x] Phase 3: Synthesis and scoring
- [ ] Fix: Background job infrastructure (currently blocks 30+ minutes) - IP-01 gap

**Analysis Outputs (P0 - PRODUCTION):**
- [x] Deal sheet generation (comprehensive property reports)
- [x] Score breakdowns (numerical decomposition)
- [ ] Enhancement: Score explanations (natural language "WHY") - XT-09 gap
- [x] Tier-based recommendations (go/no-go guidance)
- [x] Batch processing (20-50 properties per session)

**State Management (P0 - PRODUCTION):**
- [x] Crash recovery via work_items.json checkpointing
- [x] Phase prerequisite validation (can_spawn checks)
- [x] Resume capability (--resume flag)
- [x] Data preservation (raw data separate from derived scores)

**Out of Scope for MVP (Deferred to Phase 2+):**

- Journey 3 support (re-scoring when priorities shift) - configurable weights exist but UI/workflow not polished
- FEMA flood zone integration - planned but not blocking for December
- Foundation assessment service (VB-03) - partial visual assessment only
- WalkScore/crime data integrations - manual research acceptable for MVP
- Automated listing monitoring - manual batch runs acceptable

### Post-MVP Features

**Phase 2 (Post-MVP) - JANUARY-FEBRUARY 2026**

**Target:** Enhance decision confidence during active home search

1. **Score Explainability (XT-09) - 3-5 days**
   - Natural language explanations of WHY properties scored as they did
   - Comparative analysis ("This scored 487 because... vs 450 average")
   - Consequence narrative generation for warnings

2. **Background Job Infrastructure (IP-01) - 5 days**
   - Non-blocking pipeline execution (run in background)
   - Progress monitoring via status file
   - Notification when analysis complete
   - Eliminates 30-minute blocking wait

3. **Foundation Assessment (VB-03) - 5 days**
   - Enhanced visual analysis for foundation condition
   - Crack pattern recognition and severity classification
   - Risk scoring and repair cost estimation
   - Integration with proactive warning system

4. **FEMA Flood Zone Integration - 4 hours**
   - FEMA NFHL API integration
   - Add flood zone to kill-switch criteria (HARD fail)
   - Flood risk consequence mapping (insurance costs, resale impact)

5. **Re-Scoring Workflow Refinement - 2 days**
   - CLI command for weight adjustment (`/adjust-weights`)
   - Score delta tracking and visualization
   - Deal sheet regeneration with change highlights
   - Polished UX for Journey 3 (priority shift scenario)

**Phase 3 (Expansion) - POST-PURCHASE (2026+)**

**Target:** Long-term tool evolution and knowledge preservation

1. **Real-Time Listing Monitoring**
   - Daily/weekly Zillow scraping
   - New listing alerts via email or Slack
   - Automatic analysis for new properties matching criteria

2. **Automated Offer Generation**
   - Offer price calculation based on comps and scoring
   - Contingency recommendations based on risk analysis
   - Contract template generation

3. **Portfolio Comparison**
   - Multi-buyer support (if helping friends/family)
   - Criteria profile management
   - Comparative deal sheets

4. **Market Trend Integration**
   - Historical appreciation data
   - Neighborhood trajectory predictions
   - Investment return modeling

5. **Mobile Deal Sheet Viewer**
   - Web-based responsive viewer for deal sheets
   - Mobile-optimized layout for property tours
   - Offline mode for inspection visits

### Risk Mitigation Strategy

**Technical Risks:**

1. **Multi-Agent Coordination Failures**
   - **Risk:** Agent spawning fails, state corruption, phase coordination issues
   - **Mitigation:** Phase prerequisite validation (mandatory can_spawn checks), state checkpointing, resume capability
   - **Contingency:** Manual phase execution scripts as fallback, roll back to last successful checkpoint
   - **Monitoring:** Agent-specific logs, pipeline state auditing

2. **Web Scraping Brittleness**
   - **Risk:** Zillow/Redfin anti-bot detection breaks extraction
   - **Mitigation:** Stealth browser (nodriver), proxy rotation, User-Agent rotation, weekly maintenance monitoring
   - **Contingency:** Playwright MCP fallback, manual data entry for critical properties, pause pipeline until fixed
   - **Monitoring:** Extraction success rate tracking, error pattern analysis

3. **API Rate Limiting / Outages**
   - **Risk:** County Assessor API, Google Maps API, GreatSchools API rate limits or downtime
   - **Mitigation:** Exponential backoff retry logic, API response caching, rate limit monitoring
   - **Contingency:** Continue with partial data (mark confidence as Low), retry failed properties later
   - **Monitoring:** API response time and error rate tracking

**Market Risks:**

1. **Timeline Pressure**
   - **Risk:** Andrew needs to be under contract by Jan-Feb 2026 - tight deadline
   - **Mitigation:** MVP operational by end of December 2025, prioritize P0 features only
   - **Contingency:** Manual analysis for final shortlist if system not ready, fall back to Zillow + manual research
   - **Success metric:** 50+ properties evaluated by mid-January 2026

2. **Criteria Evolution**
   - **Risk:** Andrew's non-negotiables shift during search (e.g., commute becomes less important)
   - **Mitigation:** Configurable scoring weights (externalized), re-scoring capability without re-analysis
   - **Contingency:** Manual override for borderline properties, quick config updates and re-run
   - **Monitoring:** Track criteria changes and impact on property scores

3. **Market Inventory Shortage**
   - **Risk:** Not enough properties meet criteria in Phoenix metro
   - **Mitigation:** Broader geographic search (Surprise, Peoria, Goodyear), criteria relaxation analysis
   - **Contingency:** Adjust kill-switch thresholds (e.g., 7500 sqft lot instead of 8000), expand search radius
   - **Monitoring:** Track property pass/fail rates and tier distribution

**Resource Risks:**

1. **Solo Developer Capacity**
   - **Risk:** Andrew is solo developer + primary user - no team redundancy
   - **Mitigation:** Simple, maintainable architecture, extensive documentation, code commented for future Andrew
   - **Contingency:** Pause development for critical bugs only, defer enhancements to Phase 2+
   - **Monitoring:** Time spent on maintenance vs new features

2. **Operating Cost Overruns**
   - **Risk:** Claude API, Google Maps API, or proxy costs exceed $90/month budget
   - **Mitigation:** Cost tracking, batch processing optimization, model selection (Haiku vs Sonnet), cache API responses
   - **Contingency:** Reduce batch size (20 properties instead of 50), manual analysis for some properties
   - **Monitoring:** Monthly cost reports per service

3. **Tool Abandonment Post-Purchase**
   - **Risk:** Andrew stops maintaining tool after buying house
   - **Mitigation:** Code archival, documentation for future reactivation, consider open-sourcing for community
   - **Contingency:** Accept tool as time-bound utility (Dec 2025 - Feb 2026), extract learnings into blog post
   - **Success metric:** Tool successfully supported home purchase decision with zero regrets

## Functional Requirements

These functional requirements define the complete capability inventory for PHX Houses Analysis Pipeline. Each requirement is testable, implementation-agnostic, and specifies WHO can do WHAT.

### Property Data Acquisition

**FR1:** [P0] User can initiate batch property analysis for multiple properties via CLI command

**FR2:** [P0] System can fetch authoritative property data from Maricopa County Assessor API (lot size, year built, garage spaces, pool, valuations)

**FR3:** [P0] System can extract listing data from Zillow and Redfin (price, HOA fee, images, listing descriptions, property features)

**FR4:** [P0] System can download and cache property images locally for analysis

**FR5:** [P0] System can extract geographic data from Google Maps API (geocoding, distances to points of interest, orientation determination)

**FR6:** [P0] System can fetch school ratings from GreatSchools API (elementary, middle, high school ratings within catchment area)

**FR7:** [P0] System can preserve raw property data separate from derived scores and analysis

**FR8:** [P0] System can track data provenance (source, confidence level, fetch timestamp) for every data field

### Kill-Switch Filtering

**FR9:** [P0] User can define HARD kill-switch criteria that result in instant property rejection

**FR10:** [P0] User can define SOFT kill-switch criteria with severity weights that accumulate toward threshold

**FR11:** [P0] System can evaluate properties against kill-switch criteria and return PASS/FAIL/WARNING verdicts

**FR12:** [P0] System can calculate severity scores for SOFT criteria violations and compare against configurable threshold

**FR13:** [P0] System can provide detailed explanations for kill-switch failures (which criteria failed, severity accumulation details)

**FR14:** [P0] User can update kill-switch criteria and thresholds via configuration files

### Property Scoring

**FR15:** [P0] System can calculate comprehensive property scores across three dimensions (Location, Systems, Interior)

**FR16:** [P0] System can apply 18+ scoring strategies with configurable weights for each dimension

**FR17:** [P0] System can classify properties into tiers based on total score (Unicorn, Contender, Pass)

**FR18:** [P0] System can generate score breakdowns showing point allocation across all scoring dimensions

**FR19:** [P1] User can adjust scoring weights via configuration files and trigger re-scoring without re-analysis

**FR20:** [P1] System can track score deltas when priorities change (show what changed and by how much)

### Risk Intelligence & Warnings

**FR21:** [P0] System can perform visual assessment of property images to estimate condition and identify potential issues

**FR22:** [P0] System can generate proactive warnings for hidden risks (foundation concerns, HVAC age, solar leases, orientation impacts)
- *Acceptance:* Warning precision ≥80% (≤20% false positive rate); each warning includes risk category, severity, evidence source, and recommended action; validated by post-inspection comparison on 5+ toured properties

**FR23:** [P1] System can map risks to tangible consequences ($cost, quality of life impact, resale impact)
- *Acceptance:* Cost estimates within ±30% of actual repair costs; each consequence includes min/max dollar range with Arizona-specific adjustments; validated by comparing to contractor quotes during due diligence

**FR24:** [P1] System can assign confidence levels to warnings based on data quality and source reliability
- *Acceptance:* Confidence calibration: High=90%+ accuracy (authoritative sources), Medium=70-90% (listing/visual), Low=<70% (inference); auto-downgrade when data >14 days old; validated by tracking confidence vs. inspection outcomes

**FR25:** [P0] System can apply Arizona-specific context to risk assessment (HVAC lifespan, pool costs, cooling impacts)
- *Acceptance:* AZ factors applied: HVAC lifespan 10-15 years, pool cost $250-400/month, west-facing penalty $100-200/month, north-facing 30 points; each factor documented with source; validated annually against current pricing

**FR26:** [P1] System can identify properties with potential foundation issues via visual crack pattern recognition
- *Acceptance:* Recall ≥90% (miss rate ≤10%), precision ≥60% (over-flagging acceptable); severity classification (Minor/Moderate/Severe) with crack type and image reference; validated by comparison to professional inspection reports

**FR27:** [P0] System can estimate HVAC replacement timeline based on system age and Arizona climate factors
- *Acceptance:* Timeline accuracy ±2 years; categories: Immediate (≥13 yrs), Near-term (10-12 yrs), Mid-term (5-9 yrs), Long-term (<5 yrs); includes replacement cost estimate ($7k-$12k); validated by comparing to confirmed system age during inspections

### Multi-Agent Pipeline Orchestration

**FR28:** [P0] User can execute the complete multi-phase analysis pipeline via single CLI command

**FR29:** [P0] System can coordinate sequential phase execution (Phase 0 → Phase 1 → Phase 2 → Phase 3)

**FR30:** [P0] System can spawn specialized agents for each phase with appropriate model selection (Haiku for data, Sonnet for vision)

**FR31:** [P0] System can validate phase prerequisites before spawning next agent (mandatory can_spawn checks)

**FR32:** [P0] System can execute Phase 1 sub-tasks in parallel (listing extraction + map analysis)

**FR33:** [P0] System can aggregate multi-agent outputs into unified property data records

### State Management & Reliability

**FR34:** [P0] System can checkpoint pipeline progress after each phase completion

**FR35:** [P0] System can resume interrupted pipeline execution from last successful checkpoint

**FR36:** [P0] System can detect and recover from transient errors (API rate limits, network issues) via retry logic

**FR37:** [P0] System can preserve previous state before risky operations (rollback capability)

**FR38:** [P0] User can validate pipeline state and data integrity via validation scripts

**FR39:** [P0] System can track which phase/agent populated each data field (lineage tracking)

### Analysis Outputs & Reports

**FR40:** [P0] System can generate comprehensive deal sheets for each analyzed property

**FR41:** [P0] Deal sheets can include property summary, score breakdown, tier classification, kill-switch verdict, and warnings

**FR42:** [P1] System can generate score explanation narratives describing WHY properties scored as they did

**FR43:** [P1] System can generate visual comparisons (radar charts, value spotter scatter plots) for property sets

**FR44:** [P1] System can produce risk checklists for property tours and inspections

**FR45:** [P1] User can regenerate deal sheets and visualizations after re-scoring without re-analysis

### Configuration & Extensibility

**FR46:** [P0] User can externalize scoring weights to YAML configuration files

**FR47:** [P0] User can externalize kill-switch criteria to CSV configuration files

**FR48:** [P1] User can define new scoring dimensions by adding strategies to configuration

**FR49:** [P1] User can add new kill-switch criteria without code changes

**FR50:** [P0] System can load configuration files at runtime and validate against schemas

**FR51:** [P0] User can maintain environment-specific configuration overrides (local vs production)

### CLI User Experience

**FR52:** [P0] User can execute manual phase-specific scripts for testing and debugging

**FR53:** [P0] User can pass flags to control pipeline behavior (--all, --test, --resume, --strict, --dry-run)

**FR54:** [P0] User can view structured console output with progress indicators during analysis

**FR55:** [P0] System can generate both human-readable logs and machine-parseable JSON outputs

**FR56:** [P0] User can access detailed error traces with actionable troubleshooting guidance when failures occur

**FR57:** [P0] User can query pipeline status and view pending tasks via status files

### Integration Management

**FR58:** [P0] System can authenticate with external APIs using environment-variable-based secrets

**FR59:** [P0] System can handle API rate limits gracefully with exponential backoff and retry logic

**FR60:** [P0] System can cache API responses to minimize costs and respect rate limits

**FR61:** [P0] System can rotate browser User-Agents and proxies to bypass anti-bot detection

**FR62:** [P0] System can fall back to alternative extraction methods when primary method fails (nodriver → Playwright)

## Non-Functional Requirements

These non-functional requirements specify quality attributes and constraints for PHX Houses Analysis Pipeline. Only categories relevant to this personal tool are included.

### Performance

**NFR1: Pipeline Throughput**
- Target: Complete batch analysis of 20 properties in ≤30 minutes
- Rationale: Enables single-session property evaluation without multi-hour blocking
- Measurement: Time from `/analyze-property --all` start to final deal sheet generation

**NFR2: Re-Scoring Speed**
- Target: Re-score 100+ properties in ≤5 minutes when weights change
- Rationale: Enables rapid priority adjustment without re-scraping expensive data
- Measurement: Time from config update to updated scores in enrichment_data.json

**NFR3: API Response Caching**
- Target: 90%+ cache hit rate for repeated API calls within 7-day window
- Rationale: Minimizes API costs and respects rate limits
- Measurement: Cache hits / total API calls ratio

**NFR4: Phase Prerequisite Validation**
- Target: Validation completes in ≤5 seconds
- Rationale: Fast can_spawn checks prevent long waits before discovering missing data
- Measurement: Execution time of `validate_phase_prerequisites.py` script

### Reliability

**NFR5: Kill-Switch Accuracy**
- Target: 100% accuracy - zero false passes on non-negotiable criteria
- Rationale: Hard kill-switch failures are absolute deal-breakers
- Measurement: Manual audit of kill-switch verdicts vs ground truth

**NFR6: Scoring Consistency**
- Target: ±5 points variance on re-run with identical data and weights
- Rationale: Deterministic, reproducible results build trust in the system
- Measurement: Score variance across 3 consecutive runs on same property

**NFR7: Crash Recovery Success Rate**
- Target: 95%+ successful resume after interruption
- Rationale: Pipeline interruptions shouldn't require full re-run
- Measurement: Successful --resume operations / total interruptions

**NFR8: Data Integrity Validation**
- Target: 100% of loaded JSON files pass Pydantic schema validation
- Rationale: Corrupt data breaks analysis and produces incorrect scores
- Measurement: Schema validation pass rate on data file loads

**NFR9: State Checkpoint Atomicity**
- Target: 100% of checkpoints are complete or absent (no partial writes)
- Rationale: Partial checkpoints corrupt recovery state
- Measurement: Checkpoint file integrity validation

### Maintainability

**NFR10: Configuration Externalization**
- Target: 100% of scoring weights and kill-switch criteria in config files (not hardcoded)
- Rationale: User must adjust criteria without code changes
- Measurement: Grep for hardcoded thresholds in src/ (zero occurrences)

**NFR11: Code Documentation Coverage**
- Target: 80%+ of functions have docstrings explaining purpose and parameters
- Rationale: Solo developer needs to understand code months later
- Measurement: Docstring coverage analysis via interrogate tool

**NFR12: Error Message Actionability**
- Target: 90%+ of errors include actionable troubleshooting guidance
- Rationale: Solo developer troubleshooting needs clear next steps
- Measurement: Manual audit of error messages for actionable guidance

**NFR13: Configuration Schema Validation**
- Target: 100% of config files validated against schemas at load time
- Rationale: Invalid config causes confusing runtime errors
- Measurement: Schema validation pass rate on config file loads

### Usability (CLI-Specific)

**NFR14: CLI Command Discoverability**
- Target: --help flag documents all commands and flags with examples
- Rationale: User shouldn't need to read source code to use CLI
- Measurement: Manual review of --help output completeness

**NFR15: Progress Visibility**
- Target: User sees progress updates at ≤30 second intervals during pipeline execution
- Rationale: Long-running operations need feedback to avoid "is it hung?" anxiety
- Measurement: Time between console log messages during execution

**NFR16: Error Message Clarity**
- Target: 90%+ of users understand error cause without reading source code
- Rationale: Solo developer doesn't always remember code context
- Measurement: Retrospective review of error resolution time

**NFR17: Output File Readability**
- Target: Deal sheets readable on mobile devices during property tours
- Rationale: User reviews deal sheets on phone during physical property visits
- Measurement: Manual review of deal sheet HTML rendering on mobile browsers

### Data Quality

**NFR18: Data Freshness**
- Target: Listing data ≤7 days old for active property search
- Rationale: Real estate market moves quickly; stale data causes missed opportunities
- Measurement: Timestamp delta between current date and listing data fetch date

**NFR19: Data Provenance Tracking**
- Target: 100% of data fields include source and confidence metadata
- Rationale: User needs to assess data reliability for decision-making
- Measurement: Audit of enrichment_data.json for missing provenance fields

**NFR20: Confidence Level Calibration**
- Target: High confidence = 90%+ accuracy, Medium = 70-90%, Low = <70%
- Rationale: Confidence levels guide user trust in warnings and scores
- Measurement: Post-inspection validation of confidence vs ground truth

**NFR21: Arizona Context Accuracy**
- Target: AZ-specific factors (HVAC lifespan, pool costs) validated annually
- Rationale: Local market dynamics shift over time
- Measurement: Annual review against current market data

### Cost Efficiency

**NFR22: Monthly Operating Cost**
- Target: ≤$90/month for 100 properties analyzed (Claude API + Google Maps + proxies)
- Rationale: Personal tool must remain affordable for solo user
- Measurement: Monthly invoice totals from all service providers

**NFR23: Model Selection Optimization**
- Target: Haiku used for 80%+ of agent tasks, Sonnet only for vision
- Rationale: Haiku is 10x cheaper than Sonnet for data extraction tasks
- Measurement: Agent spawn logs showing model selection distribution

**NFR24: Image Analysis Cost**
- Target: ≤$0.02 per image for visual assessment
- Rationale: Properties have 10-30 images; high per-image cost is prohibitive
- Measurement: Claude API costs / total images analyzed

### Security

**NFR25: Secrets Management**
- Target: 100% of API tokens stored in .env file (gitignored), never hardcoded
- Rationale: Accidental git commit of secrets exposes accounts
- Measurement: Grep for API tokens in git-tracked files (zero occurrences)

**NFR26: Data Privacy**
- Target: No personally identifiable information (PII) logged to files
- Rationale: Logs may be shared for debugging; PII exposure is unacceptable
- Measurement: Manual audit of log files for PII

**NFR27: Dependency Vulnerability Scanning**
- Target: Zero high or critical vulnerabilities in production dependencies
- Rationale: Vulnerable dependencies create security risks
- Measurement: pip-audit scan results

### Compatibility

**NFR28: Python Version Support**
- Target: Python 3.12+ required (no backward compatibility to 3.10 or earlier)
- Rationale: Modern Python features reduce code complexity
- Measurement: Python version check at startup

**NFR29: Operating System Support**
- Target: Works on macOS and Linux (Windows support nice-to-have)
- Rationale: Developer uses macOS; Linux for potential cloud deployment
- Measurement: Manual testing on target platforms

**NFR30: Browser Automation Compatibility**
- Target: nodriver (stealth) and Playwright (fallback) both operational
- Rationale: Anti-bot detection evolves; need multiple extraction strategies
- Measurement: Successful extraction runs with both methods

