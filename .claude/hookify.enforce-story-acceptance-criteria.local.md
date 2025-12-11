---
name: enforce-story-acceptance-criteria
enabled: true
event: file
conditions:
  - field: file_path
    operator: regex_match
    pattern: stories/.*\.md$
  - field: new_text
    operator: regex_match
    pattern: (status:\s*(done|complete|finished)|Status:\s*(done|complete|finished)|##\s+Status.*?(done|complete|finished))
action: warn
---

## ✅ Story Completion Checklist

**You're marking a story as DONE. Verify all acceptance criteria before completing.**

### Acceptance Criteria Validation

Before marking DONE, confirm:

- [ ] **Each AC has explicit status**: Mark as PASS or FAIL (not just description)
- [ ] **PASS criteria have evidence**: Include test names, file:line refs, or manual verification notes
- [ ] **FAIL criteria have tickets**: Create follow-up issues for any unmet criteria
- [ ] **No vague language**: Replace "should" / "likely" / "appears to" with concrete pass/fail statements

### Quality Gates Before Completion

- [ ] **Tests written**: Unit or integration tests for new/modified code
- [ ] **Tests passing**: All related tests pass locally (`pytest tests/unit/ -v`)
- [ ] **Documentation updated**: CLAUDE.md, README, or ADRs updated if scope changed
- [ ] **No TODOs/FIXMEs**: Scan code for leftover temporary markers
- [ ] **Code review ready**: Commits are atomic and well-documented

### Sprint Status Update

- [ ] Update `docs/sprint-artifacts/sprint-status.yaml`:
  - Set story status to `done`
  - Add completion date
  - Link to PR or commit SHA
- [ ] Update story file: Add completion notes with test results, blockers resolved, any deviations from plan

### Definition of Done Checklist

Story is DONE only when:

1. ✅ All acceptance criteria explicitly PASS (or FAIL with linked tickets)
2. ✅ Tests written, passing, and added to CI
3. ✅ Documentation updated (CLAUDE.md, README, ADRs)
4. ✅ No placeholders, TODOs, or temporary code remain
5. ✅ Sprint status updated
6. ✅ Ready for review/merge

**Do NOT mark complete until all criteria above are verified.**

### Reference

- Story template: `.claude/templates/story.md`
- Sprint tracking: `docs/sprint-artifacts/sprint-status.yaml`
- Test framework: pytest 9.0.1
