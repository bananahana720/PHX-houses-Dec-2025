# FR Coverage Matrix

| FR ID | Description | Priority | Epic | Story | Status |
|-------|-------------|----------|------|-------|--------|
| FR1 | Batch property analysis via CLI command | P0 | E2 | E2.S1 | Ready |
| FR2 | Maricopa County Assessor API integration | P0 | E2 | E2.S2 | Ready |
| FR3 | Zillow/Redfin listing extraction | P0 | E2 | E2.S3 | Ready |
| FR4 | Property image download and caching | P0 | E2 | E2.S4 | Ready |
| FR5 | Google Maps API geographic data | P0 | E2 | E2.S5 | Ready |
| FR6 | GreatSchools API school ratings | P0 | E2 | E2.S6 | Ready |
| FR7 | Raw data preservation separate from scores | P0 | E1 | E1.S2 | Ready |
| FR8 | Data provenance tracking (source, confidence, timestamp) | P0 | E1 | E1.S3 | Ready |
| FR9 | HARD kill-switch criteria (instant rejection) | P0 | E3 | E3.S1 | Ready |
| FR10 | SOFT kill-switch criteria with severity weights | P0 | E3 | E3.S2 | Ready |
| FR11 | Kill-switch verdict evaluation (PASS/FAIL/WARNING) | P0 | E3 | E3.S3 | Ready |
| FR12 | Severity score calculation for SOFT criteria | P0 | E3 | E3.S2 | Ready |
| FR13 | Kill-switch failure explanations | P0 | E3 | E3.S4 | Ready |
| FR14 | Kill-switch criteria configuration updates | P0 | E3 | E3.S5 | Ready |
| FR15 | Three-dimension property scoring (Location, Systems, Interior) | P0 | E4 | E4.S1 | Ready |
| FR16 | 18+ scoring strategies with configurable weights | P0 | E4 | E4.S2 | Ready |
| FR17 | Tier classification (Unicorn, Contender, Pass) | P0 | E4 | E4.S3 | Ready |
| FR18 | Score breakdown generation by dimension | P0 | E4 | E4.S4 | Ready |
| FR19 | Scoring weight adjustment and re-scoring without re-analysis | P1 | E4 | E4.S5 | Ready |
| FR20 | Score delta tracking when priorities change | P1 | E4 | E4.S6 | Ready |
| FR21 | Visual assessment of property images | P0 | E6 | E6.S1 | Ready |
| FR22 | Proactive warnings for hidden risks (foundation, HVAC, solar) | P0 | E6 | E6.S2 | Ready |
| FR23 | Risk-to-consequence mapping (costs, QoL, resale impacts) | P1 | E6 | E6.S3 | Ready |
| FR24 | Warning confidence levels (High/Medium/Low) | P1 | E6 | E6.S4 | Ready |
| FR25 | Arizona-specific context for risk assessment | P0 | E4 | E4.S2 | Ready |
| FR26 | Foundation issue identification via visual analysis | P1 | E6 | E6.S5 | Ready |
| FR27 | HVAC replacement timeline estimation | P0 | E6 | E6.S6 | Ready |
| FR28 | Single CLI command for complete multi-phase analysis | P0 | E5 | E5.S1 | Ready |
| FR29 | Sequential phase coordination (0→1→2→3→4) | P0 | E5 | E5.S2 | Ready |
| FR30 | Agent spawning with appropriate model selection | P0 | E5 | E5.S3 | Ready |
| FR31 | Phase prerequisite validation before spawning | P0 | E5 | E5.S4 | Ready |
| FR32 | Parallel Phase 1 execution (listing + map analysis) | P0 | E5 | E5.S5 | Ready |
| FR33 | Multi-agent output aggregation into unified records | P0 | E5 | E5.S6 | Ready |
| FR34 | Pipeline checkpointing after each phase | P0 | E1 | E1.S4 | Ready |
| FR35 | Resume interrupted pipeline from last checkpoint | P0 | E1 | E1.S5 | Ready |
| FR36 | Transient error recovery with exponential backoff | P0 | E1 | E1.S6 | Ready |
| FR37 | State preservation before risky operations | P0 | E1 | E1.S4 | Ready |
| FR38 | Pipeline state and data integrity validation | P0 | E1 | E1.S5 | Ready |
| FR39 | Data lineage tracking (which phase/agent populated data) | P0 | E1 | E1.S3 | Ready |
| FR40 | Comprehensive deal sheet generation | P0 | E7 | E7.S1 | Ready |
| FR41 | Deal sheet content (summary, scores, tier, verdict, warnings) | P0 | E7 | E7.S2 | Ready |
| FR42 | Score explanation narratives (natural language "WHY") | P1 | E7 | E7.S3 | Ready |
| FR43 | Visual comparisons (radar charts, scatter plots) | P1 | E7 | E7.S4 | Ready |
| FR44 | Risk checklists for property tours | P1 | E7 | E7.S5 | Ready |
| FR45 | Deal sheet regeneration after re-scoring | P1 | E7 | E7.S6 | Ready |
| FR46 | YAML scoring weight externalization | P0 | E1 | E1.S1 | Ready |
| FR47 | CSV kill-switch criteria externalization | P0 | E1 | E1.S1 | Ready |
| FR48 | New scoring dimension definition without code changes | P1 | E4 | E4.S2 | Ready |
| FR49 | New kill-switch criteria without code changes | P1 | E3 | E3.S5 | Ready |
| FR50 | Configuration loading and runtime validation | P0 | E1 | E1.S1 | Ready |
| FR51 | Environment-specific configuration overrides | P0 | E1 | E1.S1 | Ready |
| FR52 | Manual phase-specific script execution | P0 | E7 | E7.S1 | Ready |
| FR53 | Pipeline behavior flags (--all, --test, --resume, --strict) | P0 | E5 | E5.S1 | Ready |
| FR54 | Structured console output with progress indicators | P0 | E7 | E7.S1 | Ready |
| FR55 | Human-readable logs and machine-parseable JSON output | P0 | E7 | E7.S1 | Ready |
| FR56 | Error traces with actionable troubleshooting guidance | P0 | E1 | E1.S6 | Ready |
| FR57 | Pipeline status query and pending tasks view | P0 | E5 | E5.S1 | Ready |
| FR58 | API authentication via environment secrets | P0 | E2 | E2.S7 | Ready |
| FR59 | API rate limit handling with exponential backoff | P0 | E2 | E2.S7 | Ready |
| FR60 | API response caching to minimize costs | P0 | E2 | E2.S7 | Ready |
| FR61 | Browser User-Agent and proxy rotation | P0 | E2 | E2.S3 | Ready |
| FR62 | Alternative extraction method fallback (nodriver→curl-cffi→Playwright) | P0 | E2 | E2.S3 | Ready |

**Matrix Statistics:**
- **Total FRs:** 62
- **Mapped FRs:** 62
- **Coverage:** 100%
- **P0 FRs:** 51
- **P1 FRs:** 11

---
