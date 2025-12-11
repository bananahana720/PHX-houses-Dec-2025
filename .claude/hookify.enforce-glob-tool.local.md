---
name: enforce-glob-tool
enabled: false
# DISABLED: Duplicates bash_hook.py which already blocks find
event: bash
pattern: \b(find|ls)\s+.*\*.*\.(py|md|json|yaml|yml|ts|js)
action: block
---

## 🛑 Use Glob Tool Instead of Bash find/ls

**MANDATORY per CLAUDE.md:30-36 (Tool Usage)**

### ❌ Blocked Command
```bash
find . -name "*.py"           # BLOCKED
ls src/**/*.json              # BLOCKED
find -type f -name "*.md"     # BLOCKED
```

### ✅ Correct Approach
Use the **Glob tool** instead:
```
Glob tool: pattern="**/*.py", path="src/"
Glob tool: pattern="src/**/*.json"
```

### Why This Is Enforced
1. **Fast**: Optimized file pattern matching
2. **Cross-platform**: Works on Windows/Mac/Linux
3. **Sorted**: Results sorted by modification time
4. **Consistent**: Same behavior across environments

### Glob Patterns
```yaml
"**/*.py"           # All Python files recursively
"src/**/*.test.ts"  # Test files in src
"*.json"            # JSON files in current dir
"docs/**/*.md"      # Markdown in docs
```
