# State Management Architecture

### State Files

| File | Purpose | Access Pattern |
|------|---------|----------------|
| `work_items.json` | Pipeline progress | Read at start, write after each property |
| `enrichment_data.json` | Property data | Read/write per property update |
| `extraction_state.json` | Image extraction | Read/write during Phase 2 |

### Crash Recovery Protocol

```python
def resume_pipeline(work_items_path: Path) -> list[str]:
    """Identify properties needing work based on state file."""

    work = json.load(open(work_items_path))

    # Reset stuck in_progress items (30 min timeout)
    timeout = timedelta(minutes=30)
    now = datetime.now()

    for item in work['work_items']:
        for phase, data in item['phases'].items():
            if data['status'] == 'in_progress':
                started = datetime.fromisoformat(data['started_at'])
                if now - started > timeout:
                    data['status'] = 'pending'
                    print(f"Reset stuck {phase} for {item['address']}")

    # Find pending work
    pending = []
    for item in work['work_items']:
        for phase, data in item['phases'].items():
            if data['status'] == 'pending':
                pending.append((item['address'], phase))

    return pending
```

### Checkpointing Strategy

```python
def checkpoint_after_property(address: str, phase: str, status: str):
    """Write checkpoint after each property phase completes."""

    work = json.load(open('data/work_items.json'))

    item = next(
        (w for w in work['work_items'] if w['address'] == address),
        None
    )

    if item:
        item['phases'][phase]['status'] = status
        item['phases'][phase]['completed_at'] = datetime.now().isoformat()
        item['last_updated'] = datetime.now().isoformat()

        # Update summary
        work['summary'] = calculate_summary(work['work_items'])
        work['last_checkpoint'] = datetime.now().isoformat()

        # Atomic write with backup
        backup = Path('data/work_items.json.bak')
        shutil.copy('data/work_items.json', backup)

        with open('data/work_items.json', 'w') as f:
            json.dump(work, f, indent=2)
```

---
