# The Key Insight

```
┌─ URL Construction ─────────────────────────────────────┐
│                                                         │
│  Current: /homes/{address}_rb/                         │
│  ↓                                                      │
│  Lands on: SEARCH RESULTS page                         │
│  ↓                                                      │
│  Page contains: Multiple property thumbnails           │
│  ↓                                                      │
│  Extraction blindly: Grabs ALL images on page          │
│  ↓                                                      │
│  Filter can't tell: Which images belong to which       │
│  ↓                                                      │
│  Result: WRONG IMAGES                                  │
│                                                         │
└─────────────────────────────────────────────────────────┘

┌─ URL Navigation (Fixed) ─────────────────────────────┐
│                                                      │
│  New: Interactive search                            │
│  ↓                                                   │
│  Lands on: PROPERTY DETAIL page                     │
│  ↓                                                   │
│  Page contains: Single property gallery             │
│  ↓                                                   │
│  Extraction: Grabs images from THIS property only   │
│  ↓                                                   │
│  Filter validates: Page type before extraction      │
│  ↓                                                   │
│  Result: CORRECT IMAGES                            │
│                                                      │
└──────────────────────────────────────────────────────┘

THE PROBLEM IS NOT THE EXTRACTION LOGIC.
THE PROBLEM IS THE DESTINATION PAGE.
```

---
