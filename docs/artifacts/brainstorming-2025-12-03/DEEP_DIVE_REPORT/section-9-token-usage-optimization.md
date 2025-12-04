# SECTION 9: TOKEN USAGE OPTIMIZATION

### Current Pattern Efficiency

**Per-Agent Token Cost:**

```
Session Start:
  Root CLAUDE.md          ~800 tokens (loaded once/session)
  .claude/CLAUDE.md       ~700 tokens (loaded once/session)

Per Agent Spawn:
  AGENT_BRIEFING.md       ~900 tokens (mandatory)
  Agent file (.md)        ~1200 tokens (mandatory)
  2-3 skills             ~1500-2500 tokens (on-demand)
  ─────────────────────────────────
  TOTAL                  ~4300-5600 tokens per agent

Optimizations Already Applied:
✓ Shallow root docs (no detail duplication)
✓ Skill files (2-3KB each) vs full library loading
✓ Knowledge graphs as indexes (sparse pointers, not full content)
✓ WRONG/CORRECT patterns (concrete examples > explanations)
✓ Lists + tables (scannable) > prose (readable but dense)
```

### Recommendations for Further Optimization

1. **Implement skill summaries** (100-200 tokens per skill)
   - Short summary: purpose, allowed-tools, key function
   - Full skill loaded only on explicit Skill invocation

2. **Use frontier model for heavy lifting**
   - Root/briefing files: Haiku 4.5 (current, appropriate)
   - Image assessment: Sonnet 4.5 (current, appropriate)
   - Complex orchestration: Sonnet 4.5 when needed

3. **Cache enrichment_data.json results**
   - Properties are read-heavy, write-infrequent
   - Agent caches last 10 property lookups
   - Invalidates on write

---
