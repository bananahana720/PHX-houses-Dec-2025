---
last_updated: 2025-12-10
updated_by: agent
staleness_hours: 24
---
# config

## Purpose
Configuration files for PHX Houses Analysis Pipeline: kill-switch criteria, buyer preferences, scoring weights, and web scraping resources.

## Contents
| Path | Purpose |
|------|---------|
| `kill_switch.csv` | Kill-switch criteria: 5 HARD + 4 SOFT with severity weights (E3.S2) |
| `buyer_criteria.yaml` | Buyer hard requirements (legacy: all 8 as HARD) |
| `scoring_weights.yaml` | 605-point scoring weights by category |
| `proxies.txt` | Proxy server list for web scraping |
| `user_agents.txt` | User agent rotation pool |
| `README.md` | Configuration documentation |

## Key Schema (kill_switch.csv)
| Column | Values | Description |
|--------|--------|-------------|
| `name` | snake_case | Unique criterion ID |
| `type` | HARD/SOFT | Instant fail vs severity accumulation |
| `operator` | ==, !=, >, <, >=, <=, range | Comparison type |
| `threshold` | varies | Value to compare against |
| `severity` | 0.0-10.0 | Weight when failed (0 for HARD) |

## Severity Thresholds
- FAIL: severity >= 3.0
- WARNING: severity >= 1.5
- PASS: severity < 1.5

## Tasks
- [x] Create kill_switch.csv with HARD/SOFT criteria `P:H`
- [ ] Wire CSV loading to production code (currently dead code) `P:H`
- [ ] Add hot-reload for config changes `P:M`

## Learnings
- **HARD criteria**: no_hoa, no_solar_lease, min_bedrooms, min_bathrooms, min_sqft
- **SOFT criteria**: city_sewer (2.5), no_new_build (2.0), min_garage (1.5), lot_size (1.0)
- **buyer_criteria.yaml**: Legacy format (all HARD), superseded by kill_switch.csv

## Refs
- CSV loader: `src/phx_home_analysis/services/kill_switch/severity.py:318-397`
- Constants: `src/phx_home_analysis/config/constants.py`
- Story: `docs/sprint-artifacts/stories/E3-S2-soft-kill-switch-severity-system.md`

## Deps
<- imports: none (configuration source)
-> used by: KillSwitchFilter, SoftSeverityEvaluator, scoring pipeline
