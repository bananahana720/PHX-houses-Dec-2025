# 7. Priority Matrix

```
                    HIGH IMPACT
                         │
    ┌────────────────────┼────────────────────┐
    │                    │                    │
    │  Extract shared    │  Decompose long    │
    │  data loaders      │  functions         │
    │                    │                    │
    │  Centralize        │  Add unit tests    │
    │  configuration     │                    │
LOW ├────────────────────┼────────────────────┤ HIGH
EFFORT                   │                    EFFORT
    │                    │                    │
    │  Fix global        │  Strategy pattern  │
    │  execution         │  for scoring       │
    │                    │                    │
    │  Add type hints    │  Full repository   │
    │                    │  pattern           │
    │                    │                    │
    └────────────────────┼────────────────────┘
                         │
                    LOW IMPACT
```

---
