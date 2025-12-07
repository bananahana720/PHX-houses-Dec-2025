---
last_updated: 2025-12-07T22:37:45Z
updated_by: agent
staleness_hours: 24
flags: []
---
# prd

## Purpose
Product requirements document defining vision, scope, success criteria, and functional requirements for PHX Houses Analysis Pipeline decision support system.

## Contents
| Path | Purpose |
|------|---------|
| `index.md` | Table of contents |
| `executive-summary.md` | Vision, problem statement, solution approach |
| `product-scope.md` | MVP vs growth vs future features |
| `success-criteria.md` | Measurable acceptance criteria |
| `functional-requirements.md` | Feature-level requirements |
| `non-functional-requirements.md` | Performance, security, reliability |
| `user-journeys.md` | End-to-end workflows |
| `innovation-novel-patterns.md` | Unique approach vs competitors |
| `data-input-costs.md` | API cost analysis |
| `implementation-status.md` | Current implementation state |

## Key Patterns
- **Risk-first approach**: "Asymmetric risk exposure" framing (100% financial risk, 20% decision factors)
- **Arizona-specific context**: HVAC 20-40% faster failure, pool $300-400/mo, solar lease liability
- **Proactive intelligence**: Surface unknown unknowns before emotional investment
- **MVP kill-switch updates**: HOA=$0, solar≠lease, beds≥4, baths≥2, sqft>1800

## Tasks
- [ ] Update kill-switch criteria in product-scope.md to match current implementation `P:H`
- [ ] Sync implementation-status.md with Epic 1+2 completion `P:M`
- [ ] Add PhoenixMLS Search to data-input-costs.md `P:L`

## Learnings
- **Emotional payoff critical**: "NOW I understand", "This is THE one", "Bullet dodged" moments drive UX
- **Confidence levels matter**: Medium/High annotations help users trust warnings
- **Raw data preservation**: Re-scoring flexibility requires keeping all source data
- **Phased development**: Wave 0-6 structure enables incremental delivery

## Refs
- Implementation status: `../sprint-artifacts/sprint-status.yaml`
- Kill-switch logic: `../../src/phx_home_analysis/services/kill_switch/`
- Scoring weights: `../../src/phx_home_analysis/config/constants.py`

## Deps
← imports: none (requirements source)
→ used by: `../specs/`, `../sprint-artifacts/stories/`, agents
