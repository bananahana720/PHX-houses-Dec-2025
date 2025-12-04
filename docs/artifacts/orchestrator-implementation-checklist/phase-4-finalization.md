# Phase 4: Finalization

### Step 16: Generate Summary Report
```python
def generate_summary_report(counters, test_mode, research_tasks):
    """Generate final batch summary."""

    print(f"""
{'='*60}
Batch Complete
{'='*60}

Results:
- Attempted: {counters['completed'] + counters['failed']}
- Completed: {counters['completed']}
- Skipped (already done): {counters['skipped']}
- Failed this run: {counters['failed']}

Tier Distribution:
- Unicorns found: {counters['unicorns']}
- Contenders found: {counters['contenders']}
- Pass: {counters['pass']}

Research Tasks:
- Created: {counters['research_created']}
- Auto-completed: {counters['research_completed']}
- Pending manual review: {len(research_tasks['pending_tasks'])}
""")

    if test_mode:
        success_rate = counters['completed'] / (counters['completed'] + counters['failed'])
        recommendation = "Yes" if success_rate >= 0.8 else "No - fix errors first"
        print(f"\nReady for full batch: {recommendation}")
```

### Step 17: Verification
```python
def verify_completion(state, test_mode):
    """Verify all state files updated correctly."""

    # Check no properties stuck in progress
    in_progress = state.get("in_progress_properties", [])
    if in_progress:
        print(f"WARNING: {len(in_progress)} properties still in progress")
        for addr in in_progress:
            phases = state.get("phase_status", {}).get(addr, {})
            print(f"  - {addr}: {phases}")

    # Verify stats
    total_attempted = state["stats"]["total_attempted"]
    completed_count = len(state["completed_properties"])
    success_rate = completed_count / total_attempted if total_attempted > 0 else 0

    print(f"\nVerification:")
    print(f"  Total attempted: {total_attempted}")
    print(f"  Completed: {completed_count}")
    print(f"  Success rate: {success_rate:.1%}")
```

---
