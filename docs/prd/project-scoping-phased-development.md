# Project Scoping & Phased Development

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
