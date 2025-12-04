# Section 6: Technical Debt Assessment

### Debt 1: No Job Queue (IP-01-05 cluster)
**Current Cost**: 30 min per 8 properties = 375 min per 100 properties = Can't handle production volume
**Interest (per month)**: Blocks scaling; users wait 6+ hours for full batch
**Payoff Timeline**: 5 days to design/build; worth it after property #15
**Should Fix**: YES (blocks production use)

### Debt 2: Scoring Black Box (XT-09 cluster)
**Current Cost**: Low - system works correctly, just not understandable
**Interest (per month)**: UX complaints; distrust of system
**Payoff Timeline**: 3 days to implement reasoning; high user value
**Should Fix**: YES (UX blocker)

### Debt 3: Hard-Coded Configuration (XT-05-08 cluster)
**Current Cost**: Medium - requires code change + redeploy for any adjustment
**Interest (per month)**: Blocks A/B testing buyer profiles
**Payoff Timeline**: 4 days to externalize; enables future testing
**Should Fix**: MAYBE (nice-to-have, not blocking)

### Debt 4: No Data Lineage (XT-01-04 cluster)
**Current Cost**: Medium - can't audit data quality, can't debug enrichment issues
**Interest (per month)**: Data quality erosion; trust issues
**Payoff Timeline**: 4 days to implement; prevents future data corruption
**Should Fix**: YES (compliance/audit gap)

### Debt 5: Foundation Assessment Missing (VB-03)
**Current Cost**: High - missing critical decision factor
**Interest (per month)**: Bad property selections; structural problems discovered late
**Payoff Timeline**: 5 days to build assessment service
**Should Fix**: YES (business logic gap)

---
