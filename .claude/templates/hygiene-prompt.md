# CLAUDE.md Hygiene Prompt Template

**Action Required:** Update CLAUDE.md files for the directories listed below.

## Directories to Process

{directories}

## Instructions

For each directory:

1. **Check existing CLAUDE.md** - If present, refresh content; if missing, create new
2. **Use template**: `.claude/templates/CLAUDE.md.template` (if available)
3. **Analyze directory**: Read 2-3 representative files to understand purpose

## Required Format

- **Frontmatter**: Include `last_updated` timestamp and `updated_by: agent`
- **Purpose**: 1-2 sentences maximum
- **Contents table**: List up to 10 key files only
- **Style**: Bullets and tables ONLY (no prose paragraphs)
- **Length**: Maximum 100 lines (distill if longer)

## File Extensions to Analyze

{file_extensions}

## Validation Checklist

- [ ] Frontmatter has `last_updated` and `updated_by: agent`
- [ ] Purpose is 1-2 sentences
- [ ] Contents table lists ≤10 files
- [ ] Uses only bullets and tables
- [ ] Total ≤100 lines

Process directories in batches of 5 for efficiency.
