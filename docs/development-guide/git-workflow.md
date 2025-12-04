# Git Workflow

### Commit Guidelines

1. **Never bypass pre-commit hooks**
   ```bash
   # NEVER do this
   git commit --no-verify  # PROHIBITED
   git commit -n           # PROHIBITED
   ```

2. **Commit message format**
   ```
   type: brief description

   Longer explanation if needed.

   🤖 Generated with [Claude Code](https://claude.com/claude-code)

   Co-Authored-By: Claude <noreply@anthropic.com>
   ```

   Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

3. **Pre-commit hook failures**
   - Read error messages carefully
   - Fix all reported issues
   - Stage fixes: `git add <files>`
   - Commit again (hooks run automatically)

### Branching Strategy

```bash
# Create feature branch
git checkout -b feature/add-noise-scorer

# Make changes, commit
git add src/ tests/
git commit -m "feat: add noise level scorer"

# Push to remote
git push origin feature/add-noise-scorer

# Create pull request (if applicable)
```

---
