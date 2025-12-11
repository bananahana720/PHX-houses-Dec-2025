---
last_updated: 2025-12-10
updated_by: agent
---

# tests/unit/services/scoring

## Purpose
Unit tests for scoring explanation module covering score explanations, section breakdowns, tier classifications, and markdown report generation. Validates human-readable scoring rationale with criterion-level detail.

## Contents
| File | Purpose |
|------|---------|
| `test_explanation.py` | ScoreExplanation, SectionExplanation, FullScoreExplanation dataclasses (150+ tests, 25+ test classes) |
| `conftest.py` | Scoring-specific fixtures (PropertyDataBuilder, tier-specific properties) |
| `__init__.py` | Package initialization |

## Key Test Classes (test_explanation.py)
| Class | Coverage |
|-------|----------|
| TestScoreExplanation | Score dataclass creation, serialization (to_dict, to_text) |
| TestSectionExplanation | Section breakdown aggregation (Location/Systems/Interior) |
| TestFullScoreExplanation | Tier-aware summary generation, improvement recommendations |
| TestScoringExplainer | Main explanation engine (explain method, criterion reasoning) |
| TestTierClassification | Tier determination (Unicorn >=484, Contender 360-483, Pass <360) |

## Key Patterns
- **Dataclass serialization**: to_dict() returns JSON-compatible output, to_text() generates markdown
- **Tier-aware explanations**: Conditional tips for low-scoring criteria (<40%)
- **Percentage boundaries**: Score classification (70%+ high, 40-70% medium, <40% low)
- **Criterion templates**: 50+ template patterns provide reasoning and improvement suggestions
- **Floating-point rounding**: 1 decimal place for JSON serialization

## Tasks
- [x] Map test coverage for explanation classes `P:H`
- [x] Document test patterns `P:H`
- [ ] Add edge case tests for missing fields `P:M`
- [ ] Add explanation caching tests `P:L`

## Refs
- Explanation classes: `test_explanation.py:1-100` (dataclass defs)
- ScoringExplainer: `test_explanation.py:483-1076` (main logic)
- Tier thresholds: `test_explanation.py:702-760` (boundary testing)
- Criterion templates: `../../explanation.py` (50+ patterns)

## Deps
← imports: ScoringWeights, TierThresholds, Property, enums
→ used by: pytest, CI/CD pipeline (must pass before merge)
