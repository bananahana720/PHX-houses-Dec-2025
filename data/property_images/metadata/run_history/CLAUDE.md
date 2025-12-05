<!-- TEMPLATE:UNFILLED -->
<!-- TOKEN-EFFICIENT CONTEXT: Target 50-80 lines, max 100 -->
<!-- child CLAUDE.md | Remove this block when populated -->
---
last_updated: [YYYY-MM-DDTHH:MM:SSZ]
updated_by: [main|agent]
staleness_hours: 24
line_target: 80
flags: []
---
# [Directory Name]

## Purpose
<!-- 1-2 sentences MAX. What does this directory do? Why does it exist? -->
[Brief what + why]

## Contents
<!-- Key files only (≤10 rows). Skip __init__.py, tests, generated files -->
| File | Purpose |
|------|---------|
| `file.py` | [one-line desc] |

## Key Patterns
<!-- 2-3 bullet points of patterns/conventions used here -->
- [pattern]: [brief explanation]

## Tasks
<!-- Max 5 items. Priority: H=blocking, M=important, L=nice-to-have -->
- [ ] [task description] `P:H`

## Learnings
<!-- Max 3 discoveries. Things that surprised you or are non-obvious -->
- [discovery]: [why it matters]

## Refs
<!-- Cross-references essential for navigation only -->
- [what]: `path/to/file:lines`

## Deps
<!-- Import graph edges that affect understanding -->
← imports: [module1], [module2]
→ used by: [consumer1]

<!--
TOKEN EFFICIENCY CHECKLIST (delete after review):
[ ] Purpose ≤2 sentences
[ ] Contents table ≤10 rows, key files only
[ ] No prose paragraphs - bullets/tables only
[ ] Learnings ≤3 items, non-obvious only
[ ] Total lines ≤100 (target 50-80)
[ ] Frontmatter has last_updated timestamp
-->
