# Section 2: Gap Dependencies

### Critical Path (Blocking Other Fixes)

```
IP-01 (NO background jobs)
  ↓ BLOCKS
IP-02 (NO job queue)
  ↓ BLOCKS
IP-03 (NO worker pool)
  ↓ BLOCKS
IP-04 (NO progress visibility)
```

**Cannot proceed with IP-05 through IP-12 until IP-01→IP-04 resolved.**

```
XT-01 (NO field-level lineage)
  ↓ BLOCKS
XT-04 (Extraction logs not indexed)

VB-01 (No interpretability)
  ↓ REQUIRES
XT-09 (Scoring black box)
  ↓ REQUIRES
XT-10 (Kill-switch reasons)
```

**Cannot improve explainability without first implementing lineage and reasoning generation.**

```
CA-01 (Auto-CLAUDE.md not implemented)
  ↓ BLOCKS (optional, not critical)
CA-02 (Staleness not enforced)
```

### Parallel-Safe Fixes (Can Work Independently)

- VB-02 through VB-08 can be worked in parallel
- CA-01 through CA-05 can be worked in parallel
- XT-05 through XT-08 can be worked in parallel (evolvability)
- XT-13 through XT-15 can be worked in parallel (autonomy)

---
