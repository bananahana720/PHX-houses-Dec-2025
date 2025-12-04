# Phase 0: Initialization

### Step 1: Parse Arguments
```python
import sys

args = sys.argv[1:]
test_mode = "--test" in args
batch_mode = "--all" in args or test_mode
single_address = None if batch_mode else args[0] if args else None
```

### Step 2: Load State Files
```python
import json
from pathlib import Path

# Load extraction state with validation
state = load_extraction_state("data/property_images/metadata/extraction_state.json")
validate_extraction_state(state)  # Ensure v2 schema

# Load research tasks
research_tasks = json.load(open("data/research_tasks.json"))
pending_count = len(research_tasks.get("pending_tasks", []))

if pending_count > 0:
    print(f"Note: {pending_count} research tasks pending - agents will attempt pickup")
```

### Step 3: Determine Scope
```python
# Load properties from CSV
with open("data/phx_homes.csv") as f:
    properties = [line.strip() for line in f.readlines()[1:]]  # Skip header

if test_mode:
    properties = properties[:5]
    print(f"TEST MODE: Limited to {len(properties)} properties")
```

### Step 4: Apply Triage
```python
completed = set(state.get("completed_properties", []))
failed = state.get("failed_properties", [])
retry_counts = state.get("retry_counts", {})

to_process = []
to_skip = []

for prop in properties:
    if prop in completed:
        to_skip.append({"address": prop, "reason": "already_completed"})
    elif prop in failed and retry_counts.get(prop, 0) >= 3:
        to_skip.append({"address": prop, "reason": "max_retries"})
    else:
        to_process.append(prop)

print(f"Scope: {len(to_process)} to process, {len(to_skip)} skipped")
```

---
