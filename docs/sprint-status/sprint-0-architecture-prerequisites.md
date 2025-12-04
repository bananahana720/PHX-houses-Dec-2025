# Sprint 0: Architecture Prerequisites

> **Objective**: Address architectural action items before story implementation
> **Stories**: 5 prerequisite tasks
> **Outcome**: Codebase aligned with PRD and Architecture specifications
> **Status**: ✅ **COMPLETED** (2025-12-04)

### ARCH Action Items

| ID | Task | Priority | Status |
|----|------|----------|--------|
| ARCH-05 | Update `constants.py` to 605-point scoring (250+175+180) | HIGH | `[x]` ✅ |
| ARCH-04 | Implement `SqftKillSwitch` (>1800 sqft HARD criterion) | HIGH | `[x]` ✅ |
| ARCH-03 | Fix `LotSizeKillSwitch` - change from range (7k-15k) to minimum (>8000) | MEDIUM | `[x]` ✅ |
| ARCH-02 | Update `SewerKillSwitch` - change from SOFT to HARD | MEDIUM | `[x]` ✅ |
| ARCH-01 | Clarify `GarageKillSwitch` as indoor garage required | MEDIUM | `[x]` ✅ |

### Sprint 0 Acceptance Criteria

- [x] `constants.py` defines: `MAX_POSSIBLE_SCORE=605`, `TIER_UNICORN_MIN=484`, `TIER_CONTENDER_MIN=363`
- [x] All 7 kill-switch criteria are HARD (instant fail)
- [x] Kill-switch criteria match PRD: HOA=$0, Beds>=4, Baths>=2, Sqft>1800, Lot>8000, Garage>=1 indoor, Sewer=city
- [x] Unit tests pass for updated constants and kill-switches

---
