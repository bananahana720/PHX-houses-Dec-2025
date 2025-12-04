# 1. Executive Summary

### 1.1 What Changes Are Recommended

This specification proposes targeted updates to the PHX Houses Analysis Pipeline scoring system based on comprehensive research across 9 research reports covering market conditions, domain expertise, and technical capabilities.

**Kill-Switch Updates:**
1. **ADD: Solar Lease criterion (SOFT, severity 2.5)** - Properties with leased solar systems face 3-8% value reduction and transfer complications

**Scoring Weight Updates:**
1. **ADD: HVAC Condition (25 pts)** to Section B - Arizona's extreme heat reduces HVAC lifespan to 8-15 years
2. **REBALANCE: Section A** - Reduce by 25 pts across lower-priority criteria to accommodate HVAC
3. **ADJUST: Roof scoring thresholds** - Align with Arizona-specific lifespan research
4. **ADJUST: Pool equipment age thresholds** - Match Arizona equipment degradation patterns

### 1.2 Impact on Score Distribution

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Section A Max | 250 pts | 225 pts | -25 |
| Section B Max | 170 pts | 195 pts | +25 |
| Section C Max | 180 pts | 180 pts | 0 |
| **Total Max** | **600 pts** | **600 pts** | **0** |

**Expected Tier Distribution Impact:**
- Properties with aging HVAC (10-15 years) will score lower in Section B
- Properties with leased solar will face kill-switch severity or outright failure
- Net effect: More accurate risk assessment for first-time buyers

### 1.3 Rationale Summary

| Change | Research Source | Key Finding |
|--------|-----------------|-------------|
| Solar Lease kill-switch | Market-Beta, Domain-Beta | 75% of Phoenix solar is leased; 3-8% value reduction; transfer complications |
| HVAC scoring | Domain-Alpha | AZ HVAC lifespan 8-15 years (not 20+); $11k-26k replacement |
| Roof threshold adjustment | Domain-Alpha | AZ underlayment 12-20 years; shingles 12-25 years |
| Pool equipment thresholds | Market-Beta, Domain-Alpha | AZ heat reduces pool pump life to 8-12 years |

---
