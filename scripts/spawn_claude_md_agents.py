#!/usr/bin/env python3
"""
Spawn parallel Haiku subagents to assess directories and create CLAUDE.md files.
Each agent gets one directory to analyze.
"""

# Target directories (relative to project root)
DIRECTORIES = [
    "src/phx_home_analysis/domain",
    "src/phx_home_analysis/utils",
    "tests/unit",
    "tests/integration",
    "tests/unit/utils",
    "docs/stories"
]

# Template
TEMPLATE = """---
last_updated: 2025-12-04
updated_by: agent
staleness_hours: 24
flags: []
---
# {dir_name}

## Purpose
[1-2 sentences: what + why]

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
"""

def main():
    """Print subagent spawn instructions."""
    print("=" * 80)
    print("PARALLEL SUBAGENT SPAWNING PLAN")
    print("=" * 80)
    print("\nSpawn these Haiku subagents in PARALLEL (independent work):\n")

    for i, directory in enumerate(DIRECTORIES, 1):
        print(f"{i}. Assess: {directory}")
        print("   Task: Read directory structure, analyze all files, create CLAUDE.md")
        print(f"   Output: {directory}/CLAUDE.md")
        print("   Template: .claude/templates/CLAUDE.md.template")
        print()

    print("\nTemplate location:")
    print("  .claude/templates/CLAUDE.md.template")
    print("\nInstructions for each agent:")
    print("  1. Read entire directory structure (glob *.py, *.md, *.yaml, etc.)")
    print("  2. Identify purpose, contents, patterns, dependencies")
    print("  3. Create CLAUDE.md using template")
    print("  4. Fill sections: Purpose, Contents table, Learnings, Refs, Deps")
    print("  5. Keep to <250 words + structured tables")
    print("\nSuccess criteria:")
    print("  - CLAUDE.md exists in each directory")
    print("  - Frontmatter: last_updated, updated_by, staleness_hours, flags")
    print("  - All sections populated (Purpose, Contents, Learnings, Refs, Deps)")
    print("  - File paths use relative format (e.g., 'src/...')")

if __name__ == "__main__":
    main()
