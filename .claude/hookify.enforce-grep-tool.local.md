---
name: enforce-grep-tool
enabled: true
event: bash
pattern: \b(grep|rg)\s+(-[a-zA-Z]+\s+)*['"](.*?)['"]\s+
action: block
---

## 🛑 Use Grep Tool Instead of Bash grep/rg

**MANDATORY per CLAUDE.md:30-36 (Tool Usage)**

### ❌ Blocked Command
```bash
grep "pattern" file.py     # BLOCKED
rg "search" src/           # BLOCKED
grep -r "TODO" .           # BLOCKED
```

### ✅ Correct Approach
Use the **Grep tool** instead:
```
Grep tool: pattern="pattern", path="src/", output_mode="content"
```

### Why This Is Enforced
1. **Optimized**: Grep tool is built on ripgrep
2. **Structured output**: Results formatted for context
3. **File type filtering**: Use `type` parameter
4. **Context lines**: Use `-A`, `-B`, `-C` parameters

### Grep Tool Parameters
```yaml
pattern: "your regex"
path: "directory/to/search"
output_mode: "content" | "files_with_matches" | "count"
type: "py" | "js" | "md" | etc.
```
