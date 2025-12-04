# INTERPRETABILITY ANALYSIS

### Current State: Scoring is Clear but Not Self-Explanatory

**What Works Well:**
1. **Weights are explicit** - Every criterion has a point value (e.g., school_district: 42 pts)
2. **Scoring thresholds documented** - Distance bands (quiet: >2mi = 30pts, highway: <0.5mi = 3pts)
3. **Tier boundaries clear** - Unicorn >480 (80%), Contender 360-480 (60-80%), Pass <360
4. **Kill-switch logic transparent** - Severity thresholds at 3.0 (FAIL) and 1.5 (WARNING)

**What's Missing (Interpretability Gaps):**
1. **No decision trees/rubrics for visual scoring** - Kitchen layout (40pts) → how is 40 awarded? (current: 0-40 scale, default 20)
2. **No per-property breakdown reporting** - Score of 415 doesn't explain which section pulled it down
3. **No counterfactual reasoning** - "What if you fixed the roof?" impact not calculated
4. **No relative positioning** - "Top 15% of market" vs absolute tier not clear
5. **No "buy signal" thresholds** - When should you make an offer? (Only "Unicorn/Contender/Pass")

**Opportunity for Improvement:**
```
Current: "Score: 415 (Contender)"
Better:  "Score: 415 (Contender - 69% of max)
         Section A (Location): 185/250 (74%) - Schools strong (42/42), Crime moderate (30/47), Quietness weak (5/30)
         Section B (Systems): 95/170 (56%) - Roof aging (-10pts), Cost efficient (+35pts)
         Section C (Interior): 135/180 (75%) - Good kitchen/master, ceilings standard

         Buy signals: Top 25% of comparable homes in this price range"
```

---
