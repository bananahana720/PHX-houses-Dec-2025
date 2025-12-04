# 5. Kill-Switch Criteria Validation

### Current Criteria Assessment

| Criterion | Type | Current Setting | Research Finding | Recommendation |
|-----------|------|-----------------|------------------|----------------|
| **HOA** | HARD | $0 required | 70% buyer preference, $448 avg, adequate non-HOA inventory | **MAINTAIN** |
| **Bedrooms** | HARD | 4+ required | 32% market share, multigenerational trend supports | **MAINTAIN** |
| **Bathrooms** | HARD | 2+ required | Standard requirement, 2.32 avg in Phoenix | **MAINTAIN** |
| **Sewer** | SOFT | City preferred | 10%+ septic failure rate, $6k-50k replacement | **MAINTAIN** (severity 2.5) |
| **Year Built** | SOFT | <2024 preferred | Strong implied warranty protection (Zambrano ruling) | **MAINTAIN** (severity 2.0) |
| **Garage** | SOFT | 2+ spaces | Standard for Arizona market | **MAINTAIN** (severity 1.5) |
| **Lot Size** | SOFT | 7k-15k sqft | Zoning research confirms appropriate range | **MAINTAIN** (severity 1.0) |

### Recommended NEW Kill-Switch Criteria

**1. Solar Lease - HARD Kill-Switch**

| Attribute | Value |
|-----------|-------|
| Type | HARD |
| Condition | Solar lease or PPA present |
| Rationale | 3-8% home value reduction, transfer complications, 100+ bankruptcies |
| Implementation | Check listing data, county records, seller disclosure |

**2. Flood Zone (SFHA) - HARD Kill-Switch**

| Attribute | Value |
|-----------|-------|
| Type | HARD |
| Condition | FEMA zones A, AE, AH, AO, VE (SFHA_TF = True) |
| Rationale | Mandatory flood insurance ($1,500-3,000/year), resale limitations |
| Implementation | FEMA NFHL API query by coordinates |

**3. Water Service Area - SOFT Kill-Switch (NEW)**

| Attribute | Value |
|-----------|-------|
| Type | SOFT |
| Severity | 2.0 |
| Condition | Property outside DAWS service area |
| Rationale | 2023 groundwater moratorium, development restrictions, long-term value risk |
| Implementation | Verify against ADWR designated provider list |

**4. Septic System Age - SOFT Kill-Switch Enhancement**

| Attribute | Value |
|-----------|-------|
| Type | SOFT |
| Severity | 2.5 (base) + 1.0 (if >20 years old) |
| Condition | Septic system present (verified via county database) |
| Rationale | 10%+ failure rate, $6k-50k replacement, mandatory pre-sale inspection |
| Implementation | Query Maricopa County septic database |

### Updated Kill-Switch Summary Table

| Type | Criterion | Requirement | Severity | Source |
|------|-----------|-------------|----------|--------|
| **HARD** | HOA | Must be $0 | Instant fail | Market-Alpha |
| **HARD** | Bedrooms | Must be 4+ | Instant fail | Market-Gamma |
| **HARD** | Bathrooms | Must be 2+ | Instant fail | Baseline |
| **HARD** | Solar Lease | Must be NONE or OWNED | Instant fail | Market-Beta, Domain-Beta |
| **HARD** | Flood Zone | Must NOT be SFHA (A/AE/AH/AO/VE) | Instant fail | Tech-Alpha |
| SOFT | Sewer | City preferred | 2.5 | Domain-Gamma |
| SOFT | Water Service | DAWS preferred | 2.0 | Domain-Gamma |
| SOFT | Year Built | <2024 preferred | 2.0 | Domain-Beta |
| SOFT | Garage | 2+ spaces | 1.5 | Baseline |
| SOFT | Lot Size | 7k-15k sqft | 1.0 | Baseline |

**Verdict Logic:** FAIL if any HARD fails OR severity sum >= 3.0 | WARNING if 1.5-3.0 | PASS if <1.5

---
