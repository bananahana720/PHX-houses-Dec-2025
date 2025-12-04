---
name: inspection-standards
description: Convert property assessments to professional appraisal terminology. UAD Quality (Q1-Q6) and Condition (C1-C6) ratings, ASHI inspection terms, component age estimation with Arizona climate adjustments. Use when writing deal sheets, estimating repair costs, documenting findings, or communicating with real estate professionals.
allowed-tools: Read
---

# Inspection Standards Skill

Professional appraisal terminology bridging subjective assessment and industry-standard language for mortgage underwriting, insurance, and professional communication.

## Quick Reference: Score to UAD Mapping

| Score | Quality | Condition | Description |
|-------|---------|-----------|-------------|
| 10 | Q1-Q2 | C1-C2 | New/like-new, premium materials |
| 9 | Q2 | C2 | Excellent, high-quality |
| 8 | Q2-Q3 | C2-C3 | Very good, well-maintained |
| 7 | Q3 | C3 | Good, normal wear |
| 6 | Q3-Q4 | C3-C4 | Average, minor maintenance |
| 5 | Q4 | C4 | Average/fair, showing age |
| 4 | Q4-Q5 | C4-C5 | Fair, deferred maintenance |
| 3 | Q5 | C5 | Fair/poor, significant repairs |
| 2 | Q5-Q6 | C5-C6 | Poor, major repairs required |
| 1 | Q6 | C6 | Non-functional, structural concerns |

**Key distinction:**
- **Quality (Q1-Q6)**: PERMANENT - materials, craftsmanship, design
- **Condition (C1-C6)**: CURRENT STATE - maintenance, wear, age (changes over time)

## Quick Reference: Component Lifespans (Arizona)

| Component | Phoenix Life | Visual End-of-Life Signs |
|-----------|--------------|-------------------------|
| Asphalt roof | 15-20 yrs | >30% granule loss, curling, bare substrate |
| Tile roof | 40-50 yrs | Underlayment: 20-25 yrs |
| HVAC | 10-15 yrs | Loud compressor, rust, R-22, multiple repairs |
| Pool pump | 8-12 yrs | Loud noise, severe rust |
| Water heater | 8-10 yrs | Rust, leaks, inconsistent temp |

**Arizona factor**: Reduce standard lifespans 25-30% for UV/heat exposure.

## Decision Logic: Assessment Protocol

### Step 1: Assess Quality (Permanent)
```
What materials? Premium → Q1-Q2, Builder-grade → Q4, Economy → Q5-Q6
What craftsmanship? Exceptional → Q1, Competent → Q4, Poor → Q6
```

### Step 2: Assess Condition (Current)
```
Any deferred maintenance? None → C1-C3, Some → C4, Extensive → C5-C6
Systems functional? New/like-new → C1-C2, Working → C3-C4, Failing → C5-C6
```

### Step 3: Map to Internal Score
Use table above. Average Q and C if they differ.

### Step 4: Document with UAD Terminology
```
"Kitchen: Q3/C3 (Good quality, good condition), updated 2015"
"Roof: C4 (Average condition), estimated 12-15 years old"
```

## Reference Shards

| Shard | WHAT | WHEN | HOW |
|-------|------|------|-----|
| `uad-ratings.yaml` | UAD Q1-Q6, C1-C6 definitions | Converting scores to professional terms | `quality_ratings.<Q1-Q6>`, `condition_ratings.<C1-C6>` |
| `ashi-glossary.yaml` | ASHI inspection terminology | Documenting specific conditions | `<category>.<term>` (e.g., `roof.cupping`) |
| `component-lifespans.yaml` | AZ-adjusted ages & costs | Estimating replacement timing | `<component>.visual_age_indicators` |

**To load detail:** `Read .claude/skills/inspection-standards/<shard>.yaml`

## Mortgage Eligibility Quick Reference

| Condition | Loan Type | Notes |
|-----------|-----------|-------|
| C1-C3 | Any | No issues |
| C4 | Conv/FHA | FHA may require health/safety repairs |
| C5 | FHA requires repairs | Conventional scrutiny |
| C6 | Renovation loan only | Cash or FHA 203k |

## Red Flags (Stop-the-Line Issues)

- **R-22 refrigerant**: Phased out 2020, expensive, replacement needed
- **Polybutylene pipes** (gray, 1978-1995): Class-action failures, insurance issues
- **Federal Pacific panel**: Fire hazard, replacement required by insurers
- **Post-tension cables**: NEVER CUT (common in Phoenix slabs)
- **Septic system**: Many Phoenix buyers require city sewer

## Best Practices

1. **Assess Quality first** (permanent), then Condition (current state)
2. **Use Arizona-adjusted lifespans** - reduce national averages 25-30%
3. **Document with UAD terminology** in deal sheets for professional credibility
4. **Load reference shards** when you need detailed definitions or cost estimates
5. **Flag red flags** immediately - these are often deal-breakers
