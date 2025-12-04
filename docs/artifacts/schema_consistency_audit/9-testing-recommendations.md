# 9. TESTING RECOMMENDATIONS

1. **Add Schema Validation Tests**
   - Test that JSON validates against EnrichmentDataSchema
   - Test that CSV parses to PropertySchema
   - Test that Property entity can serialize to both schemas

2. **Add Integration Tests**
   - Test Property ← CSV + JSON merge
   - Test all scorers with real data
   - Test kill-switch with edge cases

3. **Add Type Safety Tests**
   - Verify `tax_annual` handles float values
   - Verify `solar_lease_monthly` handles fractional costs
   - Verify `baths` 0.5 increments

---
