# Agent Orientation (Shared)

This snippet contains common orientation rules for all agents. Reference this file in agent definitions.

## Tool Usage Rules (MANDATORY - TIER 0)

These rules OVERRIDE any examples in agent files:

| Never Use | Always Use Instead |
|-----------|-------------------|
| `bash cat FILE` | `Read` tool |
| `bash head/tail FILE` | `Read` tool with offset/limit |
| `bash grep PATTERN` | `Grep` tool |
| `bash find DIR` | `Glob` tool |
| `bash ls DIR` | `Glob` tool |
| `cat FILE \| python -c` | `Read` tool, then parse in response |

## Data Structure Reminders

### enrichment_data.json is a LIST

```python
# CORRECT - list iteration
data = json.loads(file_content)  # Returns LIST of dicts
prop = next((p for p in data if p["full_address"] == address), None)

# WRONG - dict access
prop = data[address]  # TypeError: list indices must be integers
```

### work_items.json Structure

```python
work_items = json.loads(file_content)
session = work_items["session"]
items = work_items["work_items"]  # List of work item dicts
item = next((i for i in items if i["address"] == address), None)
```

## Common Orientation Steps

### 1. Load State Files

```
Read: data/work_items.json
Read: data/enrichment_data.json
```

### 2. Find Target Property

```python
# From enrichment_data (LIST)
prop = next((p for p in data if p["full_address"] == TARGET_ADDRESS), None)

# From work_items
item = next((i for i in work_items["work_items"] if i["address"] == TARGET_ADDRESS), None)
```

### 3. Check Phase Status

```python
if item:
    phase_status = item.get("phase_status", {})
    # Check relevant phase: phase0_county, phase1_listing, phase2_images, etc.
```

## Pre-Phase Validation

Before Phase 2 (image assessment), validate prerequisites:

```bash
python scripts/validate_phase_prerequisites.py --address "ADDRESS" --phase phase2_images --json
```

Only spawn agent if exit code is 0 (can_spawn=true).
