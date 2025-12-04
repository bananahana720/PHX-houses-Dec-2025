# 10. Implementation Checklist

```markdown
## Kill-Switch Updates
- [ ] Add SEVERITY_WEIGHT_SOLAR_LEASE = 2.5 to constants.py
- [ ] Implement SolarLeaseCriterion class
- [ ] Add solar_status to SOFT_SEVERITY_WEIGHTS
- [ ] Update evaluate_kill_switches() to include solar lease
- [ ] Add solar lease detection patterns to listing extraction
- [ ] Write unit tests for solar lease criterion
- [ ] Update kill-switch skill documentation

## Scoring Updates
- [ ] Add HVAC age constants to constants.py
- [ ] Implement HvacConditionScorer class
- [ ] Update ScoringWeights dataclass with hvac_condition
- [ ] Update Section A weights (reduce by 25 pts)
- [ ] Update Section B weights (add hvac_condition)
- [ ] Adjust roof age thresholds for Arizona
- [ ] Adjust pool equipment thresholds for Arizona
- [ ] Add HVAC to PropertyScorer orchestration
- [ ] Write unit tests for HVAC scorer
- [ ] Update scoring skill documentation

## Schema Updates
- [ ] Add solar_status field to enrichment schema
- [ ] Add hvac_age field to enrichment schema
- [ ] Add hvac_install_year field to enrichment schema
- [ ] Add hvac_condition field to enrichment schema
- [ ] Update property-data skill with new fields
- [ ] Update validation schemas

## Cost Estimation Updates
- [ ] Add solar lease to monthly cost calculation
- [ ] Update cost-efficiency skill documentation

## Testing
- [ ] Run full test suite
- [ ] Test kill-switch combinations with solar lease
- [ ] Test HVAC scoring at boundary conditions
- [ ] Validate 600-point total maintained
- [ ] Re-score sample properties for comparison
- [ ] Document tier distribution changes

## Documentation
- [ ] Update CLAUDE.md scoring section
- [ ] Update scoring skill SKILL.md
- [ ] Update kill-switch skill SKILL.md
- [ ] Update AGENT_BRIEFING.md if needed
- [ ] Add migration notes to CHANGELOG
```

---

**Document Version:** 2.0.0
**Last Updated:** December 2024
**Status:** Ready for Implementation Review
**Estimated Implementation Effort:** 16-24 hours
**Risk Level:** Low (additive changes with backwards compatibility)
