# Executive Summary

### Project Vision

PHX Houses Analysis Pipeline is a personal decision support system that transforms Phoenix real estate listings into actionable intelligence through systematic filtering and comprehensive scoring. The core UX goal is **eliminating decision anxiety** — making "no" decisions automatic through kill-switches and "yes" decisions confident through transparent scoring and proactive risk intelligence.

The system serves a first-time homebuyer who values data-driven confidence over gut feel, with a target of being under contract by Jan-Feb 2026 on a property scoring 450+ points with zero post-inspection surprises.

### Target Users

**Primary Persona: The Anxious First-Time Buyer**
- Goal: Find a home passing rigorous criteria (4 bed, 2 bath, no HOA, city sewer, 7k-15k sqft lot)
- Pain points: Decision fatigue, fear of hidden risks, Arizona-specific blindspots (HVAC lifespan, pool costs, solar leases)
- Tech comfort: High (CLI, YAML editing, JSON familiarity)
- Devices: Desktop for analysis, mobile for property tours
- Success metric: Zero post-inspection surprises

**Secondary Persona: The System Administrator**
- Goal: Maintain and debug multi-agent pipeline
- Pain points: 30+ min blocking operations, anti-bot failures, state corruption
- Success metric: <5 second resume capability, <15 min troubleshooting

### Key Design Challenges

1. **Cognitive Load Management**: 600-point scoring system with 18 strategies requires progressive disclosure (tier badge → dimension breakdown → full strategy detail)

2. **Risk Communication**: Warnings must connect to tangible consequences (cost, quality of life, resale impact) with clear actions, not just flags

3. **Mobile Deal Sheet Experience**: Must be scannable in <2 minutes on 5-inch screen during property tours, with critical info above fold

4. **Pipeline Visibility & Trust**: 30+ minute runs require progress updates every ≤30 seconds with actionable error messages

5. **Configuration Accessibility**: YAML-based config must be self-documenting with validation feedback

### Design Opportunities

1. **Emotional Confidence Building**: Transform cold data into narrative stories that build decision confidence

2. **"What If" Scenario Modeling**: Let users explore priority changes with instant score reranking

3. **Tour Checklist Generation**: Auto-generate property-specific inspection checklists bridging digital analysis to physical inspection

4. **Competitive Intelligence Visualization**: "Value Spotter" scatter plots surfacing underpriced quality properties visually
