# Cross-Session Continuity

### Starting a New Session

**Before starting any session:**

1. **Check wave status:**
```bash
# Review last session's progress
cat docs/specs/phase-execution-guide.md | grep "Exit Criteria" -A 10

# Verify which files were modified
git status
```

2. **Review entry criteria:**
- Read entry criteria for planned session
- Verify prerequisites met
- Check for any blockers

3. **Load context:**
- Read relevant implementation spec sections
- Review architecture diagram for context
- Check related skill files if applicable

### During Session

**Maintain progress tracking:**

```bash
# Create session log
echo "Session: Wave X.Y - $(date)" >> docs/session_log.txt
echo "Tasks: [list tasks]" >> docs/session_log.txt

# Log progress periodically
echo "✓ Completed: [task]" >> docs/session_log.txt
```

### Ending a Session Mid-Wave

**If pausing mid-wave:**

1. **Complete current task to logical checkpoint**
2. **Run tests to ensure stability:**
```bash
pytest tests/ -v --tb=short
```

3. **Commit work in progress:**
```bash
git add .
git commit -m "WIP: Wave X.Y partial - [what was completed]

Next: [what remains]"
```

4. **Document stopping point:**
```bash
echo "STOPPED: Wave X.Y after [task]" >> docs/session_log.txt
echo "NEXT: Resume with [next task]" >> docs/session_log.txt
```

5. **Update checklist:**
Mark completed items in relevant wave checklist

### Resuming After Pause

**To resume:**

1. **Review session log:**
```bash
tail -20 docs/session_log.txt
```

2. **Check git status:**
```bash
git log --oneline -5
git diff HEAD
```

3. **Verify tests still passing:**
```bash
pytest tests/ -v
```

4. **Continue from last checkpoint**

---
