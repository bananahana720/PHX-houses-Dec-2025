---
last_updated: 2025-12-05
updated_by: agent
staleness_hours: 24
---
# tests/unit/services/scoring

## Purpose
Unit tests for scoring explanation module covering score explanation dataclasses, section breakdowns, tier classifications, and markdown report generation. Validates human-readable scoring explanations with criterion-level detail.

## Contents
| File | Purpose |
|------|---------|
| `test_explanation.py` | ScoreExplanation, SectionExplanation, FullScoreExplanation, ScoringExplainer classes (25+ test classes, 150+ tests) |
| `__init__.py` | Package initialization |

## Key Patterns
- **Dataclass testing**: ScoreExplanation, SectionExplanation, FullScoreExplanation structs with to_dict/to_text serialization
- **Tier-aware explanations**: Generate summaries, strengths, improvements per tier (Unicorn/Contender/Pass)
- **Percentage boundaries**: Score classification logic (70%+ high, 40-70% medium, <40% low)
- **Markdown generation**: to_text() generates formatted explanations with tables, headers, improvement tips

## Tasks
- [x] Map test coverage for explanation classes `P:H`
- [x] Document test patterns (dataclass creation, serialization, tier logic) `P:H`
- [ ] Add edge case tests for missing property fields `P:M`
- [ ] Add explanation caching tests `P:L`

## Learnings
- **Improvement tips conditional**: Low-scoring criteria (<40%) include improvement_tip, high-scoring criteria don't
- **Tier thresholds**: Unicorn >480 (next_tier=None), Contender 360-480 (next_tier=Unicorn), Pass <360 (next_tier=Contender)
- **Criterion templates**: CRITERION_TEMPLATES dict (50+ criteria) provides reasoning/improvement patterns per criterion
- **Floating-point rounding**: to_dict() rounds scores/percentages to 1 decimal place for JSON serialization

## Refs
- Explanation classes: `test_explanation.py:1-100` (dataclass definitions)
- ScoringExplainer: `test_explanation.py:483-1076` (explain(), section logic, raw value extraction)
- Tier determination: `test_explanation.py:702-760` (tier thresholds, boundary testing)
- Criterion templates: `src/phx_home_analysis/services/scoring/explanation.py`

## Deps
← imports: ScoringWeights, TierThresholds, Property, enums (Orientation, FloodZone, SolarStatus, SewerType)
→ used by: pytest, CI/CD pipeline (must pass before merge)
