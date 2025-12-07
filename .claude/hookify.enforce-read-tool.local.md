---
name: enforce-read-tool
enabled: true
event: bash
pattern: \b(cat|head|tail)\s+[^|>]+\.(json|yaml|yml|py|md|txt|csv|toml)
action: block
---

## 🛑 Use Read Tool Instead of Bash cat/head/tail

**MANDATORY per CLAUDE.md:30-36 (Tool Usage)**

### ❌ Blocked Command
```bash
cat file.json      # BLOCKED
head -n 50 file.py # BLOCKED
tail -f log.txt    # BLOCKED
```

### ✅ Correct Approach
Use the **Read tool** instead:
```
Read tool: file_path="path/to/file.json"
Read tool: file_path="path/to/file.py", limit=50
```

### Why This Is Enforced
1. **Permissions**: Read tool handles access properly
2. **Error handling**: Better error messages
3. **Context**: File contents available in conversation
4. **Line numbers**: Read tool shows line numbers for references

### Exception
Piping to other commands IS allowed:
```bash
cat file.json | jq '.field'  # OK - processing pipeline
```
