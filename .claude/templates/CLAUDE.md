---
last_updated: 2025-12-06T23:30:00Z
updated_by: agent
---

# templates

## Purpose
Repository of documentation and automation templates for creating/updating CLAUDE.md files across the PHX Houses project. Provides standardized formats for hygiene prompts and CLAUDE.md documentation files.

## Contents
| File | Purpose |
|------|---------|
| `CLAUDE.md.template` | Master template for module/directory CLAUDE.md files with frontmatter, sections, and examples |
| `hygiene-prompt.md` | Automation template for batch-updating CLAUDE.md files; includes validation checklist |

## Usage

**Creating a new CLAUDE.md:**
- Copy structure from `CLAUDE.md.template`
- Fill frontmatter: `last_updated`, `updated_by: agent`
- Populate Purpose (1-2 sentences), Contents table (≤10 files), and relevant sections

**Batch updates:**
- Use `hygiene-prompt.md` template to generate automation prompts
- Substitute `{directories}` and `{file_extensions}` placeholders
- Follow validation checklist to ensure consistency

## Key Patterns
- **Frontmatter**: YAML with `last_updated` timestamp and `updated_by` field
- **Conciseness**: Max 100 lines; bullets and tables only
- **Scope**: Single directory per CLAUDE.md file
- **Validation**: Frontmatter + Purpose + Contents + Style checked

## Refs
- Parent: `../.claude/CLAUDE.md` (main Claude Code config)
- Used by: All `.claude/**/CLAUDE.md` maintenance tasks
