# Integration Map

### Data Flow Across References

```
┌─────────────────────────────────────────────────────────┐
│  Reference Documents Used By Each Wave                   │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  Wave 0: Baseline & Pre-Processing                       │
│  └─> Master Plan (data quality section)                  │
│  └─> Implementation Spec (Wave 0)                        │
│  └─> Phase Execution Guide (Session 0.1-0.3)            │
│                                                           │
│  Wave 1: Kill-Switch Threshold                           │
│  └─> Master Plan (kill-switch redesign, severity table)  │
│  └─> Architecture Doc (kill-switch filter diagram)       │
│  └─> Implementation Spec (Wave 1)                        │
│  └─> Current Kill-Switch Skill (for context)             │
│  └─> Phase Execution Guide (Session 1.1-1.3)            │
│                                                           │
│  Wave 2: Cost Estimation                                 │
│  └─> Master Plan (cost estimation module)                │
│  └─> Architecture Doc (cost estimation diagram)          │
│  └─> AZ Government Reference (utility rates)             │
│  └─> Exterior Quality Reference (maintenance costs)      │
│  └─> Rate Data Sources (mortgage, insurance, utilities)  │
│  └─> Implementation Spec (Wave 2)                        │
│  └─> Phase Execution Guide (Session 2.1-2.4)            │
│                                                           │
│  Wave 3: Data Validation                                 │
│  └─> Master Plan (Layer 1: Pydantic validation)          │
│  └─> Architecture Doc (data quality layer)               │
│  └─> Implementation Spec (Wave 3)                        │
│  └─> Property Entity Structure                           │
│  └─> Phase Execution Guide (Session 3.1-3.2)            │
│                                                           │
│  Wave 4: AI Triage                                       │
│  └─> Master Plan (Layer 2: AI inference)                 │
│  └─> AZ Context Lite (for prompt context)                │
│  └─> Interior Quality Reference (for field inference)    │
│  └─> Exterior Quality Reference (for field inference)    │
│  └─> Implementation Spec (Wave 4)                        │
│  └─> Phase Execution Guide (Session 4.1-4.2)            │
│                                                           │
│  Wave 5: Quality & Lineage                               │
│  └─> Master Plan (Layers 3-5: lineage, metrics)          │
│  └─> Architecture Doc (quality metrics)                  │
│  └─> Quality Baseline (Wave 0 output)                    │
│  └─> Implementation Spec (Wave 5)                        │
│  └─> Phase Execution Guide (Session 5.1-5.2)            │
│                                                           │
│  Wave 6: Documentation & Integration                     │
│  └─> ALL REFERENCES (for updates)                        │
│  └─> Kill-Switch Skill (update)                          │
│  └─> Scoring Skill (update)                              │
│  └─> Deal Sheets Skill (update)                          │
│  └─> Master Plan (verify all decisions implemented)      │
│  └─> Phase Execution Guide (Session 6.1-6.3)            │
└─────────────────────────────────────────────────────────┘
```

---
