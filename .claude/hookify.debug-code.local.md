---
name: block-debug-code
enabled: true
event: file
pattern: console\.log\(|(?<![a-zA-Z])print\(|debugger\b|logger\.debug\(|breakpoint\(\)|pdb\.set_trace\(|import\s+pdb|from\s+pdb\s+import
action: block
---

**Debug Code Detected - Operation Blocked**

You attempted to add debug code to the codebase. This is blocked per user preference.

**Detected patterns:**
- `console.log` - JavaScript/TypeScript console logging
- `print` statements - Python print calls (not methods like blueprint)
- `debugger` - JavaScript debugger breakpoints
- `logger.debug` - Debug-level logging calls
- `breakpoint` - Python 3.7+ built-in debugger
- `pdb.set_trace` - Python debugger breakpoints
- `import pdb` / `from pdb import` - Debugger imports

**Why this is blocked:**
- Debug code should not ship to production
- Console output can expose sensitive data
- Debug statements impact runtime performance
- Clean code should not contain debugging artifacts

**What to do instead:**
- Use proper logging with appropriate levels (info, warn, error)
- Use test assertions rather than debug prints
- Use a debugger with breakpoints during development
- Remove all debug code before committing

If you need this debug code temporarily, disable the rule by editing `.claude/hookify.debug-code.local.md` and setting `enabled: false`.
