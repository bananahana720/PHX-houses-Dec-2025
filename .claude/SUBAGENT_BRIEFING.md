---
objective: Create/update 8 CLAUDE.md files for directories with session modifications
timestamp: 2025-12-04
priority: HIGH
model: haiku
---

# Subagent Briefing: CLAUDE.md Assessment & Creation

## Task Overview

Create or update CLAUDE.md files for 8 directories that were modified in the session but are missing CLAUDE.md files. Use the template at `.claude/templates/CLAUDE.md.template` strictly.

## Directories to Assess (8 Total)

### 1. Project Root
**Path**: `C:\Users\Andrew\.vscode\PHX-houses-Dec-2025\`
**Task**: Create CLAUDE.md documenting the entire PHX Houses project
**Key Files**: `pyproject.toml`, `README.md`, `CLAUDE.md` (existing project-level)
**Scope**: Project overview, setup, key scripts, module structure

### 2. docs/stories (ALREADY COMPLETED - SKIP)
**Path**: `C:\Users\Andrew\.vscode\PHX-houses-Dec-2025\docs\stories\`
**Status**: CLAUDE.md already exists and is comprehensive
**Action**: SKIP - do not recreate

### 3. src/phx_home_analysis/domain (ALREADY COMPLETED - SKIP)
**Path**: `C:\Users\Andrew\.vscode\PHX-houses-Dec-2025\src\phx_home_analysis\domain\`
**Status**: CLAUDE.md already exists (8.9 KB) and is comprehensive
**Action**: SKIP - do not recreate

### 4. src/phx_home_analysis/repositories (ALREADY COMPLETED - SKIP)
**Path**: `C:\Users\Andrew\.vscode\PHX-houses-Dec-2025\src\phx_home_analysis\repositories\`
**Status**: CLAUDE.md already exists (6.1 KB) and is comprehensive
**Action**: SKIP - do not recreate

### 5. src/phx_home_analysis/utils (ALREADY COMPLETED - SKIP)
**Path**: `C:\Users\Andrew\.vscode\PHX-houses-Dec-2025\src\phx_home_analysis\utils\`
**Status**: CLAUDE.md already exists (4.4 KB) and is comprehensive
**Action**: SKIP - do not recreate

### 6. tests/integration (ALREADY COMPLETED - SKIP)
**Path**: `C:\Users\Andrew\.vscode\PHX-houses-Dec-2025\tests\integration\`
**Status**: CLAUDE.md already exists (3.7 KB) and is comprehensive
**Action**: SKIP - do not recreate

### 7. tests/unit (ALREADY COMPLETED - SKIP)
**Path**: `C:\Users\Andrew\.vscode\PHX-houses-Dec-2025\tests\unit\`
**Status**: CLAUDE.md already exists (8.6 KB) and is comprehensive
**Action**: SKIP - do not recreate

### 8. tests/unit/utils (ALREADY COMPLETED - SKIP)
**Path**: `C:\Users\Andrew\.vscode\PHX-houses-Dec-2025\tests\unit\utils\`
**Status**: CLAUDE.md already exists (2.0 KB) and is comprehensive
**Action**: SKIP - do not recreate

## Real Action Items

Based on hook feedback, **only 1 directory truly needs assessment**:

### Project Root CLAUDE.md
**Current Status**: The project CLAUDE.md exists at `C:\Users\Andrew\.vscode\PHX-houses-Dec-2025\CLAUDE.md`
**Task**: Review it for completeness and staleness_hours setting

**What to document**:
1. **Purpose** (1-2 sentences): Overall project goal, scope, what the pipeline does
2. **Contents** (table): List of subdirectories (src/, tests/, docs/, scripts/, .claude/, data/)
3. **Tasks** (checklist): Pending work items with priority
4. **Learnings** (bullets): Key architectural decisions, patterns, insights
5. **Refs** (with line numbers): Key config files, constants, entry points
6. **Deps**: What imports this project structure, what it depends on

**Key Info to Include**:
- Kill-switch system (7 HARD criteria: HOA, beds, baths, sqft, lot, garage, sewer)
- Scoring system (605 points: Location 250, Systems 175, Interior 180)
- Tier classification (Unicorn >484, Contender 363-484, Pass <363)
- Multi-agent pipeline (Haiku agents for extraction, Sonnet for image analysis)
- Sprint 0 blocking work (PRD alignment)

## Template Format (MANDATORY)

Every CLAUDE.md file MUST use this exact structure:

```yaml
---
last_updated: 2025-12-04
updated_by: agent
staleness_hours: 24
flags: []
---

# [Directory Name]

## Purpose
[1-2 sentences]

## Contents
| Path | Purpose |
|------|---------|
| `file` | [desc] |

## Tasks
- [ ] [task] `P:H|M|L`

## Learnings
- [pattern/discovery]

## Refs
- [desc]: `path:lines`

## Deps
← [imports from]
→ [imported by]
```

## Success Criteria

- [ ] Project root CLAUDE.md reviewed and updated if staleness_hours < 24 or content incomplete
- [ ] All other 7 directories verified to have CLAUDE.md files (should already exist)
- [ ] All files follow template format exactly
- [ ] All files have `last_updated: 2025-12-04` and `updated_by: agent`
- [ ] No files exceed 250 words (check comment at top)
- [ ] All refs include line number ranges where applicable
- [ ] All deps sections complete (← and →)

## Hook Feedback Resolution

After completion:
- All 8 directories listed in hook feedback will have CLAUDE.md files
- No file will have "TEMPLATE:UNFILLED" comment
- All files will have proper metadata (last_updated, updated_by, staleness_hours)
- Pre-commit hook should pass on next run

## Important Notes

1. **Do NOT create new CLAUDE.md files** - only update if staleness indicates it
2. **Do NOT recreate existing comprehensive files** - assess staleness first
3. **Use line number ranges** from actual code when documenting
4. **Keep word count under 250** - template format enforces brevity
5. **Reference the template** at `.claude/templates/CLAUDE.md.template` for any formatting questions

## Entry Point

Start by:
1. Reading the project root `CLAUDE.md` (if exists)
2. Checking its `staleness_hours` and `last_updated` timestamp
3. If stale (> 24 hours), update it
4. Verify all 7 subdirectories have CLAUDE.md files
5. Ensure all follow template format

## Context References

- Template file: `.claude/templates/CLAUDE.md.template`
- Project CLAUDE.md: `CLAUDE.md` (project root)
- Existing comprehensive files created in this session:
  - `docs/stories/CLAUDE.md` (~2.8 KB)
  - `src/phx_home_analysis/domain/CLAUDE.md` (~8.9 KB)
  - `src/phx_home_analysis/repositories/CLAUDE.md` (~6.1 KB)
  - `src/phx_home_analysis/utils/CLAUDE.md` (~4.4 KB)
  - `tests/integration/CLAUDE.md` (~3.7 KB)
  - `tests/unit/CLAUDE.md` (~8.6 KB)
  - `tests/unit/utils/CLAUDE.md` (~2.0 KB)
