# Integration Recommendations for PHX Houses Pipeline

### Phase 1: Immediate Integration (Low Cost)

1. **Crime Data:**
   - Primary: Phoenix Open Data Portal (free, daily updates)
   - Supplemental: FBI Crime Data Explorer (free, quarterly)
   - Implementation: Add to Phase 1 map-analyzer agent

2. **WalkScore:**
   - Use free tier (5,000 calls/day)
   - Store scores in enrichment_data.json
   - Add to Section A (Location) scoring

3. **Energy Estimation:**
   - Use EIA statistical data + square footage formula
   - Integrate ResStock Arizona data for climate-adjusted estimates

### Phase 2: Enhanced Integration (Budget Required)

1. **Crime Data:**
   - Evaluate CrimeOMeter Pro ($30/month) for address-level granularity
   - Consider NeighborhoodScout ($5K/year) for comprehensive risk scores

2. **WalkScore:**
   - Upgrade to Professional for Transit/Travel Time APIs
   - Enables commute time calculations

3. **Energy Estimation:**
   - Evaluate UtilityAPI for APS actual bill access
   - Consider Arcadia for multi-utility coverage

### Implementation Priority

| Priority | API | Estimated Effort | Value |
|----------|-----|------------------|-------|
| High | Phoenix Open Data | 2-4 hours | High |
| High | WalkScore Free | 2-4 hours | High |
| Medium | FBI CDE | 4-8 hours | Medium |
| Medium | EIA + ResStock | 8-16 hours | Medium |
| Low | CrimeOMeter | 4-8 hours | Medium |
| Low | UtilityAPI | 8-16 hours | Low |

### Proposed Schema Additions

```python
# enrichment_data.json additions
{
    "crime_data": {
        "source": "phoenix_open_data",
        "incidents_1yr_radius_0.5mi": 42,
        "violent_crime_rate": 4.2,
        "property_crime_rate": 18.7,
        "last_updated": "2024-12-03"
    },
    "walkability": {
        "walk_score": 65,
        "transit_score": 38,
        "bike_score": 52,
        "walk_description": "Somewhat Walkable",
        "source": "walkscore_api"
    },
    "energy_estimate": {
        "estimated_monthly_kwh": 1340,
        "estimated_monthly_cost": 174.20,
        "methodology": "eia_regional_sqft",
        "confidence": "medium"
    }
}
```

---
