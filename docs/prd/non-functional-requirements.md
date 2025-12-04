# Non-Functional Requirements

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

