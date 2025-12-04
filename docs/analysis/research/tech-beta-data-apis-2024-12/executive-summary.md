# Executive Summary

This report evaluates third-party APIs for integration into the PHX Houses Analysis Pipeline across three critical domains: crime data, walkability scores, and residential energy usage estimation.

### Key Findings

| Domain | Best Option | Cost | Data Granularity | Confidence |
|--------|-------------|------|------------------|------------|
| Crime Data | Phoenix Open Data + FBI CDE | Free | Address/Zip | High |
| WalkScore | WalkScore API | Free tier (5K/day) | Address | High |
| Energy Estimation | EIA API + BEopt | Free | Home characteristics | Medium |

### Recommendations for PHX Houses Pipeline

1. **Crime Data**: Use Phoenix Open Data Portal (free, address-level) as primary source, FBI Crime Data Explorer as supplemental
2. **WalkScore**: Integrate WalkScore API free tier for initial deployment; evaluate Professional tier if volume exceeds 5K/day
3. **Energy**: Combine EIA statistical data with BEopt/NREL ResStock for Phoenix-specific estimations

---
