# User Journeys

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
