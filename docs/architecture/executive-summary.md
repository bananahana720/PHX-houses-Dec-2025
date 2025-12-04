# Executive Summary

### Purpose

This document defines the complete technical architecture for the PHX Houses Analysis Pipeline - a personal decision support system that evaluates Phoenix-area residential properties against strict first-time homebuyer criteria through multi-agent analysis, kill-switch filtering, and comprehensive scoring.

### Key Architectural Goals

1. **Eliminate Decision Anxiety**: Transform 50+ weekly listings into 3-5 tour-worthy candidates through systematic filtering
2. **Ensure Zero False Passes**: 100% accuracy on kill-switch criteria - no deal-breaker properties slip through
3. **Enable Transparent Scoring**: Every point traceable to source data and calculation logic
4. **Support Crash Recovery**: Resume interrupted pipelines without re-running completed work
5. **Optimize for Cost Efficiency**: Haiku for data extraction, Sonnet only for vision tasks

### Critical Architecture Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Architecture Style | Domain-Driven Design (DDD) | Clean separation, testable business logic |
| Data Storage | JSON files (LIST-based) | Simple, crash-recoverable, adequate for <1000 properties |
| Scoring System | 605-point weighted system | Matches actual ScoringWeights dataclass calculations |
| Kill-Switch System | All HARD criteria per PRD | HOA, beds, baths, sqft, lot, garage, sewer |
| Multi-Agent Model | Haiku (extraction) + Sonnet (vision) | Cost optimization with capability matching |
| Browser Automation | nodriver (stealth) primary | PerimeterX bypass for Zillow/Redfin |

### Architecture Gap Resolutions

| Gap ID | Issue | Resolution |
|--------|-------|------------|
| ARCH-01 | Kill-switch criteria mismatch | All 7 criteria now HARD per PRD FR9-FR14 |
| ARCH-02 | Scoring totals inconsistent | Reconciled to 605 pts (ScoringWeights authoritative) |
| ARCH-03 | Tier thresholds misaligned | Updated to 484 (80%), 363 (60%) of 605 |

---
