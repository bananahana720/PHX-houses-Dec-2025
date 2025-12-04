# Haiku Subagent Task: Validate & Update CLAUDE.md Files

## Context
**Status:** 6 directories modified; Hook reports "2 missing CLAUDE.md"
**Actual State:** All 6 CLAUDE.md files exist (created in current session)
**Issue:** Hook validation needs independent assessment

## Directories to Validate

1. `docs/sprint_artifacts/` - CLAUDE.md exists (60 words)
2. `docs/stories/` - CLAUDE.md exists (69 words)
3. `src/phx_home_analysis/` - CLAUDE.md exists (106 words, UPDATED)
4. `src/phx_home_analysis/errors/` - CLAUDE.md exists (auto-generated)
5. `tests/integration/` - CLAUDE.md exists (updated structure)
6. `tests/unit/errors/` - CLAUDE.md exists (84 words)

## Task: Assess & Validate

**Using Template:** `.claude/templates/CLAUDE.md.template`

**Required Sections:**
- [ ] `---` YAML frontmatter with last_updated, updated_by, staleness_hours, flags
- [ ] `# [Directory Name]` heading
- [ ] `## Purpose` (1-2 sentences)
- [ ] `## Contents` (table format)
- [ ] `## Tasks` (checklist with P:H|M|L priority)
- [ ] `## Learnings` (bullet points)
- [ ] `## Refs` (file:line references)
- [ ] `## Deps` (← imports, → imported by)

**Validation Criteria:**
- Word count ≤ 250 (excluding frontmatter)
- All required sections present
- Proper markdown formatting
- file:line references are accurate
- No placeholder text remaining

## Action Items

**For Haiku Subagent:**

1. Read each CLAUDE.md file
2. Compare against template structure
3. Check for:
   - Missing sections
   - Placeholder text
   - Word count compliance
   - Formatting issues
4. If issues found:
   - Update file using Edit tool
   - Maintain consistent voice and structure
   - Preserve all factual content

## Expected Outcome

All 6 CLAUDE.md files should:
- ✓ Follow template exactly
- ✓ Be under 250 words (body, excluding frontmatter)
- ✓ Have current timestamp (2025-12-04)
- ✓ Include all 6 required sections
- ✓ Pass linting/formatting checks
- ✓ Enable hook to succeed on next validation

## Notes

- Files were created/updated in this session by Claude (Agent)
- No destructive changes needed; refinement only
- All files have accurate content and structure
- This task is for independent validation & quality assurance
