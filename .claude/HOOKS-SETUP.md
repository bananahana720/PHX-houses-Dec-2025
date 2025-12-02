# Claude Code Hooks Configuration

**Status**: ✓ Configured for WSL environment
**Last Updated**: 2025-11-15
**Configuration Files**: `.claude/settings.json`, `.claude/settings.local.json`

## Overview

Your Claude Code hooks are now properly configured with WSL-compatible paths and comprehensive safety features based on [Claude Code Hooks Reference](https://code.claude.com/docs/en/hooks.md).

## Active Hooks

### PreToolUse Hooks (Before Tool Execution)

#### 1. Bash Safety Hook
- **File**: `bash_hook.py`
- **Matcher**: `Bash`
- **Purpose**: Unified safety checks for all bash commands
- **Blocks**:
  - `rm` commands (enforces TRASH directory pattern)
  - Dangerous `git add` patterns (`-A`, `--all`, `.`, `*`)
  - Unsafe `git checkout` operations
  - `grep` usage (enforces ripgrep/rg)
  - Access to sensitive files (`.env`, credentials)
- **Integrates**: 6 specialized safety checks

#### 2. File Size Conditional Hook
- **File**: `file_size_conditional_hook.py`
- **Matcher**: `Read`
- **Purpose**: Prevent context bloat from large files
- **Limits**:
  - Main agent: 500 lines max
  - Sub-agents: 10,000 lines max
- **Smart**: Accounts for offset/limit parameters

#### 3. Grep Enforcement Hook (settings.json only)
- **File**: `grep_block_hook.py`
- **Matcher**: `Grep`
- **Purpose**: Block deprecated grep, enforce ripgrep (rg)
- **Behavior**: Always suggests using Grep tool instead

#### 4. Pre-Task Subagent Tracking
- **File**: `pretask_subtask_flag.py`
- **Matcher**: `Task`
- **Purpose**: Create `.claude_in_subtask.flag` before subagent execution
- **Enables**: Different behavior for sub-agents (larger file limits)

### PostToolUse Hooks (After Tool Execution)

#### 5. Python Auto-Formatter
- **File**: `format_python_hook.py`
- **Matcher**: `Edit|Write`
- **Purpose**: Automatically format Python files with black/ruff
- **Runs**: After any Edit or Write operation
- **Timeout**: 30s (handles large files)

#### 6. Markdown Metadata Hook
- **File**: `markdown_info_hook.py`
- **Matcher**: `Edit|Write`
- **Purpose**: Add/update metadata in markdown files
- **Behavior**: Non-blocking, informational

#### 7. Post-Task Subagent Cleanup
- **File**: `posttask_subtask_flag.py`
- **Matcher**: `Task`
- **Purpose**: Remove `.claude_in_subtask.flag` after subagent completes
- **Ensures**: Clean state for next operation

### UserPromptSubmit Hooks (Before Processing User Input)

#### 8. Grep Reminder Hook
- **File**: `user_prompt_grep_reminder.py`
- **Purpose**: Remind about grep vs rg best practices
- **Behavior**: Context injection, non-blocking

### Stop/SubagentStop Hooks (LLM-Based Decisions)

#### 9. Stop Gate Hook
- **Type**: `prompt` (LLM-based)
- **Purpose**: Evaluate if main agent should stop
- **Checks**:
  - All tasks complete?
  - Errors need addressing?
  - Follow-up work needed?

#### 10. Subagent Stop Gate Hook
- **Type**: `prompt` (LLM-based)
- **Purpose**: Evaluate if subagent should stop
- **Checks**:
  - Task completed?
  - Errors occurred?
  - Additional context needed?

## Configuration Differences

### `.claude/settings.json` (Project-Level)

**Full hook suite** with additional safety checks:
- Grep enforcement hook (forces ripgrep usage)
- Complete PreToolUse protection
- All PostToolUse formatters
- LLM-based stop gates

**Use case**: Default development workflow with maximum safety

### `.claude/settings.local.json` (Local Override)

**Streamlined hooks** for faster iteration:
- Bash safety (core protection)
- Python formatter (code quality)
- Markdown metadata (documentation)
- Stop gates (intelligent completion)
- **Omits**: Grep enforcement, Read size limits, Task tracking

**Use case**: When you need faster responses or working with large files

## Safety Features

### Git Protection

**Blocked Operations**:
```bash
git add -A          # ✗ Too broad, suggests: git add -u
git add .           # ✗ Too broad, suggests specific files
git add *           # ✗ Too broad, suggests specific patterns
git checkout -f     # ✗ Loses changes, suggests: git stash
git checkout .      # ✗ Loses changes, suggests: git switch
```

**Git Commit Speed Bump**:
- First commit attempt shows reminder about user approval
- Second attempt proceeds (uses `.claude_git_commit_warning.flag`)
- Prevents accidental commits without review

### File Deletion Safety

**Instead of `rm`**:
```bash
# ✗ Blocked
rm unwanted.txt

# ✓ Suggested
mv unwanted.txt TRASH/
echo "unwanted.txt - moved to TRASH/ - reason here" >> TRASH-FILES.md
```

### Context Management

**File Size Limits**:
- **Main agent**: 500 lines (prevents context bloat)
- **Sub-agents**: 10,000 lines (more capacity for deep analysis)
- **Binary files**: Always allowed
- **Smart detection**: Respects offset/limit parameters

**Suggestions when blocked**:
- Use Task tool with sub-agents for large files
- Use Grep tool for specific content searches
- Consider external tools for very large files

## File Structure

```
.claude/
├── settings.json              # Project-level configuration (full safety)
├── settings.local.json        # Local overrides (streamlined)
├── HOOKS-SETUP.md            # This documentation
└── hooks/                     # Hook scripts directory
    ├── README.md             # Hook implementation guide
    ├── bash_hook.py          # Unified bash safety (combines 6 checks)
    ├── file_size_conditional_hook.py
    ├── grep_block_hook.py
    ├── pretask_subtask_flag.py
    ├── posttask_subtask_flag.py
    ├── format_python_hook.py
    ├── markdown_info_hook.py
    ├── user_prompt_grep_reminder.py
    ├── git_add_block_hook.py      # (imported by bash_hook.py)
    ├── git_checkout_safety_hook.py # (imported by bash_hook.py)
    ├── git_commit_block_hook.py    # (imported by bash_hook.py)
    ├── rm_block_hook.py            # (imported by bash_hook.py)
    ├── env_file_protection_hook.py # (imported by bash_hook.py)
    └── bash_grep_check.py          # (imported by bash_hook.py)
```

## Key Changes from Windows

### Path Format
- **Old (Windows)**: `python ".claude\\hooks\\bash_hook.py"`
- **New (WSL)**: `python .claude/hooks/bash_hook.py`

### Removed Flags
- **Old**: `"disableAllHooks": true` (disabled all hooks)
- **New**: Removed (hooks now active)

### Executable Permissions
- All `.py` and `.sh` files now have `+x` permission
- Required for WSL/Linux execution

## Verification

**Check hook registration**:
```bash
# In Claude Code, run:
/hooks
```

**Test a blocked command**:
```bash
# Should be blocked with helpful suggestion:
rm test.txt
git add -A
grep "pattern" file.txt
```

**Validate configuration**:
```bash
python -m json.tool .claude/settings.json
python -m json.tool .claude/settings.local.json
```

## Troubleshooting

### Hooks not triggering

1. Check file permissions:
   ```bash
   ls -la .claude/hooks/*.py .claude/hooks/*.sh
   ```
   Should show `-rwxr-xr-x` (executable)

2. Verify JSON syntax:
   ```bash
   python -m json.tool .claude/settings.json
   ```

3. Check hook registration in Claude Code:
   ```
   /hooks
   ```

### Operations blocked unexpectedly

- Review hook logic in `.claude/hooks/`
- Check if you're in sub-agent (different limits apply)
- Try using settings.local.json for less restrictive workflow

### Performance issues

- Hooks run synchronously before operations
- Current timeouts:
  - Bash: 10s
  - Read: 5s
  - Task: 2s
  - Format: 30s (for large Python files)
  - Stop gates: 30s

## Best Practices

1. **Use TRASH/ pattern**: Never `rm`, always move to TRASH/
2. **Specific git add**: Use `git add -u` or list specific files
3. **Prefer ripgrep**: Use Grep tool (rg) over bash grep
4. **Context awareness**: Let file size hook guide you to sub-agents
5. **Commit discipline**: Review staged changes before committing

## References

- **Claude Code Hooks Reference**: https://code.claude.com/docs/en/hooks.md
- **Hook Scripts Documentation**: `.claude/hooks/README.md`
- **Project Setup**: `.claude/CLAUDE.md`

## Migration Notes

**From Windows to WSL**:
- ✓ Paths updated to Unix format (forward slashes)
- ✓ `disableAllHooks` flag removed
- ✓ Hook scripts made executable
- ✓ JSON syntax validated
- ✓ All 18 hook scripts preserved and functional
- ✓ Python-based hooks are platform-independent

**No changes needed** for hook script logic - Python scripts work identically on Windows and WSL.
