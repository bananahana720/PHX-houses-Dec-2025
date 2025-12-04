# Recommendations for PHX Houses System

### Immediate Implementation

1. **Add Septic System SOFT Kill-Switch**
   - Severity: 2.5
   - Detection: Query Maricopa County septic database
   - Rationale: 10%+ failure rate, $4k-$20k replacement risk, annual maintenance burden

2. **Add Water Service Verification**
   - Check: Is property within DAWS service area?
   - If Yes: PASS
   - If No: WARNING (note in report, not kill-switch)

3. **Integrate Zoning GIS Lookup**
   - Use Assessor API for lot size verification
   - Cross-reference with kill-switch lot criteria (7k-15k sqft)
   - Flag Rural-43+ zoning as "large lot" category

### Future Enhancements

4. **Track Water Provider Changes**
   - Monitor ADAWS designations for newly covered areas
   - Update service area maps quarterly

5. **Septic Age Estimation**
   - Query permit database for system installation date
   - Flag systems 20+ years old as higher risk

6. **Zoning Change Monitoring**
   - Track HB2721 implementation (missing middle housing)
   - Note properties near downtown that may benefit from density changes

---

*Report generated: December 2024*
*For: PHX Houses Analysis Pipeline*
*Research Agent: Domain-Gamma*
