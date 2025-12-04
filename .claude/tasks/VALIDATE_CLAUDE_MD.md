# CLAUDE.md Validation Task - Haiku Subagent

**Status:** Ready for Independent Validation
**Requested By:** Main Agent (Claude Code)
**Model:** Haiku 4.5 (lightweight, fast validation)
**Priority:** HIGH
**Deadline:** Before session commit

## Task Brief

Validate 7 CLAUDE.md files created/updated in current session against template requirements. Perform quality assurance, identify gaps, and update any files that don't meet standards.

## Files to Validate

1. `.claude/tasks/CLAUDE.md` - NEW (Task coordination)
2. `docs/sprint_artifacts/CLAUDE.md` - NEW (Sprint tracking)
3. `docs/stories/CLAUDE.md` - NEW (Story repository)
4. `src/phx_home_analysis/CLAUDE.md` - UPDATED (Core library)
5. `src/phx_home_analysis/errors/CLAUDE.md` - NEW (Error handling)
6. `tests/integration/CLAUDE.md` - UPDATED (Integration tests)
7. `tests/unit/errors/CLAUDE.md` - NEW (Unit tests)

## Template Requirements (Reference: `.claude/templates/CLAUDE.md.template`)

### Mandatory Structure
- [ ] YAML frontmatter with:
  - `last_updated: YYYY-MM-DD` (current date)
  - `updated_by: [main|agent]`
  - `staleness_hours: 24`
  - `flags: []`
- [ ] `# [Directory Name]` heading
- [ ] `## Purpose` section (1-2 sentences max)
- [ ] `## Contents` table with Path | Purpose columns
- [ ] `## Tasks` checklist with `P:H|M|L` priority markers
- [ ] `## Learnings` bullet points (at least 2-3)
- [ ] `## Refs` with file:line references
- [ ] `## Deps` with ← imports and → imported by

### Quality Criteria
- [ ] Word count ≤ 250 (body text, excluding YAML)
- [ ] No placeholder text (e.g., "[desc]", "[pattern/discovery]")
- [ ] file:line references are accurate
- [ ] Markdown formatting is clean
- [ ] No template tags or comments left in
- [ ] All sections contain meaningful content (not stubs)

### Content Validation
- [ ] Purpose explains what + why clearly
- [ ] Contents table accurately reflects directory structure
- [ ] Tasks are specific and actionable
- [ ] Learnings capture actual patterns discovered
- [ ] Refs point to relevant code locations with precision
- [ ] Deps clearly show data flow and dependencies

## Validation Instructions

### For Each File:

1. **Read** the file completely
2. **Check** against template structure above
3. **Score** based on:
   - 0% = Missing sections, all placeholders
   - 50% = Has sections but incomplete content
   - 85% = Good structure, minor gaps
   - 100% = Complete, accurate, meets all criteria
4. **If < 85%:** Update the file using Edit tool to meet requirements
5. **If >= 85%:** No changes needed, mark as validated

### Update Strategy (If Needed):

- Use **Edit tool** (not Write) to preserve existing quality content
- Only enhance/refine, don't rewrite
- Maintain the voice and accuracy of original
- Ensure word count stays ≤ 250
- Update `updated_by: agent` (since you're refining)
- Update `last_updated: 2025-12-04`

## Success Criteria

✓ All 7 files validated
✓ All files score ≥ 85% on template compliance
✓ All mandatory sections present and complete
✓ No placeholder text remaining
✓ All file:line refs verified as accurate
✓ Word counts confirmed ≤ 250
✓ Ready for commit approval

## Acceptance

When complete, return summary:
```
VALIDATION COMPLETE
- Files validated: 7/7
- Files updated: [N]
- All files pass template compliance: YES
- Ready for commit: YES
```

## Notes

- These files were created by main agent using template structure
- Some may be near 250 words - don't expand, only refine
- Accuracy of file:line references is critical
- Learnings should reflect actual discoveries, not generic statements
- Purpose statements must be concise (1-2 sentences)

---

**Task Created:** 2025-12-04
**Requested By:** Main Agent
**Model Suggested:** Haiku 4.5
