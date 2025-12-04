# Batch Processing Protocol

### Sequential Processing Flow

```
for property in to_process:
    1. Acquire lock (work_items.json)
    2. Phase 0 (county) → early kill-switch check
    3. Phase 0.5 (cost) → monthly cost estimation
    4. Phase 1 (listing + map) → parallel
    5. PRE-SPAWN VALIDATION for Phase 2:
       └─ python scripts/validate_phase_prerequisites.py --address "$ADDRESS" --phase phase2_images --json
       └─ If exit code 1 → log BLOCKED, skip Phase 2A/2B
       └─ If exit code 0 → extract context for agent spawn
    6. Phase 2A (exterior) → spawn with validated context
    7. Phase 2B (interior) → spawn with validated context (if Phase 2A complete)
    8. Phase 3 (synthesis) → includes CostEfficiencyScorer
    9. Phase 4 (report)
   10. Update work_items.json
   11. Git commit property completion
   12. Release lock
```

### Triage

```python
# Skip if:
# - status == "complete" (in work_items.json)
# - retry_count >= 3
# For --test: limit to first 5 from CSV
```

### Progress Display

```
Processing: 5/25 properties
Current: 123 Main St, Phoenix, AZ 85001
Phase: 2B (Interior Assessment)
Completed: 4 | Failed: 0 | Skipped: 1
Unicorns: 1 | Contenders: 2 | Pass: 1

Session: session_20251202_123456
Locked: 123 Main St
Last Commit: ef7cd95f (4732 W Davis Rd - CONTENDER)
```
